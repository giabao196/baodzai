// Cloudflare Worker: follows ordinary HTTP redirects only.
// It does NOT solve CAPTCHAs, ad gates, tasks, logins, or anti-bot challenges.
const allowedHosts = new Set([
  "link4m.net", "www.link4m.net", "link4m.com", "www.link4m.com",
  "link4m.org", "www.link4m.org"
]);
const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type"
};
export default {
  async fetch(request) {
    if (request.method === "OPTIONS") return new Response(null, {headers:cors});
    if (request.method !== "POST") return json({error:"Method not allowed"},405);
    try {
      const body = await request.json();
      const u = new URL(body.url);
      if (u.protocol !== "https:" || !allowedHosts.has(u.hostname))
        return json({error:"Chỉ chấp nhận URL HTTPS thuộc miền Link4M."},400);
      const response = await fetch(u.toString(), {
        method:"GET", redirect:"follow",
        headers:{"User-Agent":"Mozilla/5.0 (compatible; LinkHelper/1.0)"}
      });
      const finalUrl = response.url || u.toString();
      return json({finalUrl, status:response.status},200);
    } catch (e) {
      return json({error:"Không theo dõi được chuyển hướng: " + String(e.message || e)},502);
    }
  }
};
function json(data,status) {
  return new Response(JSON.stringify(data), {
    status, headers:{...cors,"Content-Type":"application/json; charset=utf-8"}
  });
}