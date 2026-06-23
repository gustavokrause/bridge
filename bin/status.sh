#!/usr/bin/env bash
# Diagnose the whole fleet: tooling, both apps, projects/tasks, personas.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KRILL="${KRILL_DIR:-$HERE/../krill}"
WHALE="${WHALE_DIR:-$HERE/../whale}"
AI_TEAM="${AI_TEAM_DIR:-$HERE/../ai-team}"
KU="http://localhost:3000"; BU="http://localhost:4100"

j() { node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{$1}catch(e){console.log('  (parse error)')}})"; }

echo "═══ FLEET STATUS ═══"
echo "node $(node -v)  ·  claude $(command -v claude >/dev/null && claude --version 2>/dev/null | head -1 || echo 'NOT FOUND')"
echo "paths: krill=$KRILL  whale=$WHALE  ai-team=$AI_TEAM"
echo

echo "── krill (executor) :3000 ──"
if curl -s --max-time 3 "$KU/api/health" | j "const h=JSON.parse(s); console.log('  up · automation='+h.automation_enabled+' · projects='+h.projects.total+' · active='+h.active_tasks);"; then :; else echo "  ✗ down"; fi
curl -s --max-time 3 "$KU/api/projects" | j "console.log('  projects: '+JSON.parse(s).projects.map(p=>p.slug).join(', '))" 2>/dev/null || true

echo "── whale (strategy) :4100 ──"
if curl -s --max-time 3 "$BU/api/health" | j "const h=JSON.parse(s); console.log('  up · runner='+h.runner+' · bypass='+h.autonomy.bypass+' · protected='+(h.autonomy.protected||[]).join('/'));"; then :; else echo "  ✗ down"; fi
curl -s --max-time 3 "$BU/api/inbox" | j "console.log('  inbox: '+JSON.parse(s).entries.length+' entries')" 2>/dev/null || true
curl -s --max-time 3 "$BU/api/proposed" | j "console.log('  proposed: '+JSON.parse(s).proposed.length)" 2>/dev/null || true

echo "── ai-team (personas) ──"
curl -s --max-time 5 "$BU/api/personas" | j "const h=JSON.parse(s); console.log('  PERSONAS ('+h.count+'): '+(h.ok?'✓ all resolved':'⚠ thin: '+(h.thin||[]).join(',')));" 2>/dev/null || echo "  ✗ persona check failed (whale up?)"
