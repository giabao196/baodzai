// Set this to your deployed Cloudflare Worker URL after deployment.
const WORKER_URL = "PASTE_YOUR_CLOUDFLARE_WORKER_URL_HERE";
const input = document.getElementById("link");
const go = document.getElementById("go");
const statusEl = document.getElementById("status");
const result = document.getElementById("result");
const finalBox = document.getElementById("final");
const openLink = document.getElementById("open");

function validLink(raw) {
  let u;
  try { u = new URL(raw); } catch { return false; }
  return u.protocol === "https:" && ["link4m.net","www.link4m.net","link4m.com","www.link4m.com","link4m.org","www.link4m.org"].includes(u.hostname);
}
go.addEventListener("click", async () => {
  const raw = input.value.trim();
  result.hidden = true;
  if (!validLink(raw)) {
    statusEl.textContent = "Link không hợp lệ. Hãy nhập URL HTTPS thuộc link4m.net, link4m.com hoặc link4m.org.";
    return;
  }
  if (WORKER_URL.startsWith("PASTE_")) {
    statusEl.textContent = "Bạn cần triển khai worker.js trên Cloudflare Workers rồi dán URL Worker vào biến WORKER_URL trong app.js.";
    return;
  }
  go.disabled = true;
  statusEl.textContent = "Đang kiểm tra chuyển hướng HTTP…";
  try {
    const response = await fetch(WORKER_URL, {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({url: raw})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Máy chủ không xử lý được liên kết.");
    finalBox.value = data.finalUrl;
    openLink.href = data.finalUrl;
    result.hidden = false;
    statusEl.textContent = data.finalUrl === raw
      ? "Không phát hiện chuyển hướng HTTP. Link có thể cần thao tác trên trang chính thức."
      : "Đã tìm thấy đích chuyển hướng HTTP.";
  } catch (e) {
    statusEl.textContent = "Không thể kiểm tra tự động: " + e.message + " Hãy mở link trên trang Link4M để tiếp tục nếu có CAPTCHA hoặc yêu cầu thao tác.";
  } finally { go.disabled = false; }
});
document.getElementById("copy").addEventListener("click", async () => {
  try { await navigator.clipboard.writeText(finalBox.value); statusEl.textContent = "Đã sao chép link."; }
  catch { finalBox.select(); document.execCommand("copy"); statusEl.textContent = "Đã sao chép link."; }
});