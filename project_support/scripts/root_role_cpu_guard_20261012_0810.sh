#!/usr/bin/env bash
set -euo pipefail
test "$(hostname)" = das
source /data3/songcl/miniconda3/etc/profile.d/conda.sh
conda activate project_cluster
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
timeout --signal=TERM --kill-after=20 360 python \
  /data3/songcl/Project/Cluster_project/pipeline/root_role_audit_20261012_0810.py
