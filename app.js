const $=id=>document.getElementById(id);
const userKey="cloud_android_demo_user";
const sessionKey="cloud_android_demo_session";

function show(which){
  $("registerBox").classList.toggle("hidden", which!=="register");
  $("loginBox").classList.toggle("hidden", which!=="login");
  $("authMsg").textContent=""; $("loginMsg").textContent="";
}
function dashboard(email){
  $("auth").classList.add("hidden");
  $("dashboard").classList.remove("hidden");
  $("userEmail").textContent=email;
}
function authScreen(){
  $("dashboard").classList.add("hidden");
  $("auth").classList.remove("hidden");
}
$("showLogin").onclick=()=>show("login");
$("showRegister").onclick=()=>show("register");

$("registerBtn").onclick=()=>{
  const email=$("email").value.trim().toLowerCase();
  const password=$("password").value;
  if(!email || !email.includes("@")) return $("authMsg").textContent="Email không hợp lệ.";
  if(password.length<6) return $("authMsg").textContent="Mật khẩu cần ít nhất 6 ký tự.";
  if(localStorage.getItem(userKey)) return $("authMsg").textContent="Email này đã đăng ký trên bản demo. Hãy đăng nhập.";
  // DEMO ONLY: localStorage is not secure authentication.
  localStorage.setItem(userKey, JSON.stringify({email,password}));
  $("authMsg").textContent="Đăng ký thành công trên bản demo. Bạn có thể đăng nhập.";
  $("loginEmail").value=email; show("login");
};

$("loginBtn").onclick=()=>{
  const email=$("loginEmail").value.trim().toLowerCase();
  const password=$("loginPassword").value;
  const u=JSON.parse(localStorage.getItem(userKey)||"null");
  if(!u || u.email!==email || u.password!==password) return $("loginMsg").textContent="Email hoặc mật khẩu không đúng.";
  localStorage.setItem(sessionKey,email); dashboard(email);
};
$("logoutBtn").onclick=()=>{localStorage.removeItem(sessionKey);authScreen();};

let running=false;
function renderVM(){
  $("status").className="status "+(running?"on":"off");
  $("status").textContent=running?"● Đang chạy":"● Chưa chạy";
  $("startBtn").disabled=running; $("stopBtn").disabled=!running; $("remoteBtn").disabled=!running;
}
$("startBtn").onclick=()=>{running=true;renderVM();$("vmMsg").textContent="Đã bật máy (demo). Chưa kết nối server Android thật.";};
$("stopBtn").onclick=()=>{running=false;renderVM();$("vmMsg").textContent="Đã tắt máy (demo).";};
$("remoteBtn").onclick=()=>{$("vmMsg").textContent="Bước tiếp theo sẽ gắn màn hình Android/remote vào nút này.";};

const session=localStorage.getItem(sessionKey);
if(session) dashboard(session); else {authScreen();show("register");}
renderVM();
