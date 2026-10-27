import os
import subprocess
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse


app = FastAPI(title="CloudPhone API")

ANDROID_CONTAINER = os.getenv(
    "ANDROID_CONTAINER",
    "cloudphone-android"
)

ANDROID_VNC_URL = os.getenv(
    "ANDROID_VNC_URL",
    "http://android:6080"
)

APK_DIR = Path("/data/apks")
APK_DIR.mkdir(parents=True, exist_ok=True)


def docker_command(*args):
    process = subprocess.run(
        ["docker", *args],
        text=True,
        capture_output=True
    )

    return (
        process.returncode,
        process.stdout.strip(),
        process.stderr.strip()
    )


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "cloudphone-api"
    }


@app.get("/api/status")
def status():
    code, output, error = docker_command(
        "inspect",
        "-f",
        "{{.State.Status}}",
        ANDROID_CONTAINER
    )

    if code != 0:
        return JSONResponse(
            {
                "status": "unknown",
                "error": error
            },
            status_code=500
        )

    return {
        "status": output,
        "vnc_url": ANDROID_VNC_URL
    }


@app.post("/api/start")
def start():
    code, output, error = docker_command(
        "start",
        ANDROID_CONTAINER
    )

    if code != 0 and "already started" not in error.lower():
        raise HTTPException(
            status_code=500,
            detail=error
        )

    return {
        "ok": True,
        "status": "running"
    }


@app.post("/api/stop")
def stop():
    code, output, error = docker_command(
        "stop",
        "-t",
        "10",
        ANDROID_CONTAINER
    )

    if code != 0 and "is not running" not in error.lower():
        raise HTTPException(
            status_code=500,
            detail=error
        )

    return {
        "ok": True,
        "status": "exited"
    }


@app.post("/api/restart")
def restart():
    code, output, error = docker_command(
        "restart",
        "-t",
        "10",
        ANDROID_CONTAINER
    )

    if code != 0:
        raise HTTPException(
            status_code=500,
            detail=error
        )

    return {
        "ok": True,
        "status": "running"
    }


@app.post("/api/apk")
async def upload_apk(file: UploadFile = File(...)):
    filename = Path(
        file.filename or "app.apk"
    ).name

    if not filename.lower().endswith(".apk"):
        raise HTTPException(
            status_code=400,
            detail="Only APK files are accepted"
        )

    target = APK_DIR / filename

    content = await file.read()
    target.write_bytes(content)

    return {
        "ok": True,
        "filename": filename
    }
