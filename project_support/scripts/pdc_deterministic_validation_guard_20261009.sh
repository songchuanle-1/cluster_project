#!/usr/bin/env bash
set -euo pipefail
root=/data3/songcl/Project/Cluster_project/Cluster
run=/data3/songcl/Project/Cluster_project/pipeline/pdc_native_algo_v2_validation_20261009
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
child=''
cleanup() {
    if [[ -n "$child" ]] && kill -0 "$child" 2>/dev/null; then
        kill -TERM "$child"
        wait "$child" || true
    fi
}
trap cleanup EXIT
trap 'exit 3' TERM INT
run_test() {
    name="$1"; shift
    python "$root/scripts/validate_pdc_20261009.py" "$@" --root "$root" \
        --output "$run/$name.json" > "$run/$name.log" 2>&1 &
    child=$!
    start=$SECONDS
    while kill -0 "$child" 2>/dev/null; do
        sleep 5
        (( SECONDS - start < 600 )) || exit 3
    done
    if wait "$child"; then
        child=''
        sha256sum "$run/$name.json"
    else
        child=''
        tail -n 30 "$run/$name.log"
        exit 1
    fi
}
run_test contracts contracts
run_test native native
run_test baseline resource --target baseline
run_test champion resource --target champion
run_test candidate resource --target candidate
printf 'complete %s\n' "$(date -Is)" > "$run/status"
