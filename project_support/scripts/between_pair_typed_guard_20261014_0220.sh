#!/usr/bin/env bash
set -euo pipefail
test "$#" -eq 1
token="$1"
test "$token" = 66fa1e81aec94d5eb10265ea533669ac
test "$(hostname)" = das
pipe=/data3/songcl/Project/Cluster_project/pipeline
log="$pipe/between_pair_typed_${token}.log"
test ! -e "$log"
set -o noclobber
date -Iseconds > "$log"
cd /data3/songcl/Project/Cluster_project/Cluster_checkpoints
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
set +e
timeout --signal=TERM --kill-after=20 300 \
  /data3/songcl/miniconda3/envs/project_cluster/bin/python -u \
  "$pipe/between_pair_typed_20261014_0220.py" --token "$token" >> "$log" 2>&1
rc=$?
set -e
{
  printf 'RUN_EXIT=%s\n' "$rc"
  date -Iseconds
} >> "$log"
tail -n 12 "$log"
exit "$rc"
