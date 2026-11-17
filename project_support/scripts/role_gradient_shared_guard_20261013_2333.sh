#!/usr/bin/env bash
set -euo pipefail
test "$#" -eq 1
token="$1"
test "$token" = 3b60320eabb148289911c480f7649b8c
exec 9>/tmp/cluster_project_gpu7_slot2_diagnostic.lock
flock -n 9
exec 8>/tmp/cluster_project_gpu7_diagnostic.lock
flock -n 8
test "$(hostname)" = das
uuid=GPU-7b284db0-8d77-1b8d-e89a-15a4af73de2a
test "$(nvidia-smi -i 7 --query-gpu=uuid --format=csv,noheader)" = "$uuid"
free="$(nvidia-smi -i 7 --query-gpu=memory.free --format=csv,noheader,nounits | tr -d ' ')"
test "$free" -ge 32768
pipe=/data3/songcl/Project/Cluster_project/pipeline
script="$pipe/role_gradient_native_20261013_1012.py"
test "$(sha256sum "$script" | cut -d ' ' -f 1)" = d01eab84334844e45c83b9aa0af437848a255203e4aeaf32e72c146ce220c7a0
test ! -e "$pipe/role_gradient_native_20261013_1012.json"
test ! -e "$pipe/role_gradient_native_20261013_1012.progress.jsonl"
log="$pipe/role_shared_${token}.log"
test ! -e "$log"
set -o noclobber
{
  date -Iseconds
  nvidia-smi -i 7 --query-gpu=uuid,utilization.gpu,memory.used,memory.free,memory.total --format=csv,noheader
  nvidia-smi -i 7 --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
} > "$log"
cd /data3/songcl/Project/Cluster_project/Cluster_checkpoints
export CUDA_VISIBLE_DEVICES=7 PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
set +e
timeout --signal=TERM --kill-after=20 600 \
  /data3/songcl/miniconda3/envs/project_cluster/bin/python -u \
  "$script" --token "$token" >> "$log" 2>&1
rc=$?
set -e
{
  printf 'RUN_EXIT=%s\n' "$rc"
  date -Iseconds
  nvidia-smi -i 7 --query-gpu=uuid,utilization.gpu,memory.used,memory.free,memory.total --format=csv,noheader
  nvidia-smi -i 7 --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
} >> "$log"
printf 'RUN_EXIT=%s LOG=%s\n' "$rc" "$log"
tail -n 8 "$log"
exit "$rc"
