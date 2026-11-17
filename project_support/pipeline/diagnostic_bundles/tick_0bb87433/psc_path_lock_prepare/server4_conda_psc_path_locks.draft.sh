#!/usr/bin/env bash
# DRAFT: target root and stage are prospective and are not claimed deployed.
# Replace the placeholder only in a separately frozen/reviewed activation copy.
_psc_base='/data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh'
_psc_bin='/data/songcl/Project/Cluster_project/pipeline/runtime/psc_path_lock_0bb87433/bin'
_psc_entry_sha='DRAFT_REPLACE_WITH_FINAL_REVIEWED_PRODUCTION_EXECUTABLE_SHA256'
[[ -f "$_psc_base" ]] || return 126
read -r _psc_base_actual _ < <(/usr/bin/sha256sum -- "$_psc_base")
[[ "$_psc_base_actual" == '6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0' ]] || return 126
source "$_psc_base" || return "$?"
declare -F __conda_activate >/dev/null || return 126
[[ "$_psc_entry_sha" != DRAFT_* ]] || return 126
[[ -x "$_psc_bin/python" && ! -L "$_psc_bin/python" ]] || return 126
read -r _psc_entry_actual _ < <(/usr/bin/sha256sum -- "$_psc_bin/python")
[[ "$_psc_entry_actual" == "$_psc_entry_sha" ]] || return 126

_psc_prepend_python() {
    [[ "${CONDA_PREFIX:-}" == '/home/songcl/.conda/envs/project_cluster' ]] || return 126
    # Shell functions cannot intercept Python. Popen uses this real PATH file.
    unset -f python 2>/dev/null || return 126
    unalias python 2>/dev/null || :
    export PATH="$_psc_bin:$PATH"
    hash -r
    [[ "$(type -P python)" == "$_psc_bin/python" ]] || return 126
    [[ "$(type -t python)" == file ]] || return 126
}

# This conda_source is scoped to canonical "conda activate project_cluster".
# Calling the original activation helper changes THIS shell, then restores the
# executable prefix, so a conda activation cannot bury it behind env/bin.
conda() {
    [[ "$#" == 2 && "$1" == activate && "$2" == project_cluster ]] || return 126
    __conda_activate "$@" || return "$?"
    _psc_prepend_python
}

# Do not activate or run Python merely by sourcing this draft. The canonical
# command performs its usual explicit conda activation immediately afterwards.
return 0
