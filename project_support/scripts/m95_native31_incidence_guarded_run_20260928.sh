#!/usr/bin/env bash
set -euo pipefail

root=/data3/songcl/Project/Cluster_project/Cluster
parent=/data3/songcl/Project/Cluster_project
run="$parent/pipeline/m95_native31_replay_20260928_1052"
script="$root/scripts/m95_native31_support_incidence_20260928.py"
adapter="$root/scripts/m95_multiword_native_31_20260928.py"
support="$root/scripts/m95_native31_physical_support_20260928.py"
manifest="$root/scripts/m95_multiword_capture_manifest_20260928.json"
checkpoint="$parent/pipeline/scm_admission_20260914/best.pth"
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
        printf 'input_hash_mismatch %s\n' "$2" > "$run/status"
        exit 1
    fi
}
check 021d36ba6b351976a1845e522ce910a56a9d3a8b425f6bd35142b5264509f3c4 "$script"
check 7bd1f022657d9dc96a53886ed2b8336386700ff048092abc4dc1e610380f85e1 "$adapter"
check 01ff763ee0c2dcae1c08240496f3a8b34099b86ddfa175f58ff9460494ae3e4f "$support"
check 3632d2686fa716d53760041afe51a7c333a474bcee3285ab57d2bf3d96930fe8 \
    "$root/scripts/m95_native31_support_contract_20260928.py"
check 85e108e8c86d65bcdbdc25061987e0a973fa45b35b00030d0721d359da720040 "$manifest"
check fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e "$checkpoint"
check 2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d "$root/framework/dataset/scannetv2.py"
check 018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d \
    /data3/songcl/data/data_cluster/scanrefer/ScanRefer_train_new.json
check e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08 \
    /data3/songcl/data/data_cluster/scanrefer/scene_graphs_new_train.json

gpu_uuid=$(nvidia-smi -i 7 --query-gpu=uuid --format=csv,noheader)
gpu_used=$(nvidia-smi -i 7 --query-gpu=memory.used --format=csv,noheader,nounits)
if (( gpu_used > 1024 )); then
    printf 'gpu7_not_idle %s MiB\n' "$gpu_used" > "$run/status"
    exit 1
fi
source /data3/songcl/miniconda3/etc/profile.d/conda.sh
conda activate project_cluster
export CUDA_VISIBLE_DEVICES=7
export PYTHONPATH="$root/scripts${PYTHONPATH:+:$PYTHONPATH}"
printf 'running %s\n' "$(date -Is)" > "$run/status"
python "$script" --root "$root" --checkpoint "$checkpoint" \
    --manifest "$manifest" --output "$run/result.json" --replay \
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
        printf 'foreign_gpu7_process %s; terminating own PID %s\n' "$foreign" "$child" > "$run/status"
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
