#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# sync_model.sh — 仅同步 framework/model/ 到远程服务器
# ============================================================
# 用法:
#   bash scripts/sync_model.sh <server_name>
#   bash scripts/sync_model.sh server-2
#
# 适用于: 环境/配置/脚本不变，只改了模型代码的情况
# 比 sync.sh 快很多，不需要 reset 全部文件
# ============================================================

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
SERVERS_YAML="${ROOT_DIR}/SERVERS.yaml"

SERVER="${1:-}"

if [[ -z "${SERVER}" ]]; then
    echo "Usage: $0 <server_name>"
    echo "Example: $0 server-2"
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

echo "==== Syncing framework/model/ to ${SERVER} (${SSH_TARGET}) ===="

# ----- 确保本地有提交 -----
cd "${ROOT_DIR}"
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "Error: not a git repository."
    exit 1
fi

# ----- 用 rsync 只传输 model 目录 -----
echo "[1/2] Syncing framework/model/ to ${SERVER} ..."

cd "${ROOT_DIR}"
rsync -avz --delete \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='build/' \
    --exclude='*.so' \
    --exclude='*.egg-info' \
    --exclude='.ninja_*' \
    framework/model/ \
    "${SSH_TARGET}:${REMOTE_CODE_ROOT}/framework/model/"

echo ""
echo "==== Model sync complete: framework/model/ -> ${SERVER}:${REMOTE_CODE_ROOT}/framework/model/ ===="
