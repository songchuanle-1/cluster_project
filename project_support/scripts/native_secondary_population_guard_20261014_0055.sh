#!/usr/bin/env bash
set -euo pipefail
test "$#" -eq 1
token="$1"
test "$token" = f38daa9ab2914c97a74bd716613388f8
test "$(hostname)" = das
pipe=/data3/songcl/Project/Cluster_project/pipeline
log="$pipe/native_secondary_population_${token}.log"
test ! -e "$log"
set -o noclobber
date -Iseconds > "$log"
cd /data3/songcl/Project/Cluster_project/Cluster_checkpoints
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
set +e
timeout --signal=TERM --kill-after=20 600 \
  /data3/songcl/miniconda3/envs/project_cluster/bin/python -u \
  "$pipe/native_secondary_population_20261014_0050.py" --token "$token" >> "$log" 2>&1
rc=$?
set -e
{
  printf 'RUN_EXIT=%s\n' "$rc"
  date -Iseconds
} >> "$log"
printf 'RUN_EXIT=%s LOG=%s\n' "$rc" "$log"
tail -n 6 "$log"
exit "$rc"
