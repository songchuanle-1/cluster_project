#!/usr/bin/env bash
set -euo pipefail
test "$#" -eq 1
token="$1"
test "$token" = 1d59938f077948578e91e2cf34fc9d53
test "$(hostname)" = das
pipe=/data3/songcl/Project/Cluster_project/pipeline
log="$pipe/bps_population_${token}.log"
test ! -e "$log"
set -o noclobber
date -Iseconds > "$log"
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
set +e
timeout --signal=TERM --kill-after=20 600 /data3/songcl/miniconda3/envs/project_cluster/bin/python -u "$pipe/bps_population_20261014_0319.py" --token "$token" >> "$log" 2>&1
rc=$?
set -e
printf 'RUN_EXIT=%s\n' "$rc" >> "$log"
date -Iseconds >> "$log"
tail -n 7 "$log"
exit "$rc"
