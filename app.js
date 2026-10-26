document.addEventListener('DOMContentLoaded', () => {
    const btnConnect = document.getElementById('btn-connect');
    const vpsInput = document.getElementById('vps-url');
    const iframe = document.getElementById('remote-iframe');
    const placeholder = document.getElementById('placeholder');
    const statusIndicator = document.getElementById('connection-status');
    const btnPower = document.getElementById('btn-power');
    const btnRemote = document.getElementById('btn-remote');
    const btnFullscreen = document.getElementById('btn-fullscreen');

    // Kết nối đến VPS Stream
    btnConnect.addEventListener('click', () => {
        const url = vpsInput.value.trim();
        if (!url) {
            alert('Vui lòng nhập URL VPS (ví dụ: http://103.x.x.x:8000 hoặc http://103.x.x.x:6080)');
            return;
        }

        placeholder.style.display = 'none';
        iframe.style.display = 'block';
        iframe.src = url;

        statusIndicator.classList.remove('offline');
        statusIndicator.classList.add('online');
        statusIndicator.textContent = 'Đã kết nối';
    });

    // Nút Bật / Tắt máy
    btnPower.addEventListener('click', () => {
        if (iframe.style.display === 'block') {
            iframe.style.display = 'none';
            iframe.src = '';
            placeholder.style.display = 'block';
            statusIndicator.classList.remove('online');
            statusIndicator.classList.add('offline');
            statusIndicator.textContent = 'Ngoại tuyến';
            btnPower.innerHTML = '<i class="fa-solid fa-play"></i> Bật máy';
            btnPower.className = 'btn btn-success';
        } else {
            btnConnect.click();
            btnPower.innerHTML = '<i class="fa-solid fa-power-off"></i> Tắt máy';
            btnPower.className = 'btn btn-dark';
        }
    });

    // Nút Mở Remote tab mới
    btnRemote.addEventListener('click', () => {
        const url = vpsInput.value.trim();
        if (url) {
            window.open(url, '_blank');
        } else {
            alert('Vui lòng nhập địa chỉ VPS trước khi mở Remote!');
        }
    });

    // Fullscreen
    btnFullscreen.addEventListener('click', () => {
        const phoneFrame = document.querySelector('.phone-frame');
        if (!document.fullscreenElement) {
            phoneFrame.requestFullscreen().catch(err => {
                alert(`Không thể mở toàn màn hình: ${err.message}`);
            });
        } else {
            document.exitFullscreen();
        }
    });
});
