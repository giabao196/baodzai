import os
import subprocess
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(title="CloudPhone API")
ANDROID = os.getenv("ANDROID_CONTAINER", "cloudphone-android")
VNC = os.getenv("ANDROID_VNC_URL", "http://android:6080")
APK_DIR = Path("/data/apks")
APK_DIR.mkdir(parents=True, exist_ok=True)

def docker(*args):
    p = subprocess.run(["docker", *args], text=True, capture_output=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()

@app.get("/api/status")
def status():
    code, out, err = docker("inspect", "-f", "{{.State.Status}}", ANDROID)
    if code != 0:
        return JSONResponse({"status": "unknown", "error": err}, status_code=500)
    return {"status": out, "vnc_url": VNC}

@app.post("/api/start")
def start():
    code, out, err = docker("start", ANDROID)
    if code != 0 and "already started" not in err.lower():
        raise HTTPException(500, err)
    return {"ok": True, "status": "running"}

@app.post("/api/stop")
def stop():
    code, out, err = docker("stop", "-t", "10", ANDROID)
    if code != 0 and "is not running" not in err.lower():
        raise HTTPException(500, err)
    return {"ok": True, "status": "exited"}

@app.post("/api/restart")
def restart():
    code, out, err = docker("restart", "-t", "10", ANDROID)
    if code != 0:
        raise HTTPException(500, err)
    return {"ok": True, "status": "running"}

@app.post("/api/apk")
async def upload_apk(file: UploadFile = File(...)):
    name = Path(file.filename or "app.apk").name
    if not name.lower().endswith(".apk"):
        raise HTTPException(400, "Only .apk files are accepted")
    target = APK_DIR / name
    target.write_bytes(await file.read())
    return {"ok": True, "filename": name, "path": str(target)}

@app.get("/api/health")
def health():
    return {"ok": True}
