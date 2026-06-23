#!/usr/bin/env bash
# Boot the fleet: krill (executor) + whale (strategy brain). Idempotent.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KRILL="${KRILL_DIR:-$HERE/../krill}"
WHALE="${WHALE_DIR:-$HERE/../whale}"
LOGS="$HERE/logs"; mkdir -p "$LOGS"

up() { curl -s --max-time 2 "$1" >/dev/null 2>&1; }

# Launch a command in a NEW SESSION, fully detached from the caller's controlling
# terminal. Redirecting fds isn't enough: a long-lived `next start` keeps the
# caller's PTY as its controlling terminal, so the PTY never hits EOF and a
# non-interactive caller (Claude Bash tool / CI / cron) blocks forever. A new
# session drops the controlling terminal. setsid does this on Linux; macOS has no
# setsid, so fall back to a fork()+setsid() python daemonize shim.
detach() { # cmd args... (stdio should be redirected by the caller)
  if command -v setsid >/dev/null 2>&1; then
    setsid "$@" &
  else
    python3 -c 'import os,sys
if os.fork() > 0: os._exit(0)
os.setsid()
os.execvp(sys.argv[1], sys.argv[1:])' "$@" &
  fi
}

start_one() { # name dir health log
  local name="$1" dir="$2" health="$3" log="$4"
  if up "$health"; then echo "✓ $name already up"; return; fi
  if [ ! -d "$dir" ]; then echo "✗ $name dir not found: $dir"; return 1; fi
  echo "-> starting ${name}  (log: ${log})"
  ( cd "$dir" && detach npm start </dev/null >"$log" 2>&1 )
}

start_one krill  "$KRILL"  http://localhost:3000/api/health "$LOGS/krill.log"
start_one whale "$WHALE" http://localhost:4100/api/health "$LOGS/whale.log"

echo "waiting for health…"
for _ in $(seq 1 40); do
  if up http://localhost:3000/api/health && up http://localhost:4100/api/health; then
    echo
    echo "✓ krill  → http://localhost:3000"
    echo "✓ whale → http://localhost:4100"
    exit 0
  fi
  sleep 1
done
echo "⚠ timed out; check $LOGS/krill.log and $LOGS/whale.log"
exit 1
