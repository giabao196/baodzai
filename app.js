const t=document.getElementById('toast');function msg(x){t.textContent=x;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2400)}
document.getElementById('menu').onclick=()=>document.querySelector('aside').style.display=document.querySelector('aside').style.display==='none'?'block':'none';
document.getElementById('trial').onclick=()=>msg('Free Trial 2 giờ — cần backend cloud để chạy Android thật.');
document.getElementById('start').onclick=()=>msg('Đã gửi lệnh bật máy (bản giao diện).');
document.getElementById('create').onclick=()=>msg('Tạo thiết bị sẽ hoạt động sau khi nối API cloud.');
document.getElementById('remote').onclick=()=>document.getElementById('remoteBox').style.display='block';
document.getElementById('close').onclick=()=>document.getElementById('remoteBox').style.display='none';