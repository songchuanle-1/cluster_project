#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# remote_status.sh — 查看远程服务器状态
# ============================================================
# 用法:
#   bash scripts/remote_status.sh <server_name>
#   bash scripts/remote_status.sh server-4
# ============================================================

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
SERVERS_YAML="${ROOT_DIR}/SERVERS.yaml"

SERVER="${1:-}"

if [[ -z "${SERVER}" ]]; then
    echo "Usage: $0 <server_name>"
    echo "Example: $0 server-4"
    exit 1
fi

# ----- 解析 SERVERS.yaml -----
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
CONDA_ENV=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "conda_env")

if [[ -z "${HOST}" ]]; then
    echo "Error: server '${SERVER}' not found in SERVERS.yaml"
    exit 1
fi

SSH_TARGET="${USER}@${HOST}"

echo "============================================"
echo "Status Report: ${SERVER} (${SSH_TARGET})"
echo "Time: $(date)"
echo "============================================"

ssh "${SSH_TARGET}" "
    echo ''
    echo '===== GPU Status (nvidia-smi) ====='
    nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.free,memory.total --format=csv 2>/dev/null || echo 'nvidia-smi unavailable'

    echo ''
    echo '===== Training Processes ====='
    ps aux 2>/dev/null | grep -E 'python.*tools/(train|test)' | grep -v grep || echo 'No training processes found.'

    echo ''
    echo '===== PID Files ====='
    if ls ${REMOTE_CODE_ROOT}/logs/.pid_* 2>/dev/null | head -5; then
        for pf in ${REMOTE_CODE_ROOT}/logs/.pid_*; do
            pid=\$(cat \"\$pf\" 2>/dev/null || echo 'unknown')
            echo \"  \$pf -> PID=\$pid\"
            if kill -0 \$pid 2>/dev/null; then
                echo '    Status: RUNNING'
            else
                echo '    Status: DEAD'
            fi
        done
    else
        echo 'No PID files found.'
    fi

    echo ''
    echo '===== Latest Logs ====='
    if ls -t ${REMOTE_CODE_ROOT}/logs/train_*.log 2>/dev/null | head -1 | read latest_log; then
        echo \"Latest: \${latest_log}\"
        echo '--- Last 30 lines ---'
        tail -30 \"\${latest_log}\" 2>/dev/null || true
    else
        echo 'No training logs found.'
    fi

    echo ''
    echo '===== Disk Usage ====='
    df -h /data 2>/dev/null || df -h /home 2>/dev/null || df -h / 2>/dev/null
    echo ''
    echo '===== Recent Checkpoints ====='
    ls -lt ${REMOTE_CODE_ROOT}/work_dir/ 2>/dev/null | head -5 || echo 'No checkpoints found.'
"

echo ""
echo "============================================"
echo "Status check complete."
echo "============================================"
