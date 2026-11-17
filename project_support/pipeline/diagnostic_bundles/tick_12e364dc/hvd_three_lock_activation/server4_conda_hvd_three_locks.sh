#!/usr/bin/env bash
# Current HVD runtime only; source the original conda initialization unchanged.
source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh || return "$?"

_hvd_gpu0_locked_exec() {
    local _hvd_python="$1"
    shift
    [[ "$_hvd_python" == '/home/songcl/.conda/envs/project_cluster/bin/python' && -x "$_hvd_python" ]] || return 126
    [[ -x /usr/bin/flock ]] || return 126
    exec /usr/bin/flock --no-fork -n /tmp/cluster_project_gpu0_training.lock \
         /usr/bin/flock --no-fork -n /tmp/cluster_project_gpu0_diagnostic.lock \
         /usr/bin/flock --no-fork -n /tmp/cluster_project_gpu0_exclusive.lock \
         "$_hvd_python" "$@"
}

python() {
    local _hvd_train=0 _hvd_arg
    # CPU -c/-m/stdin/version calls remain ordinary Python calls. Script-style
    # train.py calls, including extra Python flags, cannot bypass the strict route.
    for _hvd_arg in "$@"; do
        case "$_hvd_arg" in
            -c|-m|-|--version|-V) break ;;
            tools/train.py|./tools/train.py|*/tools/train.py) _hvd_train=1; break ;;
        esac
    done
    if [[ "$PWD" == '/data/songcl/Project/Cluster_project/Cluster_hvd_20261106' && "$_hvd_train" == 1 ]]; then
        if [[ "$#" == 6 && "$1" == 'tools/train.py' \
              && "$2" == 'configs/Quard/ctf_hcg_csort_hvd/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hvd.yaml' \
              && "$3" == '--gpu_ids' && "$4" == '0' \
              && "$5" == '--num_gpus' && "$6" == '1' ]]; then
            [[ "${CONDA_PREFIX:-}" == '/home/songcl/.conda/envs/project_cluster' ]] || return 126
            _hvd_gpu0_locked_exec "$CONDA_PREFIX/bin/python" "$@"
        else
            return 126
        fi
    else
        command python "$@"
    fi
}
