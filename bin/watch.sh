#!/bin/bash
# watch.sh — follow a krill task through the pipeline from the terminal.
#
#   npm run watch                # wait for the NEXT task created, then follow it
#   npm run watch -- <task-id>   # follow a specific task id
#
# Logs every status transition; on any terminal state (DONE / CANCELED /
# NEEDS_REVIEW park) dumps the task's stage_usage rows — stage, model (shows
# whether the cheap-first review ladder ran Sonnet), tokens, cache, cost — and
# whether diff_text was captured at IMPLEMENTING end. Read-only: SELECTs only.
#
# Env knobs: WATCH_INTERVAL (poll seconds, default 30),
#            WATCH_MAX_POLLS (default 480 ≈ 4h at 30s).
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"
DB="${KRILL_DB:-$DIR/../krill/data/tasks.db}"
INTERVAL="${WATCH_INTERVAL:-30}"
MAX="${WATCH_MAX_POLLS:-480}"
TASK="${1:-}"

if [ ! -f "$DB" ]; then
  echo "krill db not found at $DB" >&2
  exit 1
fi

q() { sqlite3 "$DB" "$1"; }

dump_usage() {
  echo "--- stage_usage for $TASK ---"
  q "SELECT stage, model, resumed, input_tokens, output_tokens, cache_creation_tokens, cache_read_tokens, round(cost_usd,4), num_turns, duration_ms FROM stage_usage WHERE task_id='$TASK' ORDER BY created_at;"
  echo "--- diff_text ---"
  q "SELECT CASE WHEN diff_text IS NULL THEN 'null' ELSE 'yes (' || length(diff_text) || ' chars)' END FROM tasks WHERE id='$TASK';"
}

if [ -n "$TASK" ]; then
  if [ -z "$(q "SELECT id FROM tasks WHERE id='$TASK';")" ]; then
    echo "task $TASK not found" >&2
    exit 1
  fi
  echo "$(date +%H:%M:%S) following $TASK"
else
  BASELINE=$(q "SELECT COALESCE(MAX(created_at),0) FROM tasks;")
  echo "$(date +%H:%M:%S) waiting for next new task (created_at > $BASELINE)…"
fi

LAST=""
for _ in $(seq 1 "$MAX"); do
  if [ -z "$TASK" ]; then
    TASK=$(q "SELECT id FROM tasks WHERE created_at > $BASELINE ORDER BY created_at LIMIT 1;")
    [ -n "$TASK" ] && echo "$(date +%H:%M:%S) NEW TASK: $TASK"
  fi
  if [ -n "$TASK" ]; then
    ST=$(q "SELECT status || '|' || COALESCE(pending_review_kind,'') FROM tasks WHERE id='$TASK';")
    if [ "$ST" != "$LAST" ]; then
      echo "$(date +%H:%M:%S) status=$ST"
      LAST="$ST"
    fi
    case "$ST" in
      DONE\|*|NEEDS_REVIEW\|*|CANCELED\|*)
        echo "$(date +%H:%M:%S) TERMINAL: $ST"
        dump_usage
        exit 0
        ;;
    esac
  fi
  sleep "$INTERVAL"
done

echo "TIMEOUT after $((MAX * INTERVAL / 60)) min task=${TASK:-none} last=$LAST"
[ -n "$TASK" ] && dump_usage
exit 1
