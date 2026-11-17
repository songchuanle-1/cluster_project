#!/usr/bin/env bash
set -euo pipefail
root=/data3/songcl/Project/Cluster_project/Cluster
script="$root/scripts/m95_quality_assignment_capture_20261009.py"
run=/data3/songcl/Project/Cluster_project/pipeline/quality_assignment_20261009_0842
checkpoint=/data3/songcl/Project/Cluster_project/pipeline/scm_admission_20260914/best.pth
mkdir -p "$run"
test ! -e "$run/result.json"
exec 9>/tmp/cluster_project_gpu7_exclusive.lock
flock -n 9 || { printf 'exclusive_lease_busy\n' > "$run/status"; exit 2; }
used=$(nvidia-smi -i 7 --query-gpu=memory.used --format=csv,noheader,nounits)
(( used < 1024 )) || { printf 'gpu7_busy %s MiB\n' "$used" > "$run/status"; exit 2; }
source /data3/songcl/miniconda3/etc/profile.d/conda.sh
conda activate project_cluster
export CUDA_VISIBLE_DEVICES=7
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$root/scripts:$root:$root/framework/lib"
gpu_uuid=$(nvidia-smi -i 7 --query-gpu=uuid --format=csv,noheader)
sha256sum "$script" "$checkpoint" "$root/scripts/m95_multiword_capture_manifest_20260928.json" > "$run/inputs.sha256"
child=''
cleanup() {
    if [[ -n "$child" ]] && kill -0 "$child" 2>/dev/null; then
        kill -TERM "$child"
        wait "$child" || true
    fi
}
trap cleanup EXIT
trap 'exit 3' TERM INT
printf 'running %s\n' "$(date -Is)" > "$run/status"
python "$script" --root "$root" --checkpoint "$checkpoint" \
    --manifest "$root/scripts/m95_multiword_capture_manifest_20260928.json" \
    --output "$run/result.json" > "$run/stdout.log" 2>&1 &
child=$!
started=$SECONDS
while kill -0 "$child" 2>/dev/null; do
    sleep 5
    kill -0 "$child" 2>/dev/null || break
    if (( SECONDS - started > 900 )); then
        printf 'own_diagnostic_timeout\n' > "$run/status"
        exit 3
    fi
    foreign=$(nvidia-smi --query-compute-apps=pid,gpu_uuid,used_gpu_memory --format=csv,noheader,nounits |
        awk -F, -v uuid="$gpu_uuid" -v own="$child" '$2 ~ uuid && $1+0 != own && $3+0 > 1024 {print $1+0}')
    if [[ -n "$foreign" ]]; then
        printf 'foreign_gpu7_process %s; stop own diagnostic only\n' "$foreign" > "$run/status"
        exit 3
    fi
done
if wait "$child"; then
    child=''
    test -s "$run/result.json"
    sha256sum "$run/result.json" > "$run/result.sha256"
    printf 'complete %s\n' "$(date -Is)" > "$run/status"
    cat "$run/result.sha256"
else
    child=''
    printf 'native_capture_failed %s\n' "$(date -Is)" > "$run/status"
    tail -n 15 "$run/stdout.log"
    exit 1
fi
