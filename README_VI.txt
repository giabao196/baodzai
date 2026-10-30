LINK4M LINK HELPER – HƯỚNG DẪN TRIỂN KHAI

LƯU Ý QUAN TRỌNG
- Đây là công cụ theo dõi chuyển hướng HTTP thông thường, không phải bản sao VNBP.
- Không giải CAPTCHA, không vượt trang quảng cáo/nhiệm vụ, không đăng nhập thay người dùng và không vượt cơ chế chống bot.
- Link4M có thể chặn yêu cầu tự động; khi đó hãy mở link trên trang chính thức.
- GitHub Pages chỉ host giao diện tĩnh. Cần Cloudflare Worker làm đầu mối kiểm tra redirect.

A. Đưa giao diện lên GitHub Pages
1. Tạo repository GitHub mới, ví dụ link4m-link-helper.
2. Upload index.html, style.css, app.js.
3. Vào Settings > Pages.
4. Chọn Deploy from a branch, chọn nhánh main và thư mục /(root), rồi Save.

B. Triển khai worker.js
1. Đăng nhập Cloudflare, mở Workers & Pages.
2. Tạo Worker mới.
3. Dán toàn bộ nội dung worker.js vào editor và Deploy.
4. Sao chép URL Worker, dạng https://ten-worker.ten-tai-khoan.workers.dev

C. Nối website với Worker
1. Mở app.js trong GitHub.
2. Thay dòng:
   const WORKER_URL = "PASTE_YOUR_CLOUDFLARE_WORKER_URL_HERE";
   bằng URL Worker vừa tạo, giữ dấu ngoặc kép.
3. Commit thay đổi. Mở website GitHub Pages và thử một URL Link4M hợp lệ.

Nếu Link4M yêu cầu CAPTCHA, đăng nhập, hoàn thành nhiệm vụ hoặc chặn truy cập tự động, công cụ sẽ không thể bypass phần đó. Không nhập mật khẩu hay OTP vào website này.
