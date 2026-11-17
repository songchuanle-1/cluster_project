#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# remote_resume.sh — 从 checkpoint 恢复远程训练
# ============================================================
# 用法:
#   bash scripts/remote_resume.sh <server> <config> <gpu_ids> [checkpoint]
#
# 示例:
#   # 自动找最新的 last.pth
#   bash scripts/remote_resume.sh server-4 configs/Quard/xxx.yaml 1
#
#   # 指定 checkpoint
#   bash scripts/remote_resume.sh server-4 configs/Quard/xxx.yaml 1 /path/to/last.pth
# ============================================================

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(dirname "${SCRIPT_DIR}")/Cluster}"
SERVERS_YAML="$(dirname "${PROJECT_DIR}")/SERVERS.yaml"

SERVER="${1:-}"
CFG="${2:-}"
GPU_IDS="${3:-0}"
RESUME_CKPT="${4:-}"

if [[ -z "${SERVER}" || -z "${CFG}" ]]; then
    echo "Usage: $0 <server> <config> <gpu_ids> [checkpoint]"
    echo "  If checkpoint omitted, auto-finds latest last.pth"
    echo "Example: $0 server-4 configs/Quard/xxx.yaml 1"
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
CONDA_SOURCE=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "conda_source")
CONDA_ENV=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "conda_env")
REMOTE_DATA_ROOT=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "data_root")
REMOTE_WORK_DIR=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "work_dir")
LOCAL_DATA_ROOT=$(get_yaml_value "${SERVERS_YAML}" "local" "data_root")
LOCAL_WORK_DIR=$(get_yaml_value "${SERVERS_YAML}" "local" "work_dir")

if [[ -z "${HOST}" ]]; then
    echo "Error: server '${SERVER}' not found in SERVERS.yaml"
    exit 1
fi

SSH_TARGET="${USER}@${HOST}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CFG_BASENAME=$(basename "${CFG}" .yaml)
GPU_IDS_EXPANDED="${GPU_IDS//,/ }"

echo "============================================"
echo "Remote Resume: ${SERVER} (${SSH_TARGET})"
echo "Config:   ${CFG}"
echo "GPU IDs:  ${GPU_IDS}"
echo "============================================"

# ----- Step 1: Sync code -----
echo "[1/5] Syncing code..."
bash "${SCRIPT_DIR}/sync.sh" "${SERVER}"

# ----- Step 2: Path adaptation -----
echo ""
echo "[2/5] Applying path mappings..."
ssh "${SSH_TARGET}" "
    cd ${REMOTE_CODE_ROOT}
    if [[ '${REMOTE_DATA_ROOT}' != '${LOCAL_DATA_ROOT}' ]]; then
        for f in \$(grep -rl '${LOCAL_DATA_ROOT%/}' configs/ 2>/dev/null || true); do
            sed -i \"s|${LOCAL_DATA_ROOT%/}|${REMOTE_DATA_ROOT%/}|g; s|${LOCAL_DATA_ROOT}|${REMOTE_DATA_ROOT%/}|g\" \"\$f\"
        done
    fi
    if [[ '${REMOTE_WORK_DIR}' != '${LOCAL_WORK_DIR}' ]]; then
        for f in \$(grep -rl '${LOCAL_WORK_DIR}' configs/ 2>/dev/null || true); do
            sed -i \"s|${LOCAL_WORK_DIR}|${REMOTE_WORK_DIR}|g\" \"\$f\"
        done
    fi
    find configs/ -name '*.bak' -delete 2>/dev/null || true
    echo 'Path adaptation done.'
"

# ----- Step 3: Find checkpoint -----
echo ""
echo "[3/5] Finding checkpoint..."
if [[ -z "${RESUME_CKPT}" ]]; then
    # Auto-find latest last.pth
    RESUME_CKPT=$(ssh "${SSH_TARGET}" "
        ls -t ${REMOTE_WORK_DIR}/${CFG_BASENAME}/*/last.pth 2>/dev/null | head -1
    " || true)
    if [[ -z "${RESUME_CKPT}" ]]; then
        # Try best.pth
        RESUME_CKPT=$(ssh "${SSH_TARGET}" "
            ls -t ${REMOTE_WORK_DIR}/${CFG_BASENAME}/*/best.pth 2>/dev/null | head -1
        " || true)
    fi
fi

if [[ -z "${RESUME_CKPT}" ]]; then
    echo "ERROR: No checkpoint found at ${REMOTE_WORK_DIR}/${CFG_BASENAME}/*/"
    echo "Specify manually: $0 ${SERVER} ${CFG} ${GPU_IDS} /path/to/checkpoint.pth"
    exit 1
fi

echo "Resume from: ${RESUME_CKPT}"

# ----- Step 4: Launch training with --resume -----
echo ""
echo "[4/5] Launching resumed training..."
REMOTE_LOG_DIR="${REMOTE_CODE_ROOT}/logs"
REMOTE_LOG_FILE="${REMOTE_LOG_DIR}/train_${CFG_BASENAME}_${TIMESTAMP}.log"

ssh "${SSH_TARGET}" "
    mkdir -p ${REMOTE_LOG_DIR}
    cd ${REMOTE_CODE_ROOT}
    source ${CONDA_SOURCE}
    conda activate ${CONDA_ENV}
    export PYTHONPATH=${REMOTE_CODE_ROOT}:${REMOTE_CODE_ROOT}/framework/lib:\${PYTHONPATH:-}
    echo 'Resuming from: ${RESUME_CKPT}'
    echo 'Log: ${REMOTE_LOG_FILE}'
    nohup python tools/train.py ${CFG} --gpu_ids ${GPU_IDS_EXPANDED} --num_gpus 1 \
        --resume ${RESUME_CKPT} \
        > ${REMOTE_LOG_FILE} 2>&1 &
    TRAIN_PID=\$!
    echo \"\${TRAIN_PID}\" > ${REMOTE_LOG_DIR}/.pid_${CFG_BASENAME}
    echo \"PID: \${TRAIN_PID}\"
    sleep 5
    if kill -0 \${TRAIN_PID} 2>/dev/null; then
        echo 'Resumed training started!'
    else
        echo 'ERROR: Process died! Check log:'
        tail -20 ${REMOTE_LOG_FILE}
        exit 1
    fi
"

# ----- Step 5: Summary -----
echo ""
echo "[5/5] ========================================"
echo "  Resumed training on ${SERVER}"
echo "  Config:    ${CFG}"
echo "  Checkpoint: ${RESUME_CKPT}"
echo "  GPU:       ${GPU_IDS}"
echo "  View log:  bash scripts/remote_log.sh ${SERVER} ${CFG_BASENAME}"
echo "  Kill:      bash scripts/remote_kill.sh ${SERVER} ${CFG_BASENAME}"
echo "============================================"
