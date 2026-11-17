#!/usr/bin/env bash
set -euo pipefail
root=/data3/songcl/Project/Cluster_project/Cluster
run=/data3/songcl/Project/Cluster_project/pipeline/pdc_minimal_native_20261009
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
run_test() {
    name="$1"; shift
    timeout --signal=TERM --kill-after=15s 600s \
        python "$root/scripts/validate_pdc_20261009.py" "$@" \
        --root "$root" --output "$run/$name.json" > "$run/$name.log" 2>&1 \
        || { tail -n 30 "$run/$name.log"; exit 1; }
    sha256sum "$run/$name.json"
}
run_test native native
run_test batch2 native --group-batch-size 2
run_test candidate resource --target candidate
printf 'complete %s\n' "$(date -Is)" > "$run/status"
