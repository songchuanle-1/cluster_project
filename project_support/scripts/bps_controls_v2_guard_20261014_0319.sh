#!/usr/bin/env bash
set -euo pipefail
test "$#" -eq 2
mode="$1"
token="$2"
test "$token" = 1d59938f077948578e91e2cf34fc9d53
test "$(hostname)" = das
pipe=/data3/songcl/Project/Cluster_project/pipeline
test -d /data3/songcl/Project/Cluster_project/Cluster
test -d /data3/songcl/data/data_cluster/scanrefer
python=/data3/songcl/miniconda3/envs/project_cluster/bin/python
test -x "$python"
case "$mode" in
  catalog) script=bps_catalog_20261014_0319.py; visible=""; limit=300 ;;
  native) script=bps_native_20261014_0319.py; visible=7; limit=600 ;;
  controls_v2) script=bps_controls_v2_20261014_0319.py; visible=7; limit=600 ;;
  *) exit 2 ;;
esac
if test "$visible" = 7; then
  exec 9>/tmp/cluster_project_gpu7_slot2_diagnostic.lock
  flock -n 9
  exec 8>/tmp/cluster_project_gpu7_diagnostic.lock
  flock -n 8
  test "$(nvidia-smi -i 7 --query-gpu=uuid --format=csv,noheader)" = GPU-7b284db0-8d77-1b8d-e89a-15a4af73de2a
  free="$(nvidia-smi -i 7 --query-gpu=memory.free --format=csv,noheader,nounits | tr -d ' ')"
  test "$free" -ge 32768
fi
log="$pipe/bps_${mode}_${token}.log"
test ! -e "$log"
set -o noclobber
date -Iseconds > "$log"
if test "$visible" = 7; then
  nvidia-smi -i 7 --query-gpu=uuid,memory.used,memory.free,memory.total --format=csv,noheader >> "$log"
  nvidia-smi -i 7 --query-compute-apps=pid,process_name,used_memory --format=csv,noheader >> "$log"
fi
cd /data3/songcl/Project/Cluster_project/Cluster_checkpoints
export CUDA_VISIBLE_DEVICES="$visible" PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
set +e
timeout --signal=TERM --kill-after=20 "$limit" "$python" -u "$pipe/$script" --token "$token" >> "$log" 2>&1
rc=$?
set -e
printf 'RUN_EXIT=%s\n' "$rc" >> "$log"
date -Iseconds >> "$log"
if test "$visible" = 7; then
  nvidia-smi -i 7 --query-compute-apps=pid,process_name,used_memory --format=csv,noheader >> "$log"
fi
tail -n 12 "$log"
exit "$rc"
