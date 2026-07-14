#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# remote_kill.sh — 终止远程训练
# ============================================================
# 用法:
#   bash scripts/remote_kill.sh <server_name>
#   bash scripts/remote_kill.sh server-4
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

echo "==== Terminating training on ${SERVER} (${SSH_TARGET}) ===="

# Kill by PID files first (more precise)
ssh "${SSH_TARGET}" "
    KILLED=0
    if ls ${REMOTE_CODE_ROOT}/logs/.pid_* 2>/dev/null | head -1; then
        for pf in ${REMOTE_CODE_ROOT}/logs/.pid_*; do
            pid=\$(cat \"\$pf\" 2>/dev/null || true)
            if [[ -n \"\${pid}\" ]]; then
                if kill -0 \$pid 2>/dev/null; then
                    echo \"Killing PID \$pid...\"
                    kill -TERM \$pid 2>/dev/null || true
                    sleep 2
                    if kill -0 \$pid 2>/dev/null; then
                        echo \"Force killing PID \$pid...\"
                        kill -9 \$pid 2>/dev/null || true
                    fi
                    KILLED=1
                else
                    echo \"PID \$pid already dead.\"
                fi
            fi
            rm -f \"\$pf\"
        done
    fi

    # Fallback: kill any remaining train/test python processes
    PIDS=\$(ps aux | grep -E 'python.*tools/(train|test)' | grep -v grep | awk '{print \$2}')
    if [[ -n \"\${PIDS}\" ]]; then
        echo \"Found remaining training processes: \${PIDS}\"
        for pid in \${PIDS}; do
            echo \"Killing PID \$pid...\"
            kill -TERM \$pid 2>/dev/null || true
        done
        sleep 2
        PIDS=\$(ps aux | grep -E 'python.*tools/(train|test)' | grep -v grep | awk '{print \$2}')
        if [[ -n \"\${PIDS}\" ]]; then
            for pid in \${PIDS}; do
                kill -9 \$pid 2>/dev/null || true
            done
        fi
        KILLED=1
    fi

    if [[ \$KILLED -eq 0 ]]; then
        echo 'No training processes found to kill.'
    else
        echo 'Done.'
    fi
"

echo "==== Kill complete ===="
