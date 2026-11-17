#!/usr/bin/env bash
# headless_tick.sh <project> — 系统 crontab 驱动的无头 tick, 与交互会话完全解耦
# 安装 (crontab -e): 分钟位错峰，crontab -l | grep headless 查当前占用后取 max+5
#   示例: 3 * * * *  ... headless_tick.sh <project>
# 日志: <project>/pipeline/headless/tick_<ts>.log (保留48h); 并发防重: flock(或 mkdir 原子锁); 健康检查: .tick_unhealthy
set -u
PROJECT="${1:?usage: headless_tick.sh <project>}"
# 跨平台根路径: Windows 上可用环境变量 PROJECT_ROOT 覆盖 (如 C:/3dres/project)
ROOT="${PROJECT_ROOT:-/home/songcl/3dres/project}"
SKILL=$ROOT/.claude/skills/songcl_research_pipeline
LOGDIR=$ROOT/$PROJECT/pipeline/headless
mkdir -p "$LOGDIR"
TS=$(date +%Y%m%d-%H%M%S)
LOG=$LOGDIR/tick_${TS}.log
LOCK=$LOGDIR/.tick.lock
LOCKDIR=$LOGDIR/.tick.lockdir
CODEX_RUNNER="$SKILL/codex_tick_exec.sh"
CONTEXT_BUILDER="$SKILL/build_tick_context.py"
STEADY_REPORTER="$SKILL/render_steady_report.py"

PROMPT=$(cat << PROMPTEOF
【自主研究流水线 — ${PROJECT} — 无头 cron 执行，全自动，不等待用户输入，不主动发起交互请求】

执行:
0. 先读 ${LOGDIR}/.tick_context.json。monitor/check_goal 已在 Codex 外执行一次，禁止重复运行。
1. 按 context mode 和 bounded manifest 工作，禁止扫描完整历史目录或旧 tick 日志。
2. 生成完整六段报告（0 Goal / 1 GPU / 2 Running / 3 Queue / 4 Actions / 5 Decisions），删除24小时前旧 summary。
3. event 模式只处理列出的终态、crash或状态变化；需要写分析时才读 formats.md 对应章节。
4. design 模式才读 autonomous_design.md 和设计模板；从 tick context 读取 queue.candidate_budget，以该数量为目标设计结构独立候选。若通过科学准入的候选不足，则少入队并记录淘汰原因。校验 goal constraints/banned 后完成设计、实现、测试、入队和同步；禁止用纯调参、seed 重复、纯消融、禁用/失败路线、改名重复或占位变体凑容量。
5. steady 模式不做全历史研究审查；无变化监控不重复记录 other 决策。
6. 禁止与用户交互，新问题落 decision 后继续。
PROMPTEOF
)
PROMPT_FILE="$LOGDIR/.tick_prompt_$$.txt"
printf '%s\n' "$PROMPT" > "$PROMPT_FILE"

{
  # 并发防重: 优先 flock(Linux); Git Bash(Windows) 无 flock → mkdir 原子锁
  if command -v flock >/dev/null 2>&1; then
    flock -n 9 || { echo "$(date '+%F %T') previous tick still running, skip" >> "$LOG"; exit 0; }
  else
    if ! mkdir "$LOCKDIR" 2>/dev/null; then
      # mkdir 锁残留自愈: 锁目录存在超 2h 视为上次 tick 进程被杀残留, 清掉重试
      if [ -d "$LOCKDIR" ] && [ "$(find "$LOCKDIR" -maxdepth 0 -mmin +120 2>/dev/null)" != "" ]; then
        rmdir "$LOCKDIR" 2>/dev/null || true
        echo "$(date '+%F %T') stale mkdir lock cleared" >> "$LOG"
      fi
      if ! mkdir "$LOCKDIR" 2>/dev/null; then
        echo "$(date '+%F %T') previous tick still running, skip" >> "$LOG"; exit 0
      fi
    fi
    LOCKED_BY_MKDIR=1
  fi
  cd "$ROOT"

  # 预检: 连续不健康 ≥3 次 → 退出避免烧 token（API 可能持续故障）
  UNHEALTHY_COUNT=$(cat "$LOGDIR/.tick_unhealthy_count" 2>/dev/null || echo 0)
  if [ "$UNHEALTHY_COUNT" -ge 3 ]; then
    echo "=== BAILING @ $(date '+%F %T'): $UNHEALTHY_COUNT consecutive unhealthy ticks, API likely down ===" >> "$LOG"
    echo "需要人工检查 API 状态后删除 $LOGDIR/.tick_unhealthy_count 恢复流水线" >> "$LOG"
    exit 0
  fi

  echo "=== headless tick $PROJECT start @ $(date '+%F %T') ===" >> "$LOG"
  MONITOR_OUT="$LOGDIR/.monitor_preflight_$$.txt"
  GOAL_OUT="$LOGDIR/.goal_preflight_$$.txt"
  PROJECT_ROOT="$ROOT" python "$SKILL/pipeline_monitor.py" "$PROJECT" > "$MONITOR_OUT" 2>&1
  MONITOR_RC=$?
  PROJECT_ROOT="$ROOT" python "$SKILL/check_goal.py" "$PROJECT" > "$GOAL_OUT" 2>&1
  GOAL_RC=$?
  cat "$MONITOR_OUT" "$GOAL_OUT" >> "$LOG"
  PROJECT_ROOT="$ROOT" python "$CONTEXT_BUILDER" "$PROJECT" \
    --monitor-file "$MONITOR_OUT" --goal-file "$GOAL_OUT" \
    --monitor-rc "$MONITOR_RC" --goal-rc "$GOAL_RC" >> "$LOG" 2>&1
  CONTEXT_RC=$?
  TICK_MODE=""
  if [ "$CONTEXT_RC" -eq 0 ]; then
    TICK_MODE=$(PROJECT_ROOT="$ROOT" python -c "import json; print(json.load(open(r'$LOGDIR/.tick_context.json', encoding='utf-8'))['mode'])" 2>> "$LOG")
  fi
  if [ "$CONTEXT_RC" -ne 0 ]; then
    echo "=== context unavailable; skip codex ===" >> "$LOG"
    RC="$CONTEXT_RC"
  elif [ "$TICK_MODE" = "steady" ]; then
    echo "=== steady mode: deterministic report, codex skipped ===" >> "$LOG"
    PROJECT_ROOT="$ROOT" python "$STEADY_REPORTER" "$PROJECT" >> "$LOG" 2>&1
    RC=$?
  else
    echo "=== context mode=${TICK_MODE:-unknown}: starting codex ===" >> "$LOG"
    PROJECT_ROOT="$ROOT" bash "$CODEX_RUNNER" "$PROJECT" "$PROMPT_FILE" "$LOG" 1500
    RC=$?
  fi
  echo "=== exit=$RC @ $(date '+%F %T') ===" >> "$LOG"
  # 健康检查: tick 是否真正完成了工作 (必须有 Tick # 标记才算有效执行)
  if [ "$RC" -ne 0 ] || ! grep -q "Tick #" "$LOG" 2>/dev/null; then
    NEW_COUNT=$((UNHEALTHY_COUNT + 1))
    echo "=== UNHEALTHY (#$NEW_COUNT): exit=$RC, no Tick# marker — Codex may have failed or output truncated ===" >> "$LOG"
    touch "$LOGDIR/.tick_unhealthy"
    echo "$NEW_COUNT" > "$LOGDIR/.tick_unhealthy_count"
  else
    if [ -f "$LOGDIR/.tick_context_state.next.json" ]; then
      mv -f "$LOGDIR/.tick_context_state.next.json" "$LOGDIR/.tick_context_state.json"
    fi
    rm -f "$LOGDIR/.tick_unhealthy" "$LOGDIR/.tick_unhealthy_count"
  fi
  [ "$RC" -eq 0 ] || rm -f "$LOGDIR/.tick_context_state.next.json"
} 9>"$LOCK"

# mkdir 锁释放 (flock 随 fd 关闭自动释放, 无需处理)
[ -n "${LOCKED_BY_MKDIR:-}" ] && rmdir "$LOCKDIR" 2>/dev/null || true
rm -f "$PROMPT_FILE" "${MONITOR_OUT:-}" "${GOAL_OUT:-}"

# 清理 48h 前旧日志
find "$LOGDIR" -maxdepth 1 -name 'tick_*.log' -mmin +2880 -delete 2>/dev/null
exit 0
