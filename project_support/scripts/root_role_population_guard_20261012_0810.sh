#!/usr/bin/env bash
set -euo pipefail
test "$(hostname)" = das
source /data3/songcl/miniconda3/etc/profile.d/conda.sh
conda activate project_cluster
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
root=/data3/songcl/Project/Cluster_project/Cluster
export PYTHONPATH="$root/scripts:$root:$root/framework/lib"
timeout --signal=TERM --kill-after=10 240 python \
  /data3/songcl/Project/Cluster_project/pipeline/root_role_population_contract_20261012_0810.py
