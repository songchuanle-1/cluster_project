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
#   bash scripts/remote_train.sh server-2 configs/modelbase2/model_base2.yaml 0
#   bash scripts/remote_train.sh server-4 configs/Quard/model_base1_quard2_c2f_enc_lite.yaml 0,1 2
# ============================================================

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(dirname "${SCRIPT_DIR}")/Cluster}"
SERVERS_YAML="$(dirname "${PROJECT_DIR}")/SERVERS.yaml"

SERVER="${1:-}"
CFG="${2:-}"
GPU_IDS="${3:-0}"
NUM_GPUS="${4:-1}"

if [[ -z "${SERVER}" || -z "${CFG}" ]]; then
    echo "Usage: $0 <server> <config> [gpu_ids] [num_gpus]"
    echo ""
    echo "Available servers:"
    python -c "
import yaml
with open('${SERVERS_YAML}') as f:
    cfg = yaml.safe_load(f)
for name in cfg.get('servers', {}):
    if name != 'local': print(f'  - {name}')
" 2>/dev/null
    echo ""
    echo "Example: $0 server-4 configs/Quard/model_base1_quard2_c2f_enc_lite.yaml 0"
    echo "         $0 server-2 configs/modelbase2/model_base2.yaml 0"
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
    echo "Error: server '${SERVER}' not found in ${SERVERS_YAML}"
    exit 1
fi

SSH_TARGET="${USER}@${HOST}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CFG_BASENAME=$(basename "${CFG}" .yaml)
GPU_IDS_EXPANDED="${GPU_IDS//,/ }"

echo "============================================"
echo "Remote Training: ${SERVER} (${SSH_TARGET})"
echo "Config:      ${CFG}"
echo "GPU IDs:     ${GPU_IDS} (${NUM_GPUS} GPUs)"
echo "Remote:      ${REMOTE_CODE_ROOT}"
echo "Env:         ${CONDA_ENV}"
echo "data_root:   ${LOCAL_DATA_ROOT%/} -> ${REMOTE_DATA_ROOT%/}"
echo "work_dir:    ${LOCAL_WORK_DIR} -> ${REMOTE_WORK_DIR}"
echo "============================================"

# ----- Step 1: Check local uncommitted changes -----
echo ""
echo "[1/6] Checking local changes..."
cd "${PROJECT_DIR}"
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "Error: Not a git repo."
    exit 1
fi
CHANGES=$(git status --porcelain 2>/dev/null | grep -v '^\?\?' | head -10 || true)
if [[ -n "${CHANGES}" ]]; then
    echo "Uncommitted changes detected, auto-committing..."
    git add -A
    git commit -m "auto: before remote training [${TIMESTAMP}]" || true
fi

# ----- Step 2: Sync code -----
echo ""
echo "[2/6] Syncing code to ${SERVER}..."
PROJECT_DIR="${PROJECT_DIR}" bash "${SCRIPT_DIR}/sync.sh" "${SERVER}"

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
        fi
    else
        echo 'WARNING: conda.sh not found at ${CONDA_SOURCE}'
    fi
    echo '--- GPU ---'
    nvidia-smi --query-gpu=name,memory.free --format=csv,noheader 2>/dev/null || echo 'nvidia-smi failed'
    echo '--- Data ---'
    ls '${REMOTE_DATA_ROOT}'scanrefer/ 2>/dev/null | head -2 || echo 'WARNING: scanrefer not found'
    ls '${REMOTE_DATA_ROOT}'sp_unet_backbone.pth 2>/dev/null && echo 'pretrain: OK' || echo 'WARNING: pretrain not found'
    echo '--- Disk ---'
    df -h \$(dirname '${REMOTE_WORK_DIR}') 2>/dev/null | tail -1 || df -h / 2>/dev/null | tail -1
"

# ----- Step 4: Path adaptation -----
echo ""
echo "[4/6] Applying path mappings on remote..."
ssh "${SSH_TARGET}" "
    cd ${REMOTE_CODE_ROOT}

    # data_root
    if [[ '${REMOTE_DATA_ROOT}' != '${LOCAL_DATA_ROOT}' ]]; then
        echo \"data_root: ${LOCAL_DATA_ROOT%/} -> ${REMOTE_DATA_ROOT%/}\"
        count=0
        for f in \$(grep -rl '${LOCAL_DATA_ROOT%/}' configs/ 2>/dev/null || true); do
            sed -i \"s|${LOCAL_DATA_ROOT%/}|${REMOTE_DATA_ROOT%/}|g; s|${LOCAL_DATA_ROOT}|${REMOTE_DATA_ROOT%/}|g\" \"\$f\"
            count=\$((count + 1))
        done
        echo \"  patched \$count config file(s)\"
    else
        echo 'data_root: same, skip'
    fi

    # work_dir
    if [[ '${REMOTE_WORK_DIR}' != '${LOCAL_WORK_DIR}' ]]; then
        echo \"work_dir: ${LOCAL_WORK_DIR} -> ${REMOTE_WORK_DIR}\"
        count=0
        for f in \$(grep -rl '${LOCAL_WORK_DIR}' configs/ 2>/dev/null || true); do
            sed -i \"s|${LOCAL_WORK_DIR}|${REMOTE_WORK_DIR}|g\" \"\$f\"
            count=\$((count + 1))
        done
        echo \"  patched \$count config file(s)\"
    else
        echo 'work_dir: same, skip'
    fi

    # pretrain
    if [[ '${REMOTE_DATA_ROOT}' != '${LOCAL_DATA_ROOT}' ]]; then
        echo 'pretrain: updating to match data_root'
        sed -i \"s|${LOCAL_DATA_ROOT%/}/sp_unet_backbone.pth|${REMOTE_DATA_ROOT%/}/sp_unet_backbone.pth|g\" configs/*.yaml 2>/dev/null || true
    fi

    # cleanup
    find configs/ -name '*.bak' -delete 2>/dev/null || true
    echo 'Path adaptation complete.'
"

# ----- Step 5: Launch training -----
echo ""
echo "[5/6] Launching training on ${SERVER}..."
REMOTE_LOG_FILE="${REMOTE_CODE_ROOT}/logs/train_${CFG_BASENAME}_${TIMESTAMP}.log"

ssh "${SSH_TARGET}" "
    mkdir -p ${REMOTE_CODE_ROOT}/logs
    cd ${REMOTE_CODE_ROOT}
    source ${CONDA_SOURCE}
    conda activate ${CONDA_ENV}
    export PYTHONPATH=${REMOTE_CODE_ROOT}:${REMOTE_CODE_ROOT}/framework/lib:\${PYTHONPATH:-}
    # nvidia pip 包目录 (torch>=2.x 的 libcudart/nccl 在 site-packages/nvidia/, 需优先于系统 /usr/local/cuda, 否则 libc10_cuda undefined symbol)
    export LD_LIBRARY_PATH=\$(python -c 'import torch,os;print(os.path.dirname(torch.__file__))')/lib:\$(find \${CONDA_PREFIX}/lib/python*/site-packages/nvidia/cuda_runtime/lib -maxdepth 0 2>/dev/null):\$LD_LIBRARY_PATH
    echo 'Starting: python tools/train.py ${CFG} --gpu_ids ${GPU_IDS_EXPANDED} --num_gpus ${NUM_GPUS}'
    echo 'Log: ${REMOTE_LOG_FILE}'
    nohup python tools/train.py ${CFG} --gpu_ids ${GPU_IDS_EXPANDED} --num_gpus ${NUM_GPUS} \
        > ${REMOTE_LOG_FILE} 2>&1 &
    TRAIN_PID=\$!
    echo \"\${TRAIN_PID}\" > ${REMOTE_CODE_ROOT}/logs/.pid_${CFG_BASENAME}
    echo \"PID: \${TRAIN_PID}\"
    sleep 5
    if kill -0 \${TRAIN_PID} 2>/dev/null; then
        echo 'Training started successfully!'
    else
        echo 'ERROR: Training process died! Last 20 lines:'
        tail -20 ${REMOTE_LOG_FILE}
        exit 1
    fi
"

# ----- Step 6: Summary -----
echo ""
echo "[6/6] ========================================"
echo "  Training launched on ${SERVER}"
echo "  Config:   ${CFG}"
echo "  GPU:      ${GPU_IDS}"
echo "  View log: bash scripts/remote_log.sh ${SERVER} ${CFG_BASENAME}"
echo "  Status:   bash scripts/remote_status.sh ${SERVER}"
echo "  Kill:     bash scripts/remote_kill.sh ${SERVER} ${CFG_BASENAME}"
echo "============================================"
