#!/usr/bin/env bash
# Exit non-zero (and report) if either app has live work a restart would orphan:
#   krill — live claims (a worker mid-stage), from /api/health.active_claims
#   whale — in-flight Claude jobs (plan / onboard audit), from /api/jobs.running
# A down app can't be busy, so its check is skipped. Used by stop.sh / rebuild.sh.
set -uo pipefail

KRILL_PORT="${KRILL_PORT:-3000}"
WHALE_PORT="${WHALE_PORT:-4100}"
KU="http://localhost:$KRILL_PORT"
BU="http://localhost:$WHALE_PORT"

busy=0

k="$(curl -s --max-time 3 "$KU/api/health" 2>/dev/null || true)"
if [ -n "$k" ]; then
  msg="$(printf '%s' "$k" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{const h=JSON.parse(s);if((h.active_claims||0)>0)console.log('krill busy: '+h.active_claims+' live claim(s) ('+(h.active_claim_ids||[]).join(', ')+')')}catch(e){}})")"
  if [ -n "$msg" ]; then echo "⚠ $msg"; busy=1; fi
fi

w="$(curl -s --max-time 3 "$BU/api/jobs" 2>/dev/null || true)"
if [ -n "$w" ]; then
  msg="$(printf '%s' "$w" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{const d=JSON.parse(s);const r=d.running||[];if(r.length>0)console.log('whale busy: '+r.length+' job(s) ('+r.map(j=>j.kind+':'+j.key).join(', ')+')')}catch(e){}})")"
  if [ -n "$msg" ]; then echo "⚠ $msg"; busy=1; fi
fi

exit $busy
