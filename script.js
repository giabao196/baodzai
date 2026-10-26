const $ = (id) => document.getElementById(id);
const input = $("url"), button = $("run"), statusBox = $("status");
function normalizeUrl(value) {
  let u;
  try { u = new URL(value.trim()); }
  catch { throw new Error("Vui lòng nhập URL hợp lệ, ví dụ https://example.com"); }
  if (!["http:", "https:"].includes(u.protocol)) throw new Error("Chỉ hỗ trợ URL http:// hoặc https://");
  return u.href;
}
button.addEventListener("click", async () => {
  $("result").classList.add("hidden"); statusBox.textContent = "";
  let url;
  try { url = normalizeUrl(input.value); } catch (e) { statusBox.textContent = e.message; return; }
  button.disabled = true; button.textContent = "Đang kiểm tra…";
  statusBox.textContent = "Đang thử đọc redirect công khai…";
  try {
    const response = await fetch(url, {method:"HEAD", mode:"cors", redirect:"follow", signal:AbortSignal.timeout(10000)});
    const finalUrl = response.url || url;
    showResult(finalUrl);
    statusBox.textContent = response.redirected ? "Đã phát hiện chuyển hướng mà trình duyệt cho phép đọc." : "Đã kết nối. Website có thể không công khai thông tin redirect.";
  } catch {
    showResult(url);
    statusBox.textContent = "Không đọc được redirect do CORS hoặc website chặn. URL hiển thị là link ban đầu, không phải kết quả bypass.";
  } finally { button.disabled = false; button.innerHTML = 'Kiểm tra link <b>→</b>'; }
});
function showResult(url) { $("dest").textContent = url; $("open").href = url; $("result").classList.remove("hidden"); }
$("copy").addEventListener("click", async () => {
  try { await navigator.clipboard.writeText($("dest").textContent); $("copy").textContent = "Đã sao chép ✓"; }
  catch { $("copy").textContent = "Không thể sao chép"; }
  setTimeout(() => $("copy").textContent = "Sao chép URL", 1800);
});
input.addEventListener("keydown", e => { if (e.key === "Enter") button.click(); });
