#!/usr/bin/env bash
set -euo pipefail
# ============================================================
# remote_train.sh — 一键远程训练
# ============================================================
# 用法:
#   bash scripts/remote_train.sh <server> <config> [gpu_ids] [num_gpus]
#
# 示例:
#   bash scripts/remote_train.sh server-4 configs/Quard/model_base1_quard2_c2f_enc_lite.yaml 0
#   bash scripts/remote_train.sh server-4 configs/modelbase2/model_base2.yaml 0,1 2
# ============================================================

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"
SERVERS_YAML="${ROOT_DIR}/SERVERS.yaml"

SERVER="${1:-}"
CFG="${2:-}"
GPU_IDS="${3:-0}"
NUM_GPUS="${4:-1}"

if [[ -z "${SERVER}" || -z "${CFG}" ]]; then
    echo "Usage: $0 <server> <config> [gpu_ids] [num_gpus]"
    echo "Example: $0 server-4 configs/Quard/model_base1_quard2_c2f_enc_lite.yaml 0"
    echo "         $0 server-4 configs/modelbase2/model_base2.yaml 0,1 2"
    exit 1
fi

# ----- 解析 SERVERS.yaml -----
get_yaml_value() {
    local file="$1" section="$2" key="$3"
    python3 -c "
import sys
data = open('${file}').read()
in_section = False
for line in data.split('\n'):
    line = line.rstrip()
    if line.startswith('${section}:'):
        in_section = True
        continue
    if in_section:
        if line and not line.startswith(' ') and not line.startswith('\t'):
            break
        stripped = line.strip()
        if stripped.startswith('${key}:'):
            val = stripped.split(':', 1)[1].strip()
            val = val.strip('\"').strip(\"'\")
            print(val)
            break
" 2>/dev/null
}

# Also get path_mappings
get_path_mapping() {
    local file="$1" mapping_key="$2" dir_key="$3"
    python3 -c "
import sys
data = open('${file}').read()
in_mapping = False
in_section = False
for line in data.split('\n'):
    line = line.rstrip()
    if line.startswith('path_mappings:'):
        in_mapping = True
        continue
    if in_mapping:
        if line and not line.startswith(' ') and not line.startswith('\t'):
            break
        stripped = line.strip()
        if stripped.startswith('${mapping_key}:'):
            in_section = True
            continue
        if in_section and stripped.startswith('${dir_key}:'):
            val = stripped.split(':', 1)[1].strip().strip('\"').strip(\"'\")
            print(val)
            break
" 2>/dev/null
}

HOST=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "host")
USER=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "user")
REMOTE_CODE_ROOT=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "remote_code_root")
CONDA_SOURCE=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "conda_source")
CONDA_ENV=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "conda_env")
REMOTE_WORK_DIR=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "work_dir")
LOCAL_WORK_DIR=$(get_path_mapping "${SERVERS_YAML}" "work_dir" "local")
REMOTE_WORK_DIR_MAPPED=$(get_path_mapping "${SERVERS_YAML}" "work_dir" "remote")

if [[ -z "${HOST}" ]]; then
    echo "Error: server '${SERVER}' not found in SERVERS.yaml"
    exit 1
fi

SSH_TARGET="${USER}@${HOST}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CFG_BASENAME=$(basename "${CFG}" .yaml)
GPU_IDS_EXPANDED="${GPU_IDS//,/ }"

echo "============================================"
echo "Remote Training: ${SERVER} (${SSH_TARGET})"
echo "Config:  ${CFG}"
echo "GPU IDs: ${GPU_IDS} (${NUM_GPUS} GPUs)"
echo "Remote:  ${REMOTE_CODE_ROOT}"
echo "Env:     ${CONDA_ENV}"
echo "============================================"

# ----- Step 1: Check local uncommitted changes -----
echo ""
echo "[1/6] Checking local changes..."
cd "${ROOT_DIR}"
if git rev-parse --git-dir >/dev/null 2>&1; then
    CHANGES=$(git status --porcelain 2>/dev/null | grep -v '^\?\?' | head -10 || true)
    if [[ -n "${CHANGES}" ]]; then
        echo "Warning: local uncommitted changes detected:"
        echo "${CHANGES}"
        echo "Consider committing before sync (auto-commit in 3s...)"
        sleep 3
        git add -A
        git commit -m "Auto-commit before remote training [${TIMESTAMP}]" || true
    fi
else
    echo "Error: Not a git repo. Run 'git init && git add -A && git commit -m \"Initial commit\"' first."
    exit 1
fi

# ----- Step 2: Sync code -----
echo ""
echo "[2/6] Syncing code to ${SERVER}..."
bash "${SCRIPT_DIR}/sync.sh" "${SERVER}"

# ----- Step 3: Check remote environment -----
echo ""
echo "[3/6] Checking remote environment..."
ssh "${SSH_TARGET}" "
    echo '--- Conda ---'
    if [[ -f '${CONDA_SOURCE}' ]]; then
        source '${CONDA_SOURCE}'
        if conda env list 2>/dev/null | grep -q '${CONDA_ENV}'; then
            echo 'Conda env ${CONDA_ENV}: OK'
        else
            echo 'WARNING: Conda env ${CONDA_ENV} not found!'
            echo 'Run: conda create -n ${CONDA_ENV} python=3.10 -y'
        fi
    else
        echo 'WARNING: conda.sh not found at ${CONDA_SOURCE}'
    fi
    echo '--- GPU ---'
    nvidia-smi --query-gpu=name,memory.free --format=csv,noheader 2>/dev/null || echo 'nvidia-smi failed'
    echo '--- Data ---'
    ls -d ${REMOTE_CODE_ROOT}/data_root/ 2>/dev/null || true
    echo '--- Disk ---'
    df -h /data 2>/dev/null | tail -1 || df -h /home 2>/dev/null | tail -1
"

# ----- Step 4: Path adaptation -----
echo ""
echo "[4/6] Applying path mappings on remote..."
if [[ -n "${LOCAL_WORK_DIR}" && -n "${REMOTE_WORK_DIR_MAPPED}" ]]; then
    ssh "${SSH_TARGET}" "
        cd ${REMOTE_CODE_ROOT}
        echo 'work_dir: ${LOCAL_WORK_DIR} -> ${REMOTE_WORK_DIR_MAPPED}'
        grep -rl '${LOCAL_WORK_DIR}' configs/ | while read f; do
            echo \"  patching: \$f\"
            sed -i \"s|${LOCAL_WORK_DIR}|${REMOTE_WORK_DIR_MAPPED}|g\" \"\$f\"
        done
    "
fi

# ----- Step 5: Launch training -----
echo ""
echo "[5/6] Launching training on ${SERVER}..."
REMOTE_LOG_DIR="${REMOTE_CODE_ROOT}/logs"
REMOTE_LOG_FILE="${REMOTE_LOG_DIR}/train_${CFG_BASENAME}_${TIMESTAMP}.log"

ssh "${SSH_TARGET}" "
    mkdir -p ${REMOTE_LOG_DIR}
    cd ${REMOTE_CODE_ROOT}
    source ${CONDA_SOURCE}
    conda activate ${CONDA_ENV}
    export PYTHONPATH=${REMOTE_CODE_ROOT}:${REMOTE_CODE_ROOT}/framework/lib:\${PYTHONPATH:-}
    echo 'Starting training...'
    echo 'Log: ${REMOTE_LOG_FILE}'
    nohup python tools/train.py ${CFG} --gpu_ids ${GPU_IDS_EXPANDED} --num_gpus ${NUM_GPUS} \
        > ${REMOTE_LOG_FILE} 2>&1 &
    TRAIN_PID=\$!
    echo \"\${TRAIN_PID}\" > ${REMOTE_LOG_DIR}/.pid_${CFG_BASENAME}
    echo \"PID: \${TRAIN_PID}\"
    # Wait a moment and check if still running
    sleep 3
    if kill -0 \${TRAIN_PID} 2>/dev/null; then
        echo 'Training started successfully!'
    else
        echo 'ERROR: Training process died! Check log:'
        tail -20 ${REMOTE_LOG_FILE}
        exit 1
    fi
"

# ----- Step 6: Summary -----
echo ""
echo "[6/6] ========================================"
echo "  Training launched on ${SERVER}"
echo "  View logs:   bash scripts/remote_log.sh ${SERVER}"
echo "  Check status: bash scripts/remote_status.sh ${SERVER}"
echo "  Kill training: bash scripts/remote_kill.sh ${SERVER}"
echo "============================================"
