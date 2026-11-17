#!/usr/bin/env bash
set -euo pipefail

root=/data3/songcl/Project/Cluster_project/Cluster
bundle="$root/pipeline/diagnostic_bundles/manifest_capture_match_20260924"
prior="$root/pipeline/diagnostic_runs/m95_full_producer_boundary_20260926_0919"
script="$root/pipeline/diagnostic_runs/m95_full_order_first_stage_20260926_1120"
batches="$root/pipeline/diagnostic_runs/m95_frozen_target_batches_20260926_0659/batches"
run="$root/pipeline/diagnostic_runs/m95_full_order_first_stage_20260926_1435"
checkpoint=/data3/songcl/Project/Cluster_project/pipeline/scm_admission_20260914/best.pth
gpu_uuid=$(nvidia-smi -i 7 --query-gpu=uuid --format=csv,noheader)

mkdir -p "$run"
exec 9>/tmp/cluster_project_gpu7_exclusive.lock
if ! flock -n 9; then
    printf 'lease_unavailable\n' > "$run/status"
    exit 1
fi

check() {
    local got
    got=$(sha256sum "$2")
    if [[ "${got%% *}" != "$1" ]]; then
        printf 'input_hash_mismatch: %s\n' "$2" > "$run/status"
        exit 1
    fi
}
check b29f5a17d471bf8e53a5c53bea07688b07a82062aa759a3ba1eb63d7373677cc "$script/m95_full_order_first_stage_20260926.py"
check fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e "$checkpoint"
check 4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023 "$bundle/frozen_manifest.json"
check ed835ab21f071048e1d1cdd8fb19b6dd4ac24770b65e85ee4048931edb3d0529 "$batches/step_3137_row_83.pt"
check 0de128c44bb103ad2e3b7690e27e83b5d2f310c1e59b0087f9ddf2457dbbd742 "$prior/result.json"

gpu_used=$(nvidia-smi -i 7 --query-gpu=memory.used --format=csv,noheader,nounits)
if (( gpu_used > 1024 )); then
    printf 'gpu7_not_idle: %s MiB\n' "$gpu_used" > "$run/status"
    exit 1
fi

source /data3/songcl/miniconda3/etc/profile.d/conda.sh
conda activate project_cluster
export CUDA_VISIBLE_DEVICES=7
export PYTHONPATH="$prior${PYTHONPATH:+:$PYTHONPATH}"
printf 'running %s\n' "$(date -Is)" > "$run/status"
python "$script/m95_full_order_first_stage_20260926.py" \
    --root "$root" --bundle "$bundle" --checkpoint "$checkpoint" \
    --manifest "$bundle/frozen_manifest.json" \
    --batch "$batches/step_3137_row_83.pt" --full-order "$prior/result.json" \
    --output "$run/result.json" --progress "$run/progress.jsonl" \
    > "$run/stdout.log" 2>&1 &
child=$!

while kill -0 "$child" 2>/dev/null; do
    sleep 15
    if ! kill -0 "$child" 2>/dev/null; then
        break
    fi
    foreign=$(nvidia-smi --query-compute-apps=pid,gpu_uuid,used_gpu_memory \
        --format=csv,noheader,nounits |
        awk -F, -v uuid="$gpu_uuid" -v own="$child" \
        '$2 ~ uuid && $1+0 != own && $3+0 > 1024 { print $1+0 }')
    if [[ -n "$foreign" ]]; then
        printf 'foreign_gpu7_process: %s; terminating own PID %s\n' "$foreign" "$child" > "$run/status"
        kill -TERM "$child"
        wait "$child" || true
        exit 2
    fi
done

if wait "$child"; then
    test -s "$run/result.json"
    sha256sum "$run/result.json" > "$run/result.sha256"
    printf 'complete %s\n' "$(date -Is)" > "$run/status"
else
    printf 'diagnostic_failed %s\n' "$(date -Is)" > "$run/status"
    exit 1
fi
