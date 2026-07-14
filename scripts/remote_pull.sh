#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# remote_pull.sh — 从远程服务器拉回 Checkpoints
# ============================================================
# 用法:
#   bash scripts/remote_pull.sh <server_name> [remote_checkpoint_dir]
#   bash scripts/remote_pull.sh server-4
#   bash scripts/remote_pull.sh server-4 /data/songcl/Cluster_project/Cluster_checkpoints
# ============================================================

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
SERVERS_YAML="${ROOT_DIR}/SERVERS.yaml"

SERVER="${1:-}"

if [[ -z "${SERVER}" ]]; then
    echo "Usage: $0 <server_name> [remote_checkpoint_dir]"
    echo "Example: $0 server-4"
    echo "         $0 server-4 /data/songcl/Cluster_project/Cluster_checkpoints"
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

# Allow overriding remote dir
REMOTE_DIR="${2:-${REMOTE_WORK_DIR}}"
LOCAL_DIR="${ROOT_DIR}/Checkpoints/$(echo ${SERVER} | tr '-' '_')"

if [[ -z "${HOST}" ]]; then
    echo "Error: server '${SERVER}' not found in SERVERS.yaml"
    exit 1
fi

SSH_TARGET="${USER}@${HOST}"

echo "==== Pulling checkpoints from ${SERVER} ===="
echo "Remote: ${SSH_TARGET}:${REMOTE_DIR}"
echo "Local:  ${LOCAL_DIR}"
echo ""

# Check remote dir exists
if ! ssh "${SSH_TARGET}" "test -d ${REMOTE_DIR}" 2>/dev/null; then
    echo "Error: Remote directory ${REMOTE_DIR} does not exist on ${SERVER}"
    exit 1
fi

# Show what's available
echo "Available checkpoints on remote:"
ssh "${SSH_TARGET}" "ls -lt ${REMOTE_DIR}/ 2>/dev/null | head -10" || true
echo ""

# rsync
mkdir -p "${LOCAL_DIR}"
rsync -avz --progress "${SSH_TARGET}:${REMOTE_DIR}/" "${LOCAL_DIR}/"

echo ""
echo "==== Pull complete: ${LOCAL_DIR} ===="
ls -lt "${LOCAL_DIR}/" | head -10
