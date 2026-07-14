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
#   bash scripts/remote_train.sh dual-3090 configs/modelbase2/model_base2.yaml 0
#   bash scripts/remote_train.sh server-3 configs/Quard/model_base1_quard2_c2f_enc_lite.yaml 0,1 2
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
    echo "Available servers: dual-3090, server-3, server-4"
    echo "Example: $0 server-4 configs/Quard/model_base1_quard2_c2f_enc_lite.yaml 0"
    echo "         $0 dual-3090 configs/modelbase2/model_base2.yaml 0"
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
CONDA_SOURCE=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "conda_source")
CONDA_ENV=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "conda_env")
REMOTE_DATA_ROOT=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "data_root")
REMOTE_WORK_DIR=$(get_yaml_value "${SERVERS_YAML}" "${SERVER}" "work_dir")

# 本地 data_root（从 local 节点取）
LOCAL_DATA_ROOT=$(get_yaml_value "${SERVERS_YAML}" "local" "data_root")
LOCAL_WORK_DIR=$(get_yaml_value "${SERVERS_YAML}" "local" "work_dir")

if [[ -z "${HOST}" ]]; then
    echo "Error: server '${SERVER}' not found in SERVERS.yaml"
    echo "Available servers: dual-3090, server-3, server-4"
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
echo "data_root:   ${LOCAL_DATA_ROOT} -> ${REMOTE_DATA_ROOT}"
echo "work_dir:    ${LOCAL_WORK_DIR} -> ${REMOTE_WORK_DIR}"
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
        fi
    else
        echo 'WARNING: conda.sh not found at ${CONDA_SOURCE}'
    fi
    echo '--- GPU ---'
    nvidia-smi --query-gpu=name,memory.free --format=csv,noheader 2>/dev/null || echo 'nvidia-smi failed'
    echo '--- Data ---'
    ls '${REMOTE_DATA_ROOT}'/scanrefer/ 2>/dev/null | head -2 || echo 'WARNING: scanrefer data not found'
    ls '${REMOTE_DATA_ROOT}'/sp_unet_backbone.pth 2>/dev/null && echo 'pretrain: OK' || echo 'WARNING: pretrain not found'
    echo '--- Disk ---'
    df -h \$(dirname '${REMOTE_WORK_DIR}') 2>/dev/null | tail -1 || df -h / 2>/dev/null | tail -1
"

# ----- Step 4: Path adaptation -----
echo ""
echo "[4/6] Applying path mappings on remote..."
ssh "${SSH_TARGET}" "
    cd ${REMOTE_CODE_ROOT}

    # data_root 替换（含各种变体：带不带末尾/）
    if [[ '${REMOTE_DATA_ROOT}' != '${LOCAL_DATA_ROOT}' ]]; then
        echo \"data_root: ${LOCAL_DATA_ROOT} -> ${REMOTE_DATA_ROOT}\"
        for pattern in '${LOCAL_DATA_ROOT%/}' '${LOCAL_DATA_ROOT}'; do
            replacement='${REMOTE_DATA_ROOT%/}'
            grep -rl \"\${pattern}\" configs/ 2>/dev/null | while read f; do
                sed -i \"s|\${pattern}|\${replacement}|g\" \"\$f\"
                echo \"  patched data_root: \$f\"
            done
        done
    else
        echo 'data_root: same on both sides, no patching needed'
    fi

    # work_dir 替换
    if [[ '${REMOTE_WORK_DIR}' != '${LOCAL_WORK_DIR}' ]]; then
        echo \"work_dir: ${LOCAL_WORK_DIR} -> ${REMOTE_WORK_DIR}\"
        grep -rl '${LOCAL_WORK_DIR}' configs/ 2>/dev/null | while read f; do
            sed -i \"s|${LOCAL_WORK_DIR}|${REMOTE_WORK_DIR}|g\" \"\$f\"
            echo \"  patched work_dir: \$f\"
        done
    else
        echo 'work_dir: same on both sides, no patching needed'
    fi

    # pretrain 路径替换（如果 data_root 不同，pretrain 里的本地路径也要改）
    # pretrain 最常见的值是 \${LOCAL_DATA_ROOT}sp_unet_backbone.pth
    LOCAL_PRETRAIN='${LOCAL_DATA_ROOT%/}/sp_unet_backbone.pth'
    REMOTE_PRETRAIN='${REMOTE_DATA_ROOT%/}/sp_unet_backbone.pth'
    if [[ \"\${LOCAL_PRETRAIN}\" != \"\${REMOTE_PRETRAIN}\" ]]; then
        echo \"pretrain: \${LOCAL_PRETRAIN} -> \${REMOTE_PRETRAIN}\"
        grep -rl \"\${LOCAL_PRETRAIN}\" configs/ 2>/dev/null | while read f; do
            sed -i \"s|\${LOCAL_PRETRAIN}|\${REMOTE_PRETRAIN}|g\" \"\$f\"
            echo \"  patched pretrain: \$f\"
        done
    fi

    # 去掉 .yaml.bak 备份文件（sed -i 在某些系统上可能产生）
    find configs/ -name '*.bak' -delete 2>/dev/null || true

    echo 'Path adaptation complete.'
"

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
