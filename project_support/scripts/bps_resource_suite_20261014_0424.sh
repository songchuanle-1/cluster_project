#!/usr/bin/env bash
set -euo pipefail
test "$#" -eq 1
token="$1"
test "$token" = c9de23ffb1804f1eaa81cf54b94b9d6a
guard=/data3/songcl/Project/Cluster_project/pipeline/bps_resources_guard_20261014_0424.sh
for target in baseline champion candidate; do
    bash "$guard" "$token" predict "$target" primary_repaired
done
for input_case in stress nonevent single; do
    for target in baseline champion candidate; do
        bash "$guard" "$token" train "$target" "$input_case"
    done
done
