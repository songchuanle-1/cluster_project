#!/usr/bin/env bash
# headless_tick_local.sh <project> — Windows local tick via Task Scheduler
# Full pipeline: monitor + Codex design + reports (same as Linux crontab)
set -u
PROJECT="${1:?usage: headless_tick_local.sh <project>}"
ROOT="${PROJECT_ROOT:-D:/project}"
SKILL="$ROOT/.claude/skills/songcl_research_pipeline"
LOGDIR="$ROOT/$PROJECT/pipeline/headless"
mkdir -p "$LOGDIR"
TS=$(date +%Y%m%d-%H%M%S)
LOG="$LOGDIR/tick_${TS}.log"
LOCKDIR="$LOGDIR/.tick.lockdir"
CODEX_RUNNER="$SKILL/codex_tick_exec.sh"
CONTEXT_BUILDER="$SKILL/build_tick_context.py"
STEADY_REPORTER="$SKILL/render_steady_report.py"

# Generate prompt via temp file (avoids pipe encoding issues with Chinese on Windows)
PROMPT_FILE="$LOGDIR/.tick_prompt_$$.txt"
cat > "$PROMPT_FILE" << 'PROMPTEOF'
[Autonomous Research Pipeline — PROJECT_PLACEHOLDER — headless cron execution, fully autonomous, no user interaction]

Environment: Windows, PROJECT_ROOT=ROOT_PLACEHOLDER, use "python" (not python3)

Execution:
0. Read LOGDIR_PLACEHOLDER/.tick_context.json first. Monitor and goal checks have already run exactly once; do not run them again.
1. Follow its mode and bounded manifests. Do not scan whole history directories or old tick logs.
2. Generate the normal six-section report to pipeline/reports/summary_<ts>.md. The required headings are:
   0 Goal Status, 1 GPU Overview, 2 Running Experiments, 3 Queue Status,
   4 This Tick's Actions, 5 Decisions Made. Delete summaries older than 24h.
3. On event mode, handle only listed terminal/crash/state changes. Read the relevant section of formats.md only when creating a new terminal analysis or bugfix.
4. On design mode only, read references/autonomous_design.md and the relevant templates. Read queue.candidate_budget from the tick context and aim to create that many scientifically admissible, structurally distinct variants. Enqueue fewer when fewer candidates pass the gates, and document the rejected remainder. Validate all goal constraints/bans, then perform motivation_review → exp_design → implementation/tests → enqueue → sync. Never add tuning-only, seed-repeat, pure-ablation, banned, failed-route, renamed-duplicate, or placeholder variants merely to fill capacity.
5. On steady mode, do not perform broad research review. No-change monitoring does not require a new decision log.
6. Log actual decisions with log_decision.sh. List pending questions from the snapshot manifest.
7. Do NOT interact with user. Record new questions and continue.
8. If pipeline/closure_policy.json enables closure, read references/closure.md.
   Resume research_work.due_ids in event mode before new design. Persist each
   candidate stage, hashed evidence and concrete next_action in research_work.json.
   A plan alone is not completion. Use admission receipts and the safe monitor
   dispatch path; verify training progress, not just PID. Explicitly reject
   failed candidates or record external blockers with retry/unblock conditions.

Start by outputting "Tick #" marker, then execute all steps.
PROMPTEOF

# Substitute placeholders
sed -i "s|PROJECT_PLACEHOLDER|$PROJECT|g; s|ROOT_PLACEHOLDER|$ROOT|g; s|SKILL_DIR|$SKILL|g; s|LOGDIR_PLACEHOLDER|$LOGDIR|g" "$PROMPT_FILE"

{
  # mkdir atomic lock
  if ! mkdir "$LOCKDIR" 2>/dev/null; then
    if [ -d "$LOCKDIR" ] && [ "$(find "$LOCKDIR" -maxdepth 0 -mmin +120 2>/dev/null)" != "" ]; then
      rmdir "$LOCKDIR" 2>/dev/null || true
      echo "$(date '+%F %T') stale lock cleared" >> "$LOG"
    fi
    if ! mkdir "$LOCKDIR" 2>/dev/null; then
      echo "$(date '+%F %T') previous tick still running, skip" >> "$LOG"
      rm -f "$PROMPT_FILE"
      exit 0
    fi
  fi
  cd "$ROOT"

  UNHEALTHY_COUNT=$(cat "$LOGDIR/.tick_unhealthy_count" 2>/dev/null || echo 0)
  if ! [[ "$UNHEALTHY_COUNT" =~ ^[0-9]+$ ]]; then
    UNHEALTHY_COUNT=0
  fi
  if [ "$UNHEALTHY_COUNT" -ge 3 ]; then
    echo "=== Codex unhealthy for $UNHEALTHY_COUNT ticks; running recovery reconciliation ===" >> "$LOG"
  fi

  echo "=== tick $PROJECT start $(date '+%F %T') ===" >> "$LOG"
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
  if [ "$CONTEXT_RC" -ne 0 ]; then
    echo "=== context builder failed rc=$CONTEXT_RC ===" >> "$LOG"
  fi
  TICK_MODE=""
  if [ "$CONTEXT_RC" -eq 0 ]; then
    TICK_MODE=$(PROJECT_ROOT="$ROOT" python -c "import json; print(json.load(open(r'$LOGDIR/.tick_context.json', encoding='utf-8'))['mode'])" 2>> "$LOG")
  fi
  if [ "$CONTEXT_RC" -ne 0 ]; then
    echo "=== context unavailable; skip codex and enter recovery path ===" >> "$LOG"
    RC="$CONTEXT_RC"
  elif [ "$TICK_MODE" = "steady" ]; then
    echo "=== steady mode: generating deterministic report; codex skipped ===" >> "$LOG"
    PROJECT_ROOT="$ROOT" python "$STEADY_REPORTER" "$PROJECT" >> "$LOG" 2>&1
    RC=$?
  else
    echo "=== context mode=${TICK_MODE:-unknown}: starting codex ===" >> "$LOG"
    PROJECT_ROOT="$ROOT" bash "$CODEX_RUNNER" "$PROJECT" "$PROMPT_FILE" "$LOG" 3600
    RC=$?
  fi
  if [ "$RC" -eq 0 ]; then
    PROJECT_ROOT="$ROOT" python "$SKILL/closure.py" "$PROJECT" >> "$LOG" 2>&1
    RC=$?
  fi
  echo "=== exit=$RC $(date '+%F %T') ===" >> "$LOG"

  # Codex quota/rate-limit failures must not stop state maintenance. Reconcile
  # terminal queue states without early-stop, new pushes, or experiment design.
  if [ "$RC" -ne 0 ]; then
    echo "=== Codex failed; running reconcile-only fallback ===" >> "$LOG"
    PROJECT_ROOT="$ROOT" python "$SKILL/pipeline_monitor.py" "$PROJECT" \
      --reconcile-only >> "$LOG" 2>&1
    RECONCILE_RC=$?
    echo "=== reconcile-only exit=$RECONCILE_RC $(date '+%F %T') ===" >> "$LOG"
  else
    RECONCILE_RC=1
  fi

  # Health check: RC=0 (tick completed cleanly) = HEALTHY. A steady-state tick with no
  # early-stops / no queue pushes / no new designs is NORMAL, not unhealthy. Only a
  # Non-zero exit (Codex crash / timeout=124 / tool failure) counts as unhealthy.
  # (2026-08-20 fix: previously "no side effects in last 30min" was misclassified as
  # UNHEALTHY, which made every normal steady-state tick increment the counter and
  # BAIL the pipeline after 3 idle ticks.)
  if [ "$RC" -eq 0 ]; then
    if [ "$RC" -eq 0 ]; then
      echo "=== HEALTHY: tick completed (RC=0, mode=${TICK_MODE:-unknown}) ===" >> "$LOG"
      if [ -f "$LOGDIR/.tick_context_state.next.json" ]; then
        mv -f "$LOGDIR/.tick_context_state.next.json" "$LOGDIR/.tick_context_state.json"
      fi
    else
      echo "=== RECOVERED: Codex failed, reconcile-only completed ===" >> "$LOG"
    fi
    rm -f "$LOGDIR/.tick_unhealthy" "$LOGDIR/.tick_unhealthy_count"
  else
    NEW_COUNT=$((UNHEALTHY_COUNT + 1))
    echo "=== UNHEALTHY #$NEW_COUNT: exit code $RC; recovery fallback attempted ===" >> "$LOG"
    touch "$LOGDIR/.tick_unhealthy"
    echo "$NEW_COUNT" > "$LOGDIR/.tick_unhealthy_count"
  fi
  [ "$RC" -eq 0 ] || rm -f "$LOGDIR/.tick_context_state.next.json"

  rmdir "$LOCKDIR" 2>/dev/null || true
  rm -f "$PROMPT_FILE" "$MONITOR_OUT" "$GOAL_OUT"
}

find "$LOGDIR" -maxdepth 1 -name 'tick_*.log' -mmin +2880 -delete 2>/dev/null
exit "${RC:-1}"
