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

# ----- 用 git archive + tar 只传输 model 目录 -----
echo "[1/3] Packaging framework/model/ ..."
cd "${ROOT_DIR}"
git add framework/model/ 2>/dev/null || true
# 只提交 model 改动（如果有的话）
if git status --porcelain framework/model/ 2>/dev/null | grep -q '.'; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    git add framework/model/
    git commit -m "Auto-commit model changes [${TIMESTAMP}]" || true
fi

# 打包最新 commit 中的 framework/model
git archive --format=tar --prefix=framework/model/ HEAD:framework/model . | gzip > /tmp/cluster_model_sync.tar.gz

echo "[2/3] Uploading to ${SERVER}..."
scp /tmp/cluster_model_sync.tar.gz "${SSH_TARGET}:/tmp/cluster_model_sync.tar.gz"

echo "[3/3] Extracting on remote..."
ssh "${SSH_TARGET}" "
    cd ${REMOTE_CODE_ROOT}
    # 删除旧的 model 代码
    rm -rf framework/model
    # 解压新的
    tar xzf /tmp/cluster_model_sync.tar.gz
    rm /tmp/cluster_model_sync.tar.gz
    # 显示更新了哪些文件
    echo 'Updated files:'
    find framework/model -name '*.py' -newer framework/__init__.py 2>/dev/null | head -10 || find framework/model -name '*.py' | head -10
    echo 'Sync complete.'
"

rm /tmp/cluster_model_sync.tar.gz
echo "==== Model sync complete: framework/model/ -> ${SERVER}:${REMOTE_CODE_ROOT}/framework/model/ ===="
