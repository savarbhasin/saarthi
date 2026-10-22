#!/usr/bin/env bash
set -euo pipefail

mkdir -p ~/files ~/notes ~/.browser-profile

# A virtual screen so the browser runs headed and can be watched over noVNC on :6080.
Xvfb :99 -screen 0 1280x800x24 -nolisten tcp &
sleep 1
fluxbox >/dev/null 2>&1 &
x11vnc -display :99 -forever -shared -nopw -quiet -rfbport 5900 >/dev/null 2>&1 &
websockify --web /usr/share/novnc 6080 localhost:5900 >/dev/null 2>&1 &

exec uvicorn agent_server.main:app --host 0.0.0.0 --port 8700
