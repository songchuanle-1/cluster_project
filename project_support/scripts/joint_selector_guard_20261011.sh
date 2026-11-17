#!/usr/bin/env bash
set -euo pipefail
exec 9>/tmp/cluster_project_gpu7_slot2_diagnostic.lock
flock -n 9
uuid=GPU-7b284db0-8d77-1b8d-e89a-15a4af73de2a
actual="$(nvidia-smi -i 7 --query-gpu=uuid --format=csv,noheader)"
test "$actual" = "$uuid"
if nvidia-smi --query-compute-apps=gpu_uuid --format=csv,noheader | grep -Fxq "$uuid"; then
    echo "GPU7 occupied; diagnostic not started"
    exit 75
fi
mem="$(nvidia-smi -i 7 --query-gpu=memory.used --format=csv,noheader,nounits | tr -d ' ')"
test "$mem" -lt 1000
source /data3/songcl/miniconda3/etc/profile.d/conda.sh
conda activate project_cluster
export CUDA_VISIBLE_DEVICES=7 PYTHONDONTWRITEBYTECODE=1
root=/data3/songcl/Project/Cluster_project/Cluster
export PYTHONPATH="$root/scripts:$root:$root/framework/lib"
manifest=/data3/songcl/Project/Cluster_project/pipeline/m95_multiword_capture_manifest_20260928.json
output=/data3/songcl/Project/Cluster_project/pipeline/joint_selector_result_20261011.json
extra=()
if [ "${1:-}" = "population" ] || [ "${1:-}" = "backward" ] || [ "${1:-}" = "equivalence" ]; then
  manifest=/data3/songcl/Project/Cluster_project/pipeline/point_detail_population_20261009/result.manifest.json
  output=/data3/songcl/Project/Cluster_project/pipeline/joint_selector_population_20261011.json
  extra=(--population)
  if [ "$1" = "backward" ]; then
    output=/data3/songcl/Project/Cluster_project/pipeline/joint_selector_backward_20261011.json
    extra+=(--full-backward)
  elif [ "$1" = "equivalence" ]; then
    output=/data3/songcl/Project/Cluster_project/pipeline/joint_selector_equivalence_20261011.json
    extra+=(--equivalence)
  fi
elif [ -n "${1:-}" ]; then
  echo "Unknown diagnostic case"
  exit 2
fi
timeout --signal=TERM --kill-after=20 900 python \
  /data3/songcl/Project/Cluster_project/pipeline/joint_selector_probe_20261011.py \
  --root "$root" \
  --checkpoint /data3/songcl/Project/Cluster_project/pipeline/scm_admission_20260914/best.pth \
  --manifest "$manifest" --output "$output" "${extra[@]}"
