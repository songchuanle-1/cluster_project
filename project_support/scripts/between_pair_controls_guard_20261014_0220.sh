#!/usr/bin/env bash
set -euo pipefail
test "$(hostname)" = das
pipe=/data3/songcl/Project/Cluster_project/pipeline
token=66fa1e81aec94d5eb10265ea533669ac
log="$pipe/between_pair_controls_${token}.log"
test ! -e "$log"
set -o noclobber
date -Iseconds > "$log"
cd /data3/songcl/Project/Cluster_project/Cluster_checkpoints
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
set +e
timeout --signal=TERM --kill-after=20 300 \
  /data3/songcl/miniconda3/envs/project_cluster/bin/python -u \
  "$pipe/between_pair_controls_20261014_0220.py" >> "$log" 2>&1
rc=$?
set -e
printf 'RUN_EXIT=%s\n' "$rc" >> "$log"
tail -n 8 "$log"
exit "$rc"
