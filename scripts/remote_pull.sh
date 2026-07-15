#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# remote_pull.sh — 从远程服务器拉回训练产物
# ============================================================
# 用法:
#   bash scripts/remote_pull.sh <server_name>              # 仅拉取日志
#   bash scripts/remote_pull.sh <server_name> --logs-only  # 仅日志（默认）
#   bash scripts/remote_pull.sh <server_name> --full       # 日志 + checkpoints
#   bash scripts/remote_pull.sh <server_name> <remote_dir> # 指定远程目录
# ============================================================

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
SERVERS_YAML="${ROOT_DIR}/SERVERS.yaml"

SERVER="${1:-}"
MODE="${2:---logs-only}"

if [[ -z "${SERVER}" ]]; then
    echo "Usage: $0 <server_name> [--logs-only|--full] [remote_dir]"
    echo "  --logs-only  仅拉取日志文件 (默认, 很小)"
    echo "  --full       拉取日志 + checkpoint (.pth) 文件"
    echo ""
    echo "Example: $0 server-4"
    echo "         $0 server-4 --full"
    exit 1
fi

get_yaml_value() {
    local file="$1" section="$2" key="$3"
    python3 -c "
import yaml
with open('${file}') as f:
    cfg = yaml.safe_load(f)
servers = cfg.get('servers', {})
server = servers.get('${section}', {})
val = server.get('${key}', '')
if val is None: val = ''
print(val)
" 2>/dev/null
}

HOST=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "host")
USER=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "user")
REMOTE_WORK_DIR=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "work_dir")

# Parse mode: --logs-only or --full
RSYNC_EXCLUDE=""
if [[ "${MODE}" == "--full" ]]; then
    echo "Mode: full (logs + checkpoints)"
    REMOTE_DIR="${3:-${REMOTE_WORK_DIR}}"
else
    echo "Mode: logs only"
    RSYNC_EXCLUDE='--exclude=*.pth --exclude=events.out.*'
    REMOTE_DIR="${3:-${REMOTE_WORK_DIR}}"
fi

LOCAL_DIR="$(dirname "${ROOT_DIR}")/Checkpoints/$(echo ${SERVER} | tr '-' '_')"

if [[ -z "${HOST}" ]]; then
    echo "Error: server '${SERVER}' not found in SERVERS.yaml"
    exit 1
fi

SSH_TARGET="${USER}@${HOST}"

echo "==== Pulling from ${SERVER} ===="
echo "Remote: ${SSH_TARGET}:${REMOTE_DIR}"
echo "Local:  ${LOCAL_DIR}"
echo ""

# Check remote dir exists
if ! ssh "${SSH_TARGET}" "test -d ${REMOTE_DIR}" 2>/dev/null; then
    echo "Error: Remote directory ${REMOTE_DIR} does not exist"
    exit 1
fi

# Show what's available
echo "Available on remote:"
ssh "${SSH_TARGET}" "ls -lt ${REMOTE_DIR}/ 2>/dev/null | head -10" || true
echo ""

# rsync
mkdir -p "${LOCAL_DIR}"
rsync -avz --progress ${RSYNC_EXCLUDE} "${SSH_TARGET}:${REMOTE_DIR}/" "${LOCAL_DIR}/"

echo ""
echo "==== Pull complete: ${LOCAL_DIR} ===="
du -sh "${LOCAL_DIR}/"
ls -lt "${LOCAL_DIR}/" | head -10
echo ""
echo "Tip: use '--full' to also pull checkpoint .pth files"
