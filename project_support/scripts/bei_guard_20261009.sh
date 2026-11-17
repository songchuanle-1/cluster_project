#!/usr/bin/env bash
set -euo pipefail
root=/data3/songcl/Project/Cluster_project/Cluster
exec 9>/tmp/cluster_project_gpu7_slot2_diagnostic.lock
flock -n 9 || exit 2
gpu_uuid=$(nvidia-smi -i 7 --query-gpu=uuid --format=csv,noheader)
used=$(nvidia-smi -i 7 --query-gpu=memory.used --format=csv,noheader,nounits)
(( used < 50000 )) || exit 2
while IFS=',' read -r uuid pid memory; do
    [[ "$uuid" == "$gpu_uuid" ]] || continue
    pid=${pid//[[:space:]]/}
    [[ "$pid" == "225589" ]] || { printf 'Unexpected GPU7 process %s\n' "$pid"; exit 2; }
    ps -p "$pid" -o args= | grep -Fq 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_pdc.yaml' || exit 2
done < <(nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader)
source /data3/songcl/miniconda3/etc/profile.d/conda.sh
conda activate project_cluster
export CUDA_VISIBLE_DEVICES=7 PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$root/scripts:$root:$root/framework/lib"
timeout --signal=TERM --kill-after=20 600 python "$root/scripts/validate_bei_20261009.py" \
    "$@" --root "$root"
