#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# sync.sh — 代码同步到远程服务器
# ============================================================
# 用法:
#   bash scripts/sync.sh <server_name>
#   bash scripts/sync.sh server-4
#
# 通过 git push 将代码推送到远程，远程 git checkout 更新工作区。
# ============================================================

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(dirname "${SCRIPT_DIR}")/Cluster}"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
SERVERS_YAML="$(dirname "${PROJECT_DIR}")/SERVERS.yaml"

SERVER="${1:-}"

if [[ -z "${SERVER}" ]]; then
    echo "Usage: $0 <server_name>"
    echo "Example: $0 server-4"
    exit 1
fi

# ----- 解析 SERVERS.yaml -----
get_yaml_value() {
    local file="$1" section="$2" key="$3"
    file=$(cygpath -m "$file" 2>/dev/null || echo "$file")
    python -c "
import yaml, io
with io.open('${file}', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)
servers = cfg.get('servers', {})
server = servers.get('${section}', {})
val = server.get('${key}', '')
if val is None: val = ''
print(val)
" 2>/dev/null
}

get_path_mapping() {
    local file="$1" mapping_key="$2" dir_key="$3"
    python -c "
import yaml
with open('${file}') as f:
    cfg = yaml.safe_load(f)
mappings = cfg.get('path_mappings', {})
m = mappings.get('${mapping_key}', {})
val = m.get('${dir_key}', '')
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

echo "==== Syncing code to ${SERVER} (${SSH_TARGET}) ===="

# ----- 确保本地有 commits -----
cd "${PROJECT_DIR}"
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "Error: not a git repository. Run 'git init && git add -A && git commit -m \"Initial commit\"' first."
    exit 1
fi

if [[ -z "$(git log --oneline 2>/dev/null | head -1)" ]]; then
    echo "No commits yet. Creating initial commit..."
    git add -A
    git commit -m "Initial commit"
fi

# ----- 远程仓库初始化 -----
echo "[1/4] Setting up remote git repo..."
ssh "${SSH_TARGET}" "
    mkdir -p ${REMOTE_CODE_ROOT}
    if [[ ! -d ${REMOTE_CODE_ROOT}/.git ]]; then
        cd ${REMOTE_CODE_ROOT}
        git init -q
        # Allow pushing to checked-out branch
        git config receive.denyCurrentBranch ignore
        echo 'Git repo initialized on remote.'
    else
        echo 'Git repo already exists on remote.'
    fi
"

# ----- 检查远程未提交修改 -----
echo "[2/4] Checking for uncommitted changes on remote..."
ssh "${SSH_TARGET}" "
    cd ${REMOTE_CODE_ROOT}
    # 守卫: 远端有训练进程在跑时, 跳过破坏性 clean (git clean -fd / checkout -- 会干扰
    # 运行中进程的文件句柄/路径 patch, 曾导致 D1-detail 中途断开). 仅用 stash 保存改动.
    RUNNING=\$(ps aux | grep -E 'python.*tools/(train|test)' | grep -v grep | wc -l)
    if [ \"\$RUNNING\" -gt 0 ]; then
        echo \"[guard] 远端有 \$RUNNING 个训练进程在跑, 跳过 git clean/checkout, 仅 stash 改动\"
        git stash -u 2>/dev/null || true
    else
        # Clean slate: force-discard local changes and clean up stale stashes
        git checkout -- . 2>/dev/null || true
        git clean -fd -e '*.so' -e 'build/' -e '*.egg-info' 2>/dev/null || true
        for i in 0 1 2 3 4 5 6 7 8 9; do git stash drop stash@{\$i} 2>/dev/null || true; done
        echo 'Working tree cleaned.'
    fi
"

# ----- 推送代码 -----
echo "[3/4] Pushing code to ${SERVER}..."
git push --force-with-lease "ssh://${SSH_TARGET}${REMOTE_CODE_ROOT}" HEAD:main 2>/dev/null || \
    git push "ssh://${SSH_TARGET}${REMOTE_CODE_ROOT}" HEAD:main

# ----- 远程更新工作区 -----
echo "[4/4] Updating working tree on remote..."
ssh "${SSH_TARGET}" "
    cd ${REMOTE_CODE_ROOT}
    git checkout main 2>/dev/null || git checkout -b main 2>/dev/null || true
    git reset --hard main 2>/dev/null || git reset --hard master 2>/dev/null || true
    echo 'Working tree updated.'
"

echo "==== Sync complete: ${PROJECT_DIR} -> ${SERVER}:${REMOTE_CODE_ROOT} ===="
