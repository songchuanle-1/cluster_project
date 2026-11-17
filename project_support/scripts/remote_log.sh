#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# remote_log.sh — 查看远程训练日志
# ============================================================
# 用法:
#   bash scripts/remote_log.sh <server>                  # 列出所有日志（多任务时）
#   bash scripts/remote_log.sh <server> --last           # 最新日志最后 50 行
#   bash scripts/remote_log.sh <server> <keyword>        # 匹配关键字的日志
#   bash scripts/remote_log.sh <server> <keyword> 100    # 指定行数
#   bash scripts/remote_log.sh <server> <keyword> 0 -f   # 实时跟踪
#
# 示例:
#   bash scripts/remote_log.sh server-4                   # 列出该服务器所有日志
#   bash scripts/remote_log.sh server-4 --last            # 最新的日志
#   bash scripts/remote_log.sh server-4 pointgate         # pointgate 任务的日志
#   bash scripts/remote_log.sh server-4 pointgate 100     # 最后 100 行
#   bash scripts/remote_log.sh server-4 pointgate 0 -f    # 实时跟踪
# ============================================================

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(dirname "${SCRIPT_DIR}")/Cluster}"
SERVERS_YAML="$(dirname "${PROJECT_DIR}")/SERVERS.yaml"

SERVER="${1:-}"

if [[ -z "${SERVER}" ]]; then
    echo "Usage: $0 <server> [keyword|--last] [lines] [-f]"
    echo ""
    echo "  <server>             服务器名"
    echo "  <keyword>            匹配日志文件名关键字（如 pointgate）"
    echo "  --last               直接看最新日志（单任务快捷方式）"
    echo "  [lines]              显示行数（默认 50）"
    echo "  -f                   实时跟踪模式"
    echo ""
    echo "Examples:"
    echo "  $0 server-4                    # 列出所有日志"
    echo "  $0 server-4 --last             # 最新日志"
    echo "  $0 server-4 pointgate          # 匹配 'pointgate' 的日志"
    echo "  $0 server-4 pointgate 100      # 最后 100 行"
    echo "  $0 server-4 pointgate 0 -f     # 实时跟踪"
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
LOG_DIR="${REMOTE_CODE_ROOT}/logs"

# Parse args
KEYWORD=""
LINES=50
FOLLOW=""

shift  # 消费 server 参数
while [[ $# -gt 0 ]]; do
    case "$1" in
        -f) FOLLOW="-f"; shift ;;
        --last) KEYWORD="__latest__"; shift ;;
        *)
            if [[ "$1" =~ ^[0-9]+$ ]]; then
                LINES="$1"
                shift
            else
                KEYWORD="$1"
                shift
            fi
            ;;
    esac
done

# List available logs
echo "==== Logs on ${SERVER} ===="
LOG_LIST=$(ssh "${SSH_TARGET}" "ls -lt ${LOG_DIR}/train_*.log 2>/dev/null" || true)

if [[ -z "${LOG_LIST}" ]]; then
    echo "No training logs found on ${SERVER} at ${LOG_DIR}/"
    # Also check for PID files to show task status
    ssh "${SSH_TARGET}" "ls ${LOG_DIR}/.pid_* 2>/dev/null" | while read pf; do
        pid=$(ssh "${SSH_TARGET}" "cat '$pf' 2>/dev/null" || echo '?')
        name=$(basename "$pf" .log | sed 's/^\.pid_//')
        echo "  PID file: $name -> PID=$pid"
    done || true
    exit 1
fi

# If --last, pick the newest
if [[ "${KEYWORD}" == "__latest__" ]]; then
    MATCHED=$(echo "${LOG_LIST}" | head -1 | awk '{print $NF}')
elif [[ -n "${KEYWORD}" ]]; then
    # Filter by keyword
    MATCHED=$(echo "${LOG_LIST}" | grep -i "${KEYWORD}" | head -1 | awk '{print $NF}' || true)
    if [[ -z "${MATCHED}" ]]; then
        echo "No log matching '${KEYWORD}'. Available:"
        echo "${LOG_LIST}" | awk '{print "  " $NF, "(" $5, $6, $7 ")"}'
        exit 1
    fi
else
    # No keyword: list all available logs
    LOG_COUNT=$(echo "${LOG_LIST}" | wc -l)
    echo ""
    echo "Found ${LOG_COUNT} log(s), use a keyword to pick one:"
    echo "${LOG_LIST}" | awk '{printf "  %-60s  %s %s %s\n", $NF, $5, $6, $7}'
    echo ""
    echo "  $0 ${SERVER} --last           # view newest log"
    echo "  $0 ${SERVER} <keyword>        # filter by keyword (e.g. 'pointgate')"
    exit 0
fi

echo "Log: ${MATCHED}"
echo ""

if [[ "${FOLLOW}" == "-f" ]]; then
    ssh "${SSH_TARGET}" "tail -f ${MATCHED}"
else
    ssh "${SSH_TARGET}" "tail -${LINES} ${MATCHED}"
fi
