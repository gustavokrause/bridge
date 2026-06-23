#!/usr/bin/env bash
# Apply a code change to either app: stop, rebuild both production bundles, restart.
# Both whale and krill now serve a Next production build (`next start`) — a plain
# restart serves stale code, so always build first.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KRILL="${KRILL_DIR:-$HERE/../krill}"
WHALE="${WHALE_DIR:-$HERE/../whale}"

bash "$HERE/bin/stop.sh" "$@" || exit 1

echo "building whale (next build)…"
( cd "$WHALE" && npm run build ) || { echo "✗ whale build failed — not restarting"; exit 1; }
echo "building krill (next build)…"
( cd "$KRILL" && npm run build ) || { echo "✗ krill build failed — not restarting"; exit 1; }

bash "$HERE/bin/start.sh"
