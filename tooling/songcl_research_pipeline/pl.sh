#!/usr/bin/env bash
# pl.sh — 研究流水线统一操作入口（跨项目：推送/训练/恢复/日志/终止/拉取/状态）
# 用法: bash pl.sh <project> <action> [args...]
#
#   action        转发到项目 scripts/ 下的脚本            参数
#   ----------    ------------------------------------    -----------------------------
#   sync          sync.sh                                  <server>
#   sync_model    sync_model.sh                            <server> ...
#   train         remote_train.sh                          <server> <config> [gpu_ids] [num_gpus]
#   resume        remote_resume.sh                         <server> <config> <gpu_ids> [checkpoint]
#   log           remote_log.sh                            <server> [config]
#   kill          remote_kill.sh                           <server> [config]
#   pull          remote_pull.sh                           <server> [more]
#   status        remote_status.sh                         <server>
#
# 白名单守卫: train/resume 的目标卡必须在该项目 SERVERS.yaml 的 allowed_gpus 内，
#             越界直接拒绝（FORCE=1 可强制越过，慎用）。
set -u

PROJECT=${1:-}
ACTION=${2:-}
ROOT="${PROJECT_ROOT:-/home/songcl/3dres/project}"
if [ -z "$PROJECT" ] || [ -z "$ACTION" ]; then
  sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
  echo "可用项目:"
  for d in $ROOT/*/SERVERS.yaml; do echo "  $(basename $(dirname $d))"; done
  exit 1
fi
shift 2

PROJECT_DIR=$ROOT/$PROJECT
if [ ! -d "$PROJECT_DIR/scripts" ]; then
  echo "错误: $PROJECT_DIR/scripts 不存在"
  exit 1
fi

case "$ACTION" in
  sync)       SCRIPT=sync.sh ;;
  sync_model) SCRIPT=sync_model.sh ;;
  train)      SCRIPT=remote_train.sh ;;
  resume)     SCRIPT=remote_resume.sh ;;
  log)        SCRIPT=remote_log.sh ;;
  kill)       SCRIPT=remote_kill.sh ;;
  pull)       SCRIPT=remote_pull.sh ;;
  status)     SCRIPT=remote_status.sh ;;
  *) echo "未知 action: $ACTION (sync|sync_model|train|resume|log|kill|pull|status)"; exit 1 ;;
esac

# --- 白名单守卫: train/resume ---
if [ "$ACTION" = "train" ] || [ "$ACTION" = "resume" ]; then
  SERVER=${1:-}
  GPUS=${3:-0}
  if [ -n "$SERVER" ] && [ "${FORCE:-0}" != "1" ]; then
    VIOL=$(python -c "
import yaml, sys
d = yaml.safe_load(open('$PROJECT_DIR/SERVERS.yaml'))
c = d.get('servers', {}).get('$SERVER', {})
ag = c.get('allowed_gpus', None)
if ag is None: sys.exit(0)                      # 未配置 = 不限制
allowed = {str(g) for g in ag}
asked = {g.strip() for g in '$GPUS'.split(',') if g.strip()}
bad = sorted(asked - allowed)
if not allowed:
    print(f'$SERVER 整台被本项目白名单排除 (allowed_gpus=[])')
elif bad:
    print(f\"卡 {','.join(bad)} 不在 $SERVER 白名单 {sorted(allowed)} 内\")
" 2>/dev/null)
    if [ -n "$VIOL" ]; then
      echo "[白名单拒绝] $PROJECT: $VIOL"
      echo "  如确需越界执行: FORCE=1 bash pl.sh $PROJECT $ACTION ..."
      exit 2
    fi
  fi
fi

cd "$PROJECT_DIR"
exec bash "scripts/$SCRIPT" "$@"
