#!/usr/bin/env bash
# 轻量早停监控 — 薄包装，仅早停检查（不推队列/不做终态归档）
# 用法: bash earlystop_monitor.sh <project_name> [server]
set -u

PROJECT=${1:?Usage: $0 <project_name> [server]}
SKILL_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ARGS=("$PROJECT" --earlystop-only)
[ -n "${2:-}" ] && ARGS+=(--server "$2")
[ -n "${PATIENCE:-}" ] && ARGS+=(--patience "$PATIENCE")

exec python "$SKILL_DIR/pipeline_monitor.py" "${ARGS[@]}"
