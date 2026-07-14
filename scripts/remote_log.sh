#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# remote_log.sh — 查看远程训练日志
# ============================================================
# 用法:
#   bash scripts/remote_log.sh <server_name> [lines]
#   bash scripts/remote_log.sh server-4          # 最后 50 行
#   bash scripts/remote_log.sh server-4 100      # 最后 100 行
#   bash scripts/remote_log.sh server-4 0 -f     # tail -f 持续跟踪
# ============================================================

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
SERVERS_YAML="${ROOT_DIR}/SERVERS.yaml"

SERVER="${1:-}"
LINES="${2:-50}"

if [[ -z "${SERVER}" ]]; then
    echo "Usage: $0 <server_name> [lines] [tail_flags]"
    echo "Example: $0 server-4"
    echo "         $0 server-4 100"
    echo "         $0 server-4 0 -f   # follow mode"
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
REMOTE_CODE_ROOT=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "remote_code_root")

if [[ -z "${HOST}" ]]; then
    echo "Error: server '${SERVER}' not found in SERVERS.yaml"
    exit 1
fi

SSH_TARGET="${USER}@${HOST}"

LATEST_LOG=$(ssh "${SSH_TARGET}" "ls -t ${REMOTE_CODE_ROOT}/logs/train_*.log 2>/dev/null | head -1" || true)

if [[ -z "${LATEST_LOG}" ]]; then
    echo "No training logs found on ${SERVER} at ${REMOTE_CODE_ROOT}/logs/"
    exit 1
fi

echo "==== Log: ${LATEST_LOG} ===="
echo ""

if [[ "${3:-}" == "-f" ]]; then
    ssh "${SSH_TARGET}" "tail -f ${LATEST_LOG}"
else
    ssh "${SSH_TARGET}" "tail -${LINES} ${LATEST_LOG}"
fi
