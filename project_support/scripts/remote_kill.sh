#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# remote_kill.sh — 终止远程训练
# ============================================================
# 用法:
#   bash scripts/remote_kill.sh <server>              # 列出所有任务
#   bash scripts/remote_kill.sh <server> <keyword>    # 终止匹配关键字的任务
#   bash scripts/remote_kill.sh <server> <pid>        # 终止指定 PID
#   bash scripts/remote_kill.sh <server> --all        # 终止所有任务（需确认）
#
# 示例:
#   bash scripts/remote_kill.sh server-4               # 列出任务
#   bash scripts/remote_kill.sh server-4 pointgate     # 只杀 pointgate
#   bash scripts/remote_kill.sh server-4 2383067       # 杀指定 PID
#   bash scripts/remote_kill.sh server-4 --all         # 杀全部
# ============================================================

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(dirname "${SCRIPT_DIR}")/Cluster}"
SERVERS_YAML="$(dirname "${PROJECT_DIR}")/SERVERS.yaml"

SERVER="${1:-}"
KEYWORD="${2:-}"

if [[ -z "${SERVER}" ]]; then
    echo "Usage: $0 <server> [keyword|pid|--all]"
    echo ""
    echo "  <server>             服务器名"
    echo "  <keyword>            匹配训练任务关键字（如 pointgate）"
    echo "  <pid>                直接杀指定 PID"
    echo "  --all                终止所有任务"
    echo ""
    echo "Examples:"
    echo "  $0 server-4                    # 列出所有运行中的任务"
    echo "  $0 server-4 pointgate          # 只终止 pointgate 任务"
    echo "  $0 server-4 2383067            # 终止 PID 2383067"
    echo "  $0 server-4 --all              # 终止全部"
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

# ----- List running tasks -----
list_tasks() {
    ssh -n "${SSH_TARGET}" "
        printf '%-8s  %-55s  %s\n' 'PID' 'CONFIG' 'GPU_MEM'
        printf '%-8s  %-55s  %s\n' '--------' '-------------------------------------------------------' '-------'
        for pid in \$(ps aux | grep -E 'python.*tools/(train|test)' | grep -v grep | awk '{print \$2}'); do
            # Check if this process is running from our project directory
            cwd=\$(ls -l /proc/\$pid/cwd 2>/dev/null | awk '{print \$NF}' || echo '')
            if [[ \"\$cwd\" != '${REMOTE_CODE_ROOT}' ]]; then continue; fi
            cfg=\$(ps -p \$pid -o args --no-headers 2>/dev/null | grep -oP 'configs/\S+\.yaml' | head -1 || echo '?')
            gpu=\$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader 2>/dev/null | grep \"^\$pid,\" | cut -d, -f2 || echo '?')
            printf '%-8s  %-55s  %s\n' \"\$pid\" \"\$cfg\" \"\$gpu\"
        done
    " 2>/dev/null
}

echo "==== Tasks on ${SERVER} ===="
TASK_LIST=$(list_tasks)

if [[ -z "${TASK_LIST}" || "$(echo "${TASK_LIST}" | wc -l)" -le 2 ]]; then
    echo "No running training tasks found."
    exit 0
fi

echo "${TASK_LIST}"
echo ""

# ----- No keyword: just list and exit -----
if [[ -z "${KEYWORD}" ]]; then
    echo "Use a keyword to kill a specific task, or --all to kill all:"
    echo "  $0 ${SERVER} <keyword>     # kill matching task"
    echo "  $0 ${SERVER} --all          # kill all tasks"
    exit 0
fi

# ----- Kill specific task by keyword -----
kill_by_keyword() {
    local kw="$1"
    ssh "${SSH_TARGET}" "
        cd ${REMOTE_CODE_ROOT}
        KILLED=0

        # Kill by PID file match first (EXACT basename match — no substring, prevents mass-kill of prefix-sharing variants)
        for pf in ${REMOTE_CODE_ROOT}/logs/.pid_*; do
            pf_name=\$(basename \"\$pf\" | sed 's/^\.pid_//')
            if [[ \"\$pf_name\" == '${kw}' ]]; then
                pid=\$(cat \"\$pf\" 2>/dev/null || true)
                if [[ -n \"\${pid}\" ]] && kill -0 \$pid 2>/dev/null; then
                    echo \"Killing PID \$pid (\$pf_name)...\"
                    kill -TERM \$pid 2>/dev/null || true
                    sleep 2
                    kill -0 \$pid 2>/dev/null && kill -9 \$pid 2>/dev/null || true
                    rm -f \"\$pf\"
                    KILLED=1
                else
                    echo \"PID \$pid (\$pf_name) already dead, cleaning up.\"
                    rm -f \"\$pf\"
                fi
            fi
        done

        # Fallback: kill matching processes (check cwd to ensure same project)
        for pid in \$(ps aux | grep -E 'python.*tools/(train|test)' | grep -v grep | awk '{print \$2}'); do
            cwd=\$(ls -l /proc/\$pid/cwd 2>/dev/null | awk '{print \$NF}' || echo '')
            if [[ \"\$cwd\" != '${REMOTE_CODE_ROOT}' ]]; then continue; fi
            cmd=\$(ps -p \$pid -o args --no-headers 2>/dev/null)
            cfg_yaml=\$(echo \"\$cmd\" | grep -oP 'configs/\\S+\\.yaml' | head -1)
            cfg_bn=\$(basename \"\$cfg_yaml\" .yaml 2>/dev/null)
            if [[ \"\$cfg_bn\" == '${kw}' ]]; then
                echo \"Killing PID \$pid...\"
                kill -TERM \$pid 2>/dev/null || true
                KILLED=1
            fi
        done
        if [[ \$KILLED -eq 1 ]]; then
            sleep 2
            for pid in \$(ps aux | grep -E 'python.*tools/(train|test)' | grep -v grep | awk '{print \$2}'); do
                cwd=\$(ls -l /proc/\$pid/cwd 2>/dev/null | awk '{print \$NF}' || echo '')
                [[ \"\$cwd\" == '${REMOTE_CODE_ROOT}' ]] || continue
                kill -0 \$pid 2>/dev/null && kill -9 \$pid 2>/dev/null || true
            done
        fi

        if [[ \$KILLED -eq 0 ]]; then
            echo \"No task matching '${kw}' found.\"
        else
            echo 'Done.'
        fi
    "
}

# ----- Kill all tasks with confirmation -----
kill_all() {
    echo "This will kill ALL training tasks on ${SERVER}."
    echo -n "Are you sure? [y/N] "
    read -r confirm || confirm="n"
    if [[ "${confirm,,}" != "y" && "${confirm,,}" != "yes" ]]; then
        echo "Cancelled."
        exit 0
    fi

    ssh "${SSH_TARGET}" "
        cd ${REMOTE_CODE_ROOT}
        KILLED=0

        # Kill all PID files
        for pf in ${REMOTE_CODE_ROOT}/logs/.pid_*; do
            pid=\$(cat \"\$pf\" 2>/dev/null || true)
            if [[ -n \"\${pid}\" ]] && kill -0 \$pid 2>/dev/null; then
                echo \"Killing PID \$pid...\"
                kill -TERM \$pid 2>/dev/null || true
                KILLED=1
            fi
            rm -f \"\$pf\"
        done
        sleep 2

        # Kill remaining (check cwd to ensure same project)
        for pid in \$(ps aux | grep -E 'python.*tools/(train|test)' | grep -v grep | awk '{print \$2}'); do
            cwd=\$(ls -l /proc/\$pid/cwd 2>/dev/null | awk '{print \$NF}' || echo '')
            if [[ \"\$cwd\" == '${REMOTE_CODE_ROOT}' ]]; then
                echo \"Force killing PID \$pid...\"
                kill -9 \$pid 2>/dev/null || true
                KILLED=1
            fi
        done

        if [[ \$KILLED -eq 0 ]]; then
            echo 'No training processes found.'
        else
            echo 'All tasks terminated.'
        fi
    "
}

# ----- Kill by PID -----
kill_by_pid() {
    local pid="$1"
    ssh -n "${SSH_TARGET}" "
        if kill -0 ${pid} 2>/dev/null; then
            cwd=\$(ls -l /proc/${pid}/cwd 2>/dev/null | awk '{print \$NF}' || echo '')
            echo \"Killing PID ${pid} (cwd: \${cwd})...\"
            kill -TERM ${pid} 2>/dev/null || true
            sleep 2
            kill -0 ${pid} 2>/dev/null && kill -9 ${pid} 2>/dev/null && echo 'Force killed.' || true
            # Also clean up PID file if exists
            rm -f ${REMOTE_CODE_ROOT}/logs/.pid_* 2>/dev/null || true
            echo 'Done.'
        else
            echo \"PID ${pid} not found.\"
        fi
    "
}

# Dispatch
if [[ "${KEYWORD}" == "--all" ]]; then
    kill_all
elif [[ "${KEYWORD}" =~ ^[0-9]+$ ]]; then
    kill_by_pid "${KEYWORD}"
elif [[ -n "${KEYWORD}" ]]; then
    echo "Killing task matching: ${KEYWORD}"
    kill_by_keyword "${KEYWORD}"
fi

echo "==== Kill complete ===="
