const express = require("express");
const cors = require("cors");
const dns = require("node:dns/promises");
const ipaddr = require("ipaddr.js");

const app = express();
app.disable("x-powered-by");
app.use(express.json({ limit: "8kb" }));

const allowedOrigin = process.env.FRONTEND_ORIGIN;
app.use(cors({
  origin(origin, cb) {
    if (!origin || !allowedOrigin || origin === allowedOrigin) return cb(null, true);
    return cb(new Error("Origin not allowed"));
  },
  methods: ["GET", "POST"],
  allowedHeaders: ["Content-Type"]
}));

const requests = new Map();
app.use("/api", (req, res, next) => {
  const key = req.ip || "unknown", now = Date.now();
  let item = requests.get(key) || { start: now, count: 0 };
  if (now - item.start > 60000) item = { start: now, count: 0 };
  item.count++; requests.set(key, item);
  if (item.count > 30) return res.status(429).json({ error: "Quá nhiều yêu cầu. Hãy thử lại sau một phút." });
  next();
});

function publicIP(address) {
  try {
    let ip = ipaddr.parse(address);
    if (ip.kind() === "ipv6" && ip.isIPv4MappedAddress()) ip = ip.toIPv4Address();
    return ip.range() === "unicast";
  } catch { return false; }
}
async function validateUrl(value) {
  let u;
  try { u = new URL(value); } catch { throw new Error("Link không hợp lệ."); }
  if (!["http:", "https:"].includes(u.protocol)) throw new Error("Chỉ hỗ trợ link HTTP/HTTPS.");
  if (u.username || u.password) throw new Error("Không hỗ trợ URL có thông tin đăng nhập.");
  const host = u.hostname.replace(/^\[|\]$/g, "").toLowerCase();
  if (host === "localhost" || host.endsWith(".localhost") || host.endsWith(".local")) throw new Error("Không cho phép địa chỉ nội bộ.");
  let records;
  try { records = await dns.lookup(host, { all: true, verbatim: true }); }
  catch { throw new Error("Không phân giải được tên miền.");
  }
  if (!records.length || records.some(r => !publicIP(r.address))) throw new Error("Địa chỉ không công khai hoặc không được phép.");
  return u;
}

app.get("/", (_req,res) => res.json({ name: "LinkFlow", status: "ok" }));
app.get("/health", (_req,res) => res.json({ ok: true }));

app.post("/api/resolve", async (req,res) => {
  const raw = typeof req.body?.url === "string" ? req.body.url.trim() : "";
  if (!raw || raw.length > 2048) return res.status(400).json({ error: "Nhập một URL hợp lệ (tối đa 2048 ký tự)." });
  try {
    let current = raw;
    const chain = [];
    for (let hop = 0; hop <= 8; hop++) {
      const u = await validateUrl(current);
      if (chain.includes(u.href)) return res.status(422).json({ error: "Phát hiện vòng lặp chuyển hướng.", chain });
      chain.push(u.href);

      let response, methodUsed = "HEAD";
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 8000);
      try {
        response = await fetch(u, { method: "HEAD", redirect: "manual", signal: controller.signal,
          headers: { "user-agent": "LinkFlow-Redirect-Checker/1.0", "accept": "*/*" } });
        if (![301,302,303,307,308].includes(response.status) || !response.headers.get("location")) {
          // Retry GET only if HEAD appears unsupported. Stream is cancelled immediately.
          if ([400,403,405,501].includes(response.status)) {
            try {
              await response.body?.cancel();
              response = await fetch(u, { method: "GET", redirect: "manual", signal: controller.signal,
                headers: { "user-agent": "LinkFlow-Redirect-Checker/1.0", "accept": "text/html,*/*" } });
              methodUsed = "GET";
            } catch { /* retain the HEAD result below */ }
          }
        }
      } catch {
        return res.status(502).json({ error: "Không thể truy cập link. Website có thể chặn yêu cầu tự động hoặc đang không phản hồi.", chain });
      } finally { clearTimeout(timer); }

      const location = response.headers.get("location");
      if ([301,302,303,307,308].includes(response.status) && location) {
        if (hop === 8) return res.status(422).json({ error: "Link chuyển hướng quá nhiều bước.", chain });
        current = new URL(location, u).href;
        continue;
      }
      return res.json({
        ok: true, originalUrl: raw, finalUrl: u.href, status: response.status,
        hops: chain.length - 1, chain, method: methodUsed,
        note: "Chỉ kiểm tra redirect HTTP công khai. Nếu trang cần Get Code, đăng nhập, CAPTCHA hoặc nhiệm vụ, API không tự vượt bước đó."
      });
    }
  } catch (e) { return res.status(400).json({ error: e.message || "Không thể kiểm tra link." }); }
});

const port = Number(process.env.PORT || 10000);
app.listen(port, "0.0.0.0", () => console.log(`LinkFlow listening on ${port}`));
