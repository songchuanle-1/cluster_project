#!/usr/bin/env bash
set -euo pipefail
exec 9>/tmp/cluster_project_gpu7_slot2_diagnostic.lock
flock -n 9
test "$(hostname)" = das
uuid=GPU-7b284db0-8d77-1b8d-e89a-15a4af73de2a
source /data3/songcl/miniconda3/etc/profile.d/conda.sh
conda activate project_cluster
export CUDA_VISIBLE_DEVICES=7 PYTHONDONTWRITEBYTECODE=1
root=/data3/songcl/Project/Cluster_project/Cluster
export PYTHONPATH="$root/scripts:$root:$root/framework/lib"
for target in target_role; do
  test "$(nvidia-smi -i 7 --query-gpu=uuid --format=csv,noheader)" = "$uuid"
  if nvidia-smi --query-compute-apps=gpu_uuid --format=csv,noheader | grep -Fxq "$uuid"; then
    echo "GPU7 occupied; resource worker not started"
    exit 75
  fi
  memory="$(nvidia-smi -i 7 --query-gpu=memory.used --format=csv,noheader,nounits | tr -d ' ')"
  test "$memory" -lt 1000
  nvidia-smi -i 7 --query-gpu=timestamp,uuid,utilization.gpu,memory.used,memory.total --format=csv,noheader
  timeout --signal=TERM --kill-after=20 360 python \
    /data3/songcl/Project/Cluster_project/pipeline/root_role_resources_v2_20261012_0810.py "$target"
done
