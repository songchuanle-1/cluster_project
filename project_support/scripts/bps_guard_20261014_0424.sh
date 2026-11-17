#!/usr/bin/env bash
set -euo pipefail
test "$#" -eq 2
mode="$1"
token="$2"
test "$token" = c9de23ffb1804f1eaa81cf54b94b9d6a
exec 9>/tmp/cluster_project_gpu7_slot2_diagnostic.lock
flock -n 9
exec 8>/tmp/cluster_project_gpu7_diagnostic.lock
flock -n 8
test "$(hostname)" = das
test "$(nvidia-smi -i 7 --query-gpu=uuid --format=csv,noheader)" = GPU-7b284db0-8d77-1b8d-e89a-15a4af73de2a
free="$(nvidia-smi -i 7 --query-gpu=memory.free --format=csv,noheader,nounits | tr -d ' ')"
test "$free" -ge 32768
case "$mode" in
  controls) script=bps_controls_20261014_0424.py; limit=180 ;;
  controls_opt) script=bps_controls_opt_20261014_0424.py; limit=180 ;;
  profile) script=bps_profile_20261014_0424.py; limit=360 ;;
  compare) script=bps_compare_20261014_0424.py; limit=240 ;;
  native) script=bps_native_20261014_0424.py; limit=360 ;;
  geometry) script=bps_geometry_20261014_0424.py; limit=180 ;;
  resources) script=bps_train_cost_20261014_0424.py; limit=240 ;;
  *) exit 2 ;;
esac
pipe=/data3/songcl/Project/Cluster_project/pipeline
log="$pipe/bps_${mode}_${token}.log"
test ! -e "$log"
set -o noclobber
date -Iseconds > "$log"
nvidia-smi -i 7 --query-compute-apps=pid,process_name,used_memory --format=csv,noheader >> "$log"
export CUDA_VISIBLE_DEVICES=7 PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
cd /data3/songcl/Project/Cluster_project/Cluster_checkpoints
set +e
timeout --signal=TERM --kill-after=20 "$limit" /data3/songcl/miniconda3/envs/project_cluster/bin/python -u "$pipe/$script" --token "$token" >> "$log" 2>&1
rc=$?
set -e
printf 'RUN_EXIT=%s\n' "$rc" >> "$log"
date -Iseconds >> "$log"
nvidia-smi -i 7 --query-compute-apps=pid,process_name,used_memory --format=csv,noheader >> "$log"
tail -n 8 "$log"
exit "$rc"
