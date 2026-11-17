#!/usr/bin/env bash
set -euo pipefail
test "$#" -eq 4
token="$1"
mode="$2"
target="$3"
input_case="$4"
test "$token" = c9de23ffb1804f1eaa81cf54b94b9d6a
case "$target" in baseline|champion|candidate) ;; *) exit 2 ;; esac
exec 9>/tmp/cluster_project_gpu7_slot2_diagnostic.lock
flock -n 9
exec 8>/tmp/cluster_project_gpu7_diagnostic.lock
flock -n 8
test "$(hostname)" = das
test "$(nvidia-smi -i 7 --query-gpu=uuid --format=csv,noheader)" = GPU-7b284db0-8d77-1b8d-e89a-15a4af73de2a
free="$(nvidia-smi -i 7 --query-gpu=memory.free --format=csv,noheader,nounits | tr -d ' ')"
test "$free" -ge 32768
pipe=/data3/songcl/Project/Cluster_project/pipeline
log="$pipe/bps_${mode}_${input_case}_${target}_${token}.log"
test ! -e "$log"
set -o noclobber
date -Iseconds > "$log"
nvidia-smi -i 7 --query-compute-apps=pid,process_name,used_memory --format=csv,noheader >> "$log"
export CUDA_VISIBLE_DEVICES=7 PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
cd /data3/songcl/Project/Cluster_project/Cluster_checkpoints
case "$mode" in
  predict) script=bps_predict_opt_20261014_0424.py; extra=(--target "$target") ;;
  train) script=bps_train_cost_20261014_0424.py; extra=(--target "$target" --case "$input_case") ;;
  *) exit 2 ;;
esac
set +e
timeout --signal=TERM --kill-after=20 240 /data3/songcl/miniconda3/envs/project_cluster/bin/python -u "$pipe/$script" --token "$token" "${extra[@]}" >> "$log" 2>&1
rc=$?
set -e
printf 'RUN_EXIT=%s\n' "$rc" >> "$log"
date -Iseconds >> "$log"
nvidia-smi -i 7 --query-compute-apps=pid,process_name,used_memory --format=csv,noheader >> "$log"
tail -n 5 "$log"
exit "$rc"
