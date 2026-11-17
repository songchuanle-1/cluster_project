#!/usr/bin/env bash
set -euo pipefail
root=/data3/songcl/Project/Cluster_project/Cluster
run=/data3/songcl/Project/Cluster_project/pipeline/point_detail_population_20261009
mkdir -p "$run"
test ! -e "$run/result.json"
exec 9>/tmp/cluster_project_gpu7_exclusive.lock
flock -n 9 || exit 2
used=$(nvidia-smi -i 7 --query-gpu=memory.used --format=csv,noheader,nounits)
(( used < 1024 )) || exit 2
source /data3/songcl/miniconda3/etc/profile.d/conda.sh
conda activate project_cluster
export CUDA_VISIBLE_DEVICES=7 PYTHONDONTWRITEBYTECODE=1 POINT_DETAIL_POPULATION=1
export PYTHONPATH="$root/scripts:$root:$root/framework/lib"
child=''
cleanup() {
    if [[ -n "$child" ]] && kill -0 "$child" 2>/dev/null; then
        kill -TERM "$child"
        wait "$child" || true
    fi
}
trap cleanup EXIT
trap 'exit 3' TERM INT
python "$root/scripts/m95_point_detail_capture_20261009.py" --root "$root" \
    --checkpoint /data3/songcl/Project/Cluster_project/pipeline/scm_admission_20260914/best.pth \
    --manifest "$root/scripts/m95_multiword_capture_manifest_20260928.json" \
    --output "$run/result.json" > "$run/stdout.log" 2>&1 &
child=$!
start=$SECONDS
while kill -0 "$child" 2>/dev/null; do
    sleep 5
    (( SECONDS - start < 600 )) || exit 3
done
if wait "$child"; then
    child=''
    sha256sum "$run/result.json" "$run/result.manifest.json"
    tail -n 1 "$run/stdout.log"
else
    child=''
    tail -n 20 "$run/stdout.log"
    exit 1
fi
