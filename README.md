# CloudPhone V1

A small self-hosted Android cloud-phone prototype designed to be opened from Safari on iPad or Chrome on Android.

## What it does

- Web dashboard with Start / Stop / Restart
- Android emulator in Docker
- 4 GB RAM target
- Persistent Android data volume
- Browser control through the emulator's noVNC endpoint
- Mobile-friendly UI
- Optional APK upload endpoint
- Idle timeout hook (server-side placeholder)

## Important

GitHub hosts the source code; it does not provide the Android VM. The deployment host must be a Linux machine with hardware virtualization/KVM (`/dev/kvm`) and enough CPU/RAM.

The included Android image is intended as a starting point. Play Store availability depends on the selected emulator image/API configuration.

## Quick start

1. Install Docker + Docker Compose on a Linux KVM host.
2. Make sure `/dev/kvm` exists:
   `ls -l /dev/kvm`
3. Run:
   `docker compose up -d --build`
4. Open:
   `http://SERVER_IP/`

The first Android boot can take several minutes.

## Security

This V1 is deliberately simple. Do not expose it directly to the public Internet without HTTPS and authentication. The APK upload endpoint is also intentionally basic.

## GitHub

Push this folder to a GitHub repository, then deploy the same repository on your KVM host.
