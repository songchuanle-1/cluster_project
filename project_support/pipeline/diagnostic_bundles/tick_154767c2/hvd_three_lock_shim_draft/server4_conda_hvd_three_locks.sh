#!/usr/bin/env bash
# Separate HVD-only draft; legacy shim is sourced unchanged.
source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh || return "$?"
_hvd_gpu0_locked_exec() {
    local _hvd_python="$1"
    shift
    exec /usr/bin/flock --no-fork -n /tmp/cluster_project_gpu0_training.lock \
         /usr/bin/flock --no-fork -n /tmp/cluster_project_gpu0_diagnostic.lock \
         /usr/bin/flock --no-fork -n /tmp/cluster_project_gpu0_exclusive.lock \
         "$_hvd_python" "$@"
}
python() {
    if [[ "$PWD" == '/data/songcl/Project/Cluster_project/Cluster_hvd_20261106' && "$#" -ge 4 && "$1" == 'tools/train.py' && "$2" == 'configs/Quard/ctf_hcg_csort_hvd/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hvd.yaml' && "$3" == '--gpu_ids' && "$4" == '0' ]]; then
        [[ -n "${CONDA_PREFIX:-}" && -x "$CONDA_PREFIX/bin/python" ]] || return 126
        [[ -x /usr/bin/flock ]] || return 126
        _hvd_gpu0_locked_exec "$CONDA_PREFIX/bin/python" "$@"
    else
        command python "$@"
    fi
}
