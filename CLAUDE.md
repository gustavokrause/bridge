# 🌉 bridge — fleet control

This is the **control room** for the AI-fleet. You `cd` here, open Claude Code,
and operate the whole system: start/stop the apps, diagnose them, and work on
any part with the personas loaded.

> Need the plain-words pitch (one-liner / analogy / 30-sec)? → [`docs/PITCH.md`](docs/PITCH.md).

## The fleet (topology)

```
ai-team/ (personas, source of truth)  ──▶  whale (strategy brain)  ──HTTP──▶  krill (executor → PRs)
```

| Repo | Path | Role | Port |
| --- | --- | --- | --- |
| **ai-team** | `../ai-team` | 14 AI personas + routing + risk rubric. Read-only source of truth. | — |
| **whale** | `../whale` | Capture → distill → plan → triage → push. The brain. | 4100 |
| **krill** | `../krill` | Staged task pipeline (plan→review→implement→AI-review→PR). The hands. | 3000 |

One-way dependency: `ai-team ← whale → krill`. whale reads personas, never
writes them; talks to krill over HTTP only.

## Operate

```bash
npm start      # boot krill + whale (idempotent; ./bin/start.sh)
npm run status # diagnose the whole fleet  (./bin/status.sh)
npm stop       # stop both by port         (./bin/stop.sh)
```

Logs land in `./logs/`. Both run **real Claude** by default: whale via its `.env`
(`WHALE_RUNNER=real`), krill via its `.env.local` (`CLAUDE_RUNNER=real`). Both
spawn the Claude Code CLI — no API key.

## Applying changes — build vs restart (READ THIS)

**Both apps now serve a Next production build** (`next start`, serving `.next/`).
Edit → **`npm run build` THEN restart** → live. A plain restart serves **stale
code**. ⚠️ Tests run source via `tsx`, so they pass green while the *server* is
stale — that exact gap stalled A1. After any change to whale or krill:
**build, then restart.**

Convenience: `npm run rebuild` (bridge) rebuilds **both** and restarts the fleet.

**Busy guard**: `npm stop` / `npm run rebuild` now **refuse while the fleet is
working** (a live krill claim or in-flight whale job) — a restart would orphan a
task or kill a Claude run. Override with `npm run rebuild -- --force`. Each app's
footer (and `npm run status`) shows **"safe to restart"** vs **"working —
don't rebuild"**; key it on *live work*, not on tasks merely existing
(NEEDS_REVIEW is parked, safe).

**Iterating on UI?** Run an app in **dev** for hot reload instead of
rebuild-per-change: `cd ../whale && npm run dev` (4100) / `cd ../krill && npm run
dev` (3000). (`start.sh` launches servers detached — in a new session, stdin from
`/dev/null` — so `npm run rebuild` returns cleanly from a non-interactive caller
instead of hanging on the never-exiting `next start`.)

Implication for self-modification: a merged change only takes effect after
**build + restart**, not just merge — that's the real "restart to pick it up."

## How to use this room

- **Diagnose first**: `npm run status` tells you what's up, runner mode, project
  list, inbox/proposed counts, and that all personas load.
- **Work on a part**: edit in its own repo (`../whale`, `../krill`,
  `../ai-team`) — this folder just orchestrates. Run `../whale && npm test`
  before merging whale changes.
- **Consult the team**: invoke any persona (see roster below) the same way you
  would in this session — manual ("act as Caio"), auto-route, or handoff.

## Safety (self-modification)

whale and krill improve *themselves* through this loop. Guards in place:
- whale's triage forces any task targeting `whale`/`krill` to **human review,
  never bypass/auto-finish** (the self-edit guard) — holds on **every** dial,
  including `ludicrous`.
- Work runs in krill **worktrees** → lands as **PRs**; the running process keeps
  old code until *you restart*. Roll back with git + restart.
- `../whale && npm test` is the merge gate. Never merge a self-edit that fails.

The autonomy envelope is now wider — know what you've armed:
- **Dials**: `conservative · balanced · aggressive · autonomous · ludicrous`.
  `ludicrous` auto-finishes **every risk tier** (migrations/auth/deploy merge to
  main unattended); `autonomous` does low+medium. Self-edit always gated.
- **krill loads your user MCP** (e.g. Supabase) into the executor — an armed task
  can write external systems unattended. `KRILL_STRICT_MCP=1` isolates it.
- **Blocker queue**: when whale/krill hit an interactive wall (MCP auth, CLI
  login) they **pause + file a blocker** (surfaced in each app's banner) instead
  of failing; clear it to resume. Not a brake — just no silent stalls.
  - **MCP-auth blockers don't carry a clickable link** — the captured OAuth URL
    is single-use and process-scoped (dead the moment the worker exits; client_id
    is dynamically registered). Authenticate the MCP **once** in a live
    interactive session (`claude` → `/mcp` → authorize), which caches the token;
    krill's headless runner reuses it. Then **Resume** the blocker.
- **Dead-worker recovery**: a restart orphans whatever krill had in flight (the
  worker dies with the process, claim outlives it). krill flags those tasks
  **"worker dead"** on the board with a countdown to the claim-TTL self-heal and a
  **Recover** button (force-release → re-picked next tick). Detection is by
  per-boot generation (`claim_gen`); nothing re-runs unattended beyond the
  existing TTL self-heal.
- **Follow-ups pause picking**: when a krill task surfaces out-of-scope work it
  *seeds a follow-up* (a note, not a task — whale pulls these into its inbox). On
  every follow-up krill now also comments the origin task, files a **persistent
  warning** with the surfaced content, and **pauses the global todo-picker** so a
  human reviews before more auto-picking runs. In-flight tasks keep going. Clear
  it on the board: **Resume** re-enables picking, **Dismiss** keeps it paused. The
  warning is decoupled from whale consuming the follow-up — it persists until you act.

Don't weaken the self-edit guard / merge gate without reading the PR — they're the
brakes that keep the fleet from running itself off a cliff.

## The personas

The full roster, routing modes (manual / auto-route / handoff), and risk rubric
are imported below. Treat them as available here.

@../ai-team/AGENTS.md
