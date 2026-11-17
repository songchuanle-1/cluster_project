#!/usr/bin/env bash
set -euo pipefail
root=/data3/songcl/Project/Cluster_project/Cluster
run=/data3/songcl/Project/Cluster_project/pipeline/pdc_predict_resources_20261009
mkdir -p "$run"
exec 9>/tmp/cluster_project_gpu7_exclusive.lock
flock -n 9 || exit 2
used=$(nvidia-smi -i 7 --query-gpu=memory.used --format=csv,noheader,nounits)
(( used < 1024 )) || exit 2
source /data3/songcl/miniconda3/etc/profile.d/conda.sh
conda activate project_cluster
export CUDA_VISIBLE_DEVICES=7 PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$root/scripts:$root:$root/framework/lib"
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$CONDA_PREFIX/lib/python3.10/site-packages/torch/lib:${LD_LIBRARY_PATH:-}"
for target in baseline champion candidate; do
    timeout --signal=TERM --kill-after=15s 300s \
        python "$root/scripts/validate_pdc_20261009.py" resource \
        --target "$target" --root "$root" --output "$run/$target.json" \
        > "$run/$target.log" 2>&1 \
        || { tail -n 30 "$run/$target.log"; exit 1; }
    sha256sum "$run/$target.json"
done
printf 'complete %s\n' "$(date -Is)" > "$run/status"
