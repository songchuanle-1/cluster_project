#!/usr/bin/env bash
# SSH 端口转发 — 把远程 8080 映射到本地 8080
# 用法: bash /home/songcl/3dres/project/scripts/port_forward.sh

HOST="${1:-192.168.1.175}"
USER="${2:-songcl}"

echo "Forwarding ${HOST}:8080 -> localhost:8080"
echo "Open http://localhost:8080 in browser"
echo "Press Ctrl+C to stop"

ssh -N -L 8080:localhost:8080 ${USER}@${HOST}
