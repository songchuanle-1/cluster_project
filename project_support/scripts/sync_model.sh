#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# sync_model.sh — 同步 framework/model/ + configs/ 到远程服务器
# ============================================================
# 用法:
#   bash scripts/sync_model.sh <server_name>
#   bash scripts/sync_model.sh server-2
#
# 适用于: 只改了模型代码和/或 YAML 配置，不需要全量 git push
# 比 sync.sh 快很多，使用 rsync 增量传输
# ============================================================

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(dirname "${SCRIPT_DIR}")/Cluster}"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
SERVERS_YAML="$(dirname "${PROJECT_DIR}")/SERVERS.yaml"

SERVER="${1:-}"

if [[ -z "${SERVER}" ]]; then
    echo "Usage: $0 <server_name>"
    echo "Example: $0 server-2"
    exit 1
fi

get_yaml_value() {
    local file="$1" section="$2" key="$3"
    file=$(cygpath -m "$file" 2>/dev/null || echo "$file")
    python -c "
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

echo "==== Syncing model + configs to ${SERVER} (${SSH_TARGET}) ===="

# ----- 确保本地有提交 -----
cd "${PROJECT_DIR}"
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "Error: not a git repository."
    exit 1
fi

# ----- 用 rsync 传输 model + configs -----
echo "[1/3] Syncing framework/model/ ..."
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
echo "[2/3] Syncing configs/ ..."
rsync -avz \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    configs/ \
    "${SSH_TARGET}:${REMOTE_CODE_ROOT}/configs/"

echo ""
echo "[3/3] Applying path mappings on remote..."
# 根据 SERVERS.yaml 做路径替换
LOCAL_DATA_ROOT=$(get_yaml_value "${SERVERS_YAML}" "local" "data_root")
LOCAL_WORK_DIR=$(get_yaml_value "${SERVERS_YAML}" "local" "work_dir")
REMOTE_DATA_ROOT=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "data_root")
REMOTE_WORK_DIR=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "work_dir")

ssh "${SSH_TARGET}" "
    cd ${REMOTE_CODE_ROOT}
    if [[ '${REMOTE_DATA_ROOT}' != '${LOCAL_DATA_ROOT}' ]]; then
        echo \"data_root: ${LOCAL_DATA_ROOT%/} -> ${REMOTE_DATA_ROOT%/}\"
        grep -rl '${LOCAL_DATA_ROOT%/}' configs/ 2>/dev/null | while read f; do
            sed -i \"s|${LOCAL_DATA_ROOT%/}|${REMOTE_DATA_ROOT%/}|g; s|${LOCAL_DATA_ROOT}|${REMOTE_DATA_ROOT%/}|g\" \"\$f\"
        done
        # pretrain
        sed -i \"s|${LOCAL_DATA_ROOT%/}/sp_unet_backbone.pth|${REMOTE_DATA_ROOT%/}/sp_unet_backbone.pth|g\" configs/*.yaml 2>/dev/null || true
    fi
    if [[ '${REMOTE_WORK_DIR}' != '${LOCAL_WORK_DIR}' ]]; then
        echo \"work_dir: ${LOCAL_WORK_DIR} -> ${REMOTE_WORK_DIR}\"
        grep -rl '${LOCAL_WORK_DIR}' configs/ 2>/dev/null | while read f; do
            sed -i \"s|${LOCAL_WORK_DIR}|${REMOTE_WORK_DIR}|g\" \"\$f\"
        done
    fi
    echo 'Done.'
"

echo ""
echo "==== Sync complete: model + configs -> ${SERVER}:${REMOTE_CODE_ROOT}/ ===="
