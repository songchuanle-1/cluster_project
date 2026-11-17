#!/usr/bin/env bash
# Run one project tick through a persistent Codex thread with file-backed memory.
set -u

PROJECT="${1:?usage: codex_tick_exec.sh <project> <prompt_file> <log_file> [timeout_seconds]}"
PROMPT_FILE="${2:?}"
LOG="${3:?}"
TIMEOUT_SECONDS="${4:-3600}"

ROOT="${PROJECT_ROOT:-D:/project}"
PROJECT_DIR="$ROOT/$PROJECT"
LOGDIR="$PROJECT_DIR/pipeline/headless"
MEMORY_FILE="$PROJECT_DIR/pipeline/codex_memory.md"
THREAD_FILE="$LOGDIR/.codex_thread_id"
TARGET_THREAD_FILE="$LOGDIR/.codex_target_thread_id"
THREAD_COUNT_FILE="$LOGDIR/.codex_thread_ticks"
CODEX_MODEL="${CODEX_PIPELINE_MODEL:-gpt-6-sol}"
CODEX_FALLBACK_MODEL="${CODEX_FALLBACK_MODEL-deepseek-flash}"
MAX_THREAD_TICKS="${CODEX_THREAD_MAX_TICKS:-48}"
FRESH_THREAD="${CODEX_FRESH_THREAD:-0}"
LAST_MODEL_FILE="$LOGDIR/.codex_last_model"
# Failures that mean "this model could not run at all", so a different model is
# a sensible retry: the model is gone/not permitted, or the provider throttled
# every attempt (429). Genuine mid-turn failures are excluded by the
# no-completed-work guard in model_retryable().
MODEL_RETRYABLE_RE='unknown model|model not found|model_not_found|no such model|model .* not found|the model .* does not exist|model is not available|model unavailable|invalid model|unsupported model|unsupported_model|not have access to (the )?model|model is not supported|429 Too Many Requests|too many requests|rate limit|rate_limit|exceeded retry limit'

mkdir -p "$LOGDIR" "$(dirname "$MEMORY_FILE")"

CODEX_BIN=$(command -v codex || command -v codex.cmd || true)
if [ -z "$CODEX_BIN" ] && [ -n "${LOCALAPPDATA:-}" ]; then
  CODEX_BIN=$(find "$LOCALAPPDATA/OpenAI/Codex/bin" -maxdepth 2 -type f -name "codex.exe" -print -quit 2>/dev/null || true)
fi
if [ -z "$CODEX_BIN" ]; then
  echo "=== NO codex CLI ===" >> "$LOG"
  exit 127
fi

if [ ! -f "$MEMORY_FILE" ]; then
  cat > "$MEMORY_FILE" << 'MEMORYEOF'
# Codex Research Memory

This file is the durable cross-tick research context. Codex must replace the
sections below at the end of every successful tick using current project files.

## Goal And Phase

Not initialized.

## Champion And Baseline

Not initialized.

## Active Hypotheses

Not initialized.

## Closed Or Failed Directions

Not initialized.

## Running And Queue

Not initialized.

## Open Questions And Risks

Not initialized.

## Last Tick

Not initialized.
MEMORYEOF
fi

TARGET_THREAD_ID=$(cat "$TARGET_THREAD_FILE" 2>/dev/null || true)
THREAD_TICKS=$(cat "$THREAD_COUNT_FILE" 2>/dev/null || echo 0)
if ! [[ "$THREAD_TICKS" =~ ^[0-9]+$ ]]; then
  THREAD_TICKS=0
fi
if [ "$FRESH_THREAD" = "1" ]; then
  # Scheduled work should not inherit an unbounded interactive session.
  # Durable project files and codex_memory.md carry state across ticks.
  echo "=== fresh Codex thread requested; ignoring stored thread ids ===" >> "$LOG"
  TARGET_THREAD_ID=""
  THREAD_ID=""
  THREAD_TICKS=0
else
  if [ -z "$TARGET_THREAD_ID" ] && [ "$THREAD_TICKS" -ge "$MAX_THREAD_TICKS" ]; then
    echo "=== rotating Codex thread after $THREAD_TICKS ticks ===" >> "$LOG"
    rm -f "$THREAD_FILE" "$THREAD_COUNT_FILE"
    THREAD_TICKS=0
  fi
  if [[ "$TARGET_THREAD_ID" =~ ^[0-9a-fA-F-]{36}$ ]]; then
    THREAD_ID="$TARGET_THREAD_ID"
    printf '%s\n' "$THREAD_ID" > "$THREAD_FILE"
  else
    THREAD_ID=$(cat "$THREAD_FILE" 2>/dev/null || true)
  fi
fi

COMBINED_PROMPT="$LOGDIR/.codex_prompt_$$.txt"
EVENTS_FILE="$LOGDIR/.codex_events_$$.jsonl"
STDERR_FILE="$LOGDIR/.codex_stderr_$$.txt"
cat > "$COMBINED_PROMPT" << CONTEXTEOF
[Codex compact context contract]

Project working directory: $PROJECT_DIR
Durable memory file: $MEMORY_FILE
Tick context file: $LOGDIR/.tick_context.json

Before acting:
1. Read .tick_context.json first. It contains the completed monitor/goal preflight,
   active queue state, recent experiments, changes, and a bounded file manifest.
2. Read the durable memory file once. Project files override thread history.
3. Obey the context mode:
   - steady: do not enumerate historical directories, read full queue.json, read
     skill/reference files, or inspect old headless logs. Use the snapshot and at
     most one targeted live-log/GPU query when needed for the current run.
   - event: inspect only files tied to changes.new_terminal_ids, listed failures,
     manifests.suggested_reads, or research_work.due_ids. Resume due candidate
     actions even when a new design cycle is not due.
   - design: read goal.json and the bounded manifest first. Open older analyses or
     decisions only by an explicit experiment ID or citation needed for the design.
4. Never read pipeline/headless/tick_*.log during a normal tick. Those logs are
   diagnostic evidence only when .tick_context.json reports a failed/unhealthy tick.
5. Keep tool calls compact: combine related structured reads. Do not repeatedly
   re-read the same file or dump whole directories into the context.

Before finishing a successful tick:
1. On event/design mode, replace the durable memory file with a concise current
   snapshot. On steady mode, do not rewrite it unless durable facts changed.
2. Keep these sections: Goal And Phase; Champion And Baseline; Active Hypotheses;
   Closed Or Failed Directions; Running And Queue; Open Questions And Risks; Last Tick.
3. Keep it under 120 lines. Do not append an unbounded transcript.
4. A steady monitoring result is not a new research decision. Do not create a
   repetitive type=other decision when no policy, queue, terminal state, or route changed.

CONTEXTEOF
cat "$PROMPT_FILE" >> "$COMBINED_PROMPT"

if [[ "$THREAD_ID" =~ ^[0-9a-fA-F-]{36}$ ]]; then
  echo "=== codex resume thread=$THREAD_ID model=$CODEX_MODEL ===" >> "$LOG"
  RUN_MODE=resume
else
  echo "=== codex new thread model=$CODEX_MODEL ===" >> "$LOG"
  RUN_MODE=new
fi

# Execute one codex attempt with the given model. Results land in EVENTS_FILE /
# STDERR_FILE so the caller can inspect them regardless of outcome.
run_codex_attempt() {
  if [ "$RUN_MODE" = "resume" ]; then
    timeout "$TIMEOUT_SECONDS" "$CODEX_BIN" exec \
      -C "$PROJECT_DIR" \
      --model "$1" \
      --dangerously-bypass-approvals-and-sandbox \
      --skip-git-repo-check \
      --json \
      resume "$THREAD_ID" - \
      < "$COMBINED_PROMPT" > "$EVENTS_FILE" 2> "$STDERR_FILE"
  else
    timeout "$TIMEOUT_SECONDS" "$CODEX_BIN" exec \
      -C "$PROJECT_DIR" \
      --model "$1" \
      --dangerously-bypass-approvals-and-sandbox \
      --skip-git-repo-check \
      --json \
      - \
      < "$COMBINED_PROMPT" > "$EVENTS_FILE" 2> "$STDERR_FILE"
  fi
}

# Retrying is only safe when the failed attempt produced no work at all: no
# tool call or message completed, so nothing was written and no side effect can
# be duplicated. `thread.started` is emitted before the first API call and
# therefore cannot be used as the guard. Stderr is searched too because some
# failures are reported there rather than in the JSON event stream.
model_retryable() {
  [ "$1" -ne 0 ] || return 1
  cat "$2" "$3" 2>/dev/null | grep -Eqi "$MODEL_RETRYABLE_RE" || return 1
  grep -q '"type":"item.completed"' "$3" 2>/dev/null && return 1
  return 0
}

ACTIVE_MODEL="$CODEX_MODEL"
run_codex_attempt "$ACTIVE_MODEL"
RC=$?

if [ -n "$CODEX_FALLBACK_MODEL" ] && [ "$CODEX_FALLBACK_MODEL" != "$ACTIVE_MODEL" ] && \
    model_retryable "$RC" "$STDERR_FILE" "$EVENTS_FILE"; then
  echo "=== model '$ACTIVE_MODEL' unavailable or throttled (rc=$RC); retrying with fallback '$CODEX_FALLBACK_MODEL' ===" >> "$LOG"
  cat "$STDERR_FILE" >> "$LOG" 2>/dev/null || true
  : > "$EVENTS_FILE"
  : > "$STDERR_FILE"
  ACTIVE_MODEL="$CODEX_FALLBACK_MODEL"
  run_codex_attempt "$ACTIVE_MODEL"
  RC=$?
  if [ "$RC" -eq 0 ]; then
    echo "=== fallback model '$ACTIVE_MODEL' succeeded ===" >> "$LOG"
  else
    echo "=== fallback model '$ACTIVE_MODEL' failed rc=$RC ===" >> "$LOG"
    grep -Eqi "$MODEL_RETRYABLE_RE" "$STDERR_FILE" "$EVENTS_FILE" 2>/dev/null && \
      echo "=== fallback model was also unavailable or throttled ===" >> "$LOG"
  fi
fi

if [ "$RC" -eq 0 ]; then
  printf '%s\n' "$ACTIVE_MODEL" > "$LAST_MODEL_FILE"
fi

cat "$STDERR_FILE" "$EVENTS_FILE" >> "$LOG" 2>/dev/null || true

# Only a pre-start conflict may skip; tool output can quote historical errors.
if [ "$RC" -ne 0 ] && [ ! -s "$EVENTS_FILE" ] && \
    grep -q "already has an active writer" "$STDERR_FILE" 2>/dev/null; then
  echo "=== target Codex thread is busy; skip this tick without marking unhealthy ===" >> "$LOG"
  rm -f "$COMBINED_PROMPT" "$EVENTS_FILE" "$STDERR_FILE"
  exit 75
fi

if [ "$RC" -eq 0 ]; then
  NEW_THREAD_ID=$(sed -n 's/.*"type":"thread.started","thread_id":"\([^"]*\)".*/\1/p' "$EVENTS_FILE" | head -n 1)
  if [[ "$NEW_THREAD_ID" =~ ^[0-9a-fA-F-]{36}$ ]]; then
    printf '%s\n' "$NEW_THREAD_ID" > "$THREAD_FILE"
  fi
  echo $((THREAD_TICKS + 1)) > "$THREAD_COUNT_FILE"
else
  echo "=== codex tick failed rc=$RC model=$ACTIVE_MODEL; next tick will start a fresh thread ===" >> "$LOG"
  if [[ "$TARGET_THREAD_ID" =~ ^[0-9a-fA-F-]{36}$ ]]; then
    echo "=== retaining pinned target thread=$TARGET_THREAD_ID for retry ===" >> "$LOG"
    rm -f "$THREAD_COUNT_FILE"
  else
    rm -f "$THREAD_FILE" "$THREAD_COUNT_FILE"
  fi
fi

rm -f "$COMBINED_PROMPT" "$EVENTS_FILE" "$STDERR_FILE"
exit "$RC"
