#!/usr/bin/env bash
# Stop the fleet by port (reliable across npm/next/node process trees).
# Refuses while the fleet is working (would orphan a task / kill a Claude run)
# unless --force is passed. See bin/check-busy.sh.
set -uo pipefail

KRILL_PORT="${KRILL_PORT:-3000}"
WHALE_PORT="${WHALE_PORT:-4100}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORCE=0
for a in "$@"; do [ "$a" = "--force" ] && FORCE=1; done

if [ "$FORCE" -ne 1 ]; then
  if ! bash "$HERE/check-busy.sh"; then
    echo "Refusing to stop — the fleet is working (a restart would orphan it)."
    echo "Wait for it to go idle, or re-run with --force to override."
    exit 1
  fi
fi

stop_port() { # label port
  local label="$1" port="$2"
  local pids; pids="$(lsof -ti tcp:"$port" 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    kill $pids 2>/dev/null && echo "■ stopped $label (:$port)"
  else
    echo "· $label not running (:$port)"
  fi
}

stop_port whale "$WHALE_PORT"
stop_port krill  "$KRILL_PORT"
