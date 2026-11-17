#!/usr/bin/env bash
# 通用研究流水线监控 — 薄包装，逻辑统一在 pipeline_monitor.py (v2)
# 用法: bash pipeline_monitor.sh <project_name> [server]
# 环境变量: PATIENCE=N 覆盖早停 patience（默认读队列文件，再默认 10）
set -u

PROJECT=${1:-}
if [ -z "$PROJECT" ]; then
  echo "用法: $0 <project_name> [server]"
  echo "可用项目:"
  for d in ${PROJECT_ROOT:-/home/songcl/3dres/project}/*/SERVERS.yaml; do
    echo "  $(basename $(dirname $d))"
  done
  exit 1
fi

SKILL_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ARGS=("$PROJECT")
[ -n "${2:-}" ] && ARGS+=(--server "$2")
[ -n "${PATIENCE:-}" ] && ARGS+=(--patience "$PATIENCE")

exec python "$SKILL_DIR/pipeline_monitor.py" "${ARGS[@]}"
