#!/usr/bin/env bash
# headless_tick_local.sh <project> — Windows local tick via Task Scheduler
# Full pipeline: monitor + Codex design + reports (same as Linux crontab)
set -u
PROJECT="${1:?usage: headless_tick_local.sh <project>}"
ROOT="${PROJECT_ROOT:-D:/project}"
SKILL="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LOGDIR="$ROOT/$PROJECT/pipeline/headless"
# Migrated projects are owned by their visible Codex task, even after reboot.
EXECUTION_MODE=$(python -c 'import json,pathlib,sys; p=pathlib.Path(sys.argv[1]); print(json.loads(p.read_text(encoding="utf-8")).get("mode","background") if p.exists() else "background")' "$ROOT/$PROJECT/pipeline/execution_mode.json") || exit 1
if [ "$EXECUTION_MODE" = "foreground" ]; then
  echo "Foreground-owned project; background tick skipped: $PROJECT"
  exit 0
fi
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
Run one legacy background research tick for PROJECT_PLACEHOLDER; PROJECT_ROOT=ROOT_PLACEHOLDER, use python -B.
Read SKILL_DIR/SKILL.md (legacy background mode) and relevant references only; current project goals, permissions and resources remain authoritative.
Start with LOGDIR_PLACEHOLDER/.tick_model_view.json. Preflight already ran; do not repeat it, scan history, change schedulers or invoke nested executors.
Follow mode and due IDs under the real deadline. Use closure.md for reserve preparation, bounded local revisions, admission and honest stopping; reserve_only forbids queue additions or launches.
Persist actual evidence, necessary memory and a complete Chinese six-section report. Unknown stays unknown; never fabricate PASS or reopen frozen work. The outer runner performs postflight.
For a project without enabled closure, retain its existing deployment contract; do not enable closure automatically.
PROMPTEOF

# Substitute placeholders
sed -i "s|PROJECT_PLACEHOLDER|$PROJECT|g; s|ROOT_PLACEHOLDER|$ROOT|g; s|SKILL_DIR|$SKILL|g; s|LOGDIR_PLACEHOLDER|$LOGDIR|g" "$PROMPT_FILE"

{
  # mkdir atomic lock
  if ! mkdir "$LOCKDIR" 2>/dev/null; then
    LOCK_OWNER=$(cat "$LOCKDIR/pid" 2>/dev/null || true)
    LOCK_ORPHANED=0
    if [ -n "$LOCK_OWNER" ] && ! kill -0 "$LOCK_OWNER" 2>/dev/null; then
      LOCK_ORPHANED=1
    elif [ -z "$LOCK_OWNER" ] && [ "$(find "$LOCKDIR" -maxdepth 0 -mmin +1 2>/dev/null)" != "" ]; then
      LOCK_ORPHANED=1
    elif [ "$(find "$LOCKDIR" -maxdepth 0 -mmin +120 2>/dev/null)" != "" ]; then
      LOCK_ORPHANED=1
    fi
    if [ "$LOCK_ORPHANED" -eq 1 ]; then
      rm -f "$LOCKDIR/pid"
      rmdir "$LOCKDIR" 2>/dev/null || true
      echo "$(date '+%F %T') orphaned tick lock cleared" >> "$LOG"
    fi
    if ! mkdir "$LOCKDIR" 2>/dev/null; then
      echo "$(date '+%F %T') previous tick still running, skip" >> "$LOG"
      rm -f "$PROMPT_FILE"
      exit 0
    fi
  fi
  printf '%s\n' "$$" > "$LOCKDIR/pid"
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
    TICK_DEADLINE=$(PROJECT_ROOT="$ROOT" python -c \
      "import datetime,json; p=r'$LOGDIR/.tick_context.json'; d=json.load(open(p,encoding='utf-8')); print(int(datetime.datetime.fromisoformat(d['deadline_at']).timestamp()))")
    LAST_RESEARCH_STATE=""
    while :; do
      REMAINING=$((TICK_DEADLINE - $(date +%s)))
      if [ "$REMAINING" -lt 180 ]; then
        echo "=== design deadline near: checking existing artifacts before stopping ===" >> "$LOG"
        PROJECT_ROOT="$ROOT" python "$SKILL/closure.py" "$PROJECT" >> "$LOG" 2>&1
        RC=$?
        break
      fi
      PROJECT_ROOT="$ROOT" CODEX_FRESH_THREAD="${CODEX_FRESH_THREAD:-1}" \
        bash "$CODEX_RUNNER" "$PROJECT" "$PROMPT_FILE" "$LOG" "$REMAINING"
      RC=$?
      # A crashed or timed-out model may have partial side effects. Reconcile,
      # but do not blindly replay it inside this tick.
      if [ "$RC" -eq 75 ]; then
        echo "=== active thread writer; skip without postflight or unhealthy state ===" >> "$LOG"
        break
      fi
      [ "$RC" -eq 0 ] || break
      CLOSURE_OUT="$LOGDIR/.closure_postflight_$$.txt"
      PROJECT_ROOT="$ROOT" python "$SKILL/closure.py" "$PROJECT" > "$CLOSURE_OUT" 2>&1
      RC=$?
      cat "$CLOSURE_OUT" >> "$LOG"
      if [ "$RC" -eq 0 ]; then
        rm -f "$CLOSURE_OUT"
        break
      fi
      # Only a design-capacity failure is a research continuation. Other
      # postflight failures are unhealthy and need ordinary recovery.
      if [ "$TICK_MODE" != "design" ] || ! grep -Eq \
        'Capacity gap remains|Incomplete design-cycle stop|Design-cycle stop|Capacity-gap design made no durable candidate progress' \
        "$CLOSURE_OUT"; then
        rm -f "$CLOSURE_OUT"
        break
      fi
      CURRENT_RESEARCH_STATE=$(PROJECT_ROOT="$ROOT" python -c \
        "import hashlib,pathlib; p=pathlib.Path(r'$ROOT/$PROJECT/pipeline/research_work.json'); print(hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else 'missing')")
      if [ "$CURRENT_RESEARCH_STATE" = "$LAST_RESEARCH_STATE" ]; then
        echo "=== design continuation made no research-state progress; unhealthy ===" >> "$LOG"
        rm -f "$CLOSURE_OUT"
        break
      fi
      LAST_RESEARCH_STATE="$CURRENT_RESEARCH_STATE"
      {
        printf '\n[Same-tick closure continuation]\n'
        printf 'The preceding Codex invocation ended but postflight failed:\n'
        sed -n '1,5p' "$CLOSURE_OUT"
        printf 'Continue only the failed checks and executable due work within the original deadline; follow closure.md, preserve evidence, update report/memory. No repeated closed work or weaker gates.\n'
      } >> "$PROMPT_FILE"
      echo "=== design capacity still open; continuing in same tick ===" >> "$LOG"
      rm -f "$CLOSURE_OUT"
    done
  fi
  if [ "$RC" -eq 0 ] && [ "$TICK_MODE" = "steady" ]; then
    PROJECT_ROOT="$ROOT" python "$SKILL/closure.py" "$PROJECT" >> "$LOG" 2>&1
    RC=$?
  fi
  echo "=== exit=$RC $(date '+%F %T') ===" >> "$LOG"
  if [ "$RC" -eq 75 ]; then
    # A pre-start writer conflict has no research side effects. The next
    # scheduled tick will build a fresh snapshot.
    rm -f "$LOGDIR/.tick_context_state.next.json"
    rm -f "$LOGDIR/.tick_unhealthy" "$LOGDIR/.tick_unhealthy_count"
    rm -f "$LOCKDIR/pid"
    rmdir "$LOCKDIR" 2>/dev/null || true
    rm -f "$PROMPT_FILE" "$MONITOR_OUT" "$GOAL_OUT"
    exit 0
  fi

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

  rm -f "$LOCKDIR/pid"
  rmdir "$LOCKDIR" 2>/dev/null || true
  rm -f "$PROMPT_FILE" "$MONITOR_OUT" "$GOAL_OUT"
}

find "$LOGDIR" -maxdepth 1 -name 'tick_*.log' -mmin +2880 -delete 2>/dev/null
exit "${RC:-1}"
