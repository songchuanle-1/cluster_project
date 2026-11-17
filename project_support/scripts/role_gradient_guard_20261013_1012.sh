#!/usr/bin/env bash
set -euo pipefail
test "$#" -eq 1
exec 9>/tmp/cluster_project_gpu7_slot2_diagnostic.lock
flock -n 9
exec 8>/tmp/cluster_project_gpu7_diagnostic.lock
flock -n 8
test "$(hostname)" = das
uuid=GPU-7b284db0-8d77-1b8d-e89a-15a4af73de2a
test "$(nvidia-smi -i 7 --query-gpu=uuid --format=csv,noheader)" = "$uuid"
if nvidia-smi --query-compute-apps=gpu_uuid --format=csv,noheader | grep -Fxq "$uuid"; then
  echo "GPU7 occupied; no diagnostic started"
  exit 75
fi
memory="$(nvidia-smi -i 7 --query-gpu=memory.used --format=csv,noheader,nounits | tr -d ' ')"
test "$memory" -lt 1000
cd /data3/songcl/Project/Cluster_project/Cluster_checkpoints
export CUDA_VISIBLE_DEVICES=7 PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
timeout --signal=TERM --kill-after=20 600 \
  /data3/songcl/miniconda3/envs/project_cluster/bin/python -u \
  /data3/songcl/Project/Cluster_project/pipeline/role_gradient_native_20261013_1012.py \
  --token "$1"
