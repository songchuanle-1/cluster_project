#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/train.sh [NUM_GPUS] [GPU_IDS] [CONFIG]
#
# Examples:
#   ./scripts/train.sh 1 0                           # single GPU 0
#   ./scripts/train.sh 2 0,1 configs/model_agent1.yaml # multi-GPU 0 and 1
NUM_GPUS="${1:-1}"
GPU_IDS_RAW="${2:-0}"

CFG="${3:-configs/model_agent1.yaml}"

# Resolve project root (the parent of this script's directory)
SCRIPT_DIR="$( cd -- "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$(dirname "${SCRIPT_DIR}")"

# Prefer the conda test env python, fall back to PATH
PYTHON_BIN="/home/songcl/.conda/envs/test/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="$(command -v python || true)"
fi
if [[ -z "${PYTHON_BIN}" ]]; then
  echo "Error: python not found in /home/songcl/.conda/envs/test or PATH" >&2
  exit 1
fi

# # Ensure project libs are importable
export PYTHONPATH="${ROOT_DIR}:${ROOT_DIR}/framework/lib:${PYTHONPATH:-}"
# Ensure project libs are importable
# Add DEST3D path so that nested 'issm_triton' becomes importable
# export PYTHONPATH="${ROOT_DIR}:${ROOT_DIR}/framework/lib:${ROOT_DIR}/framework/DEST3D:${PYTHONPATH:-}"
# cd "${ROOT_DIR}"

# echo "==== Launching training ===="
# echo "Python: ${PYTHON_BIN}"
# ${PYTHON_BIN} -V || true

# echo "Project root: ${ROOT_DIR}"
# echo "PYTHONPATH: ${PYTHONPATH}"
# echo "Config: ${CFG}"
# echo "GPU IDs: ${GPU_IDS_RAW}"

# date
# nvidia-smi || true

# # Start training
GPU_IDS_EXPANDED=${GPU_IDS_RAW//,/ }
"${PYTHON_BIN}" tools/train.py "${CFG}" --gpu_ids ${GPU_IDS_EXPANDED} --num_gpus "${NUM_GPUS}"
# # 进入项目目录
# cd /data/songcl/3dres/Agent_project/Agent
# # 激活环境
# conda activate test
# # 确保能到本地扩展（pointgroup_ops）
# export PYTHONPATH=/data/songcl/3dres/Agent_project/Agent:/data/songcl/3dres/Agent_project/Agent/framework/lib:$PYTHONPATH
# # 启动训练（示例用 GPU 1）
# python tools/train.py configs/model_agent1.yaml --gpu_ids 1