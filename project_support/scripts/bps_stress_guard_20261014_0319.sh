#!/usr/bin/env bash
set -euo pipefail
test "$#" -eq 1
token="$1"
test "$token" = 1d59938f077948578e91e2cf34fc9d53
exec 9>/tmp/cluster_project_gpu7_slot2_diagnostic.lock
flock -n 9
exec 8>/tmp/cluster_project_gpu7_diagnostic.lock
flock -n 8
test "$(hostname)" = das
test "$(nvidia-smi -i 7 --query-gpu=uuid --format=csv,noheader)" = GPU-7b284db0-8d77-1b8d-e89a-15a4af73de2a
free="$(nvidia-smi -i 7 --query-gpu=memory.free --format=csv,noheader,nounits | tr -d ' ')"
test "$free" -ge 32768
pipe=/data3/songcl/Project/Cluster_project/pipeline
log="$pipe/bps_stress_${token}.log"
test ! -e "$log"
set -o noclobber
date -Iseconds > "$log"
nvidia-smi -i 7 --query-compute-apps=pid,process_name,used_memory --format=csv,noheader >> "$log"
export CUDA_VISIBLE_DEVICES=7 PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
cd /data3/songcl/Project/Cluster_project/Cluster_checkpoints
set +e
timeout --signal=TERM --kill-after=20 360 /data3/songcl/miniconda3/envs/project_cluster/bin/python -u "$pipe/bps_stress_20261014_0319.py" --token "$token" >> "$log" 2>&1
rc=$?
set -e
printf 'RUN_EXIT=%s\n' "$rc" >> "$log"
date -Iseconds >> "$log"
nvidia-smi -i 7 --query-compute-apps=pid,process_name,used_memory --format=csv,noheader >> "$log"
tail -n 7 "$log"
exit "$rc"
