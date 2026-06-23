# Session 01 — Docs sync (bridge / whale / krill)

You are in the **bridge** control room (read `CLAUDE.md` + `AGENTS.md` here first).
This session is **docs-only**: bring every repo's documentation in line with the
code that shipped in `CLOSING-THE-CYCLE.md` (phases A1–A3, B0–B5). The code is
done and tested; the prose drifted. No behavior changes.

## Start

```bash
npm run status          # confirm fleet + paths
```

Read, in order:
1. `bridge/CLOSING-THE-CYCLE.md` — **the source of truth** for what was built
   (design §1–6 + the Implementation Tracker at the bottom: A1, A2, A3, B0–B5).
2. The target docs (below). For any claim you write, **verify it against the
   actual code**, not memory. Run the test suites if unsure
   (`cd ../krill && npm test`, `cd ../whale && npm test`).

## Goal

Each repo's docs should accurately describe current behavior so a newcomer (or a
future session) isn't misled. Fix drift, add the new capabilities, remove stale
claims. Keep docs tight — update, don't bloat.

## Per-repo checklist

### krill (`../krill`)
Docs: `README.md`, `OVERVIEW.md`, `ARCHITECTURE.md`, `RUNBOOK.md`, `CLAUDE.md`.
Make sure they cover what A1–A3 added (verify each against the schema/code):
- **Publish policy** (A1): per-project `create_pr` / `push_remote` / `merge_to_main`,
  nullable = auto-detect from remote presence; **local-merge path** for remote-less
  repos (publish → `local:<branch>` deliverable → `localMergeToMain` on approve).
- **Auto-finish** (A2): `tasks.auto_publish` + `projects.allow_auto_finish`,
  `deliverOrAutoFinish` (skip deliverable + merge → DONE, double-gated, AI-review
  stays on), `workflow/finish.ts`.
- **Circuit breaker + cascade-cancel** (A3): `workflow/breaker.ts` (2-fail/30%
  pause; decline → cancel dependent subtree; pause/resume emergent from deps).
- **Migrations** 0004 (publish policy) + 0005 (auto-finish columns).
- Fix the stale line claiming **stub Claude by default** — it's `CLAUDE_RUNNER=real`
  via `.env.local`.
- The OVERVIEW state machine: note the deliverable gate can now be skipped by
  auto_publish, and the new `local:` delivery form.

### whale (`../whale`)
Docs: `README.md`, `PLAN.md`, `.env.example`.
- README should describe the **full pipeline** as built: capture inbox → distiller
  → CONTEXT → planner (Augusto+Maria, **sandboxed**) → triage → router → batch
  handoff (deps) → push to krill; plus **onboarding** (audit/seed), the
  **Approve/Decline/Input refine loop**, **flow preview**, **arm-time double-confirm**.
- The **runner** mirrors krill (spawns the `claude` CLI, no API key); sandboxed by
  default, read-only `auditComplete` for onboarding.
- **Autonomy ladder** (B1): `WHALE_BYPASS` conservative/balanced/aggressive →
  skip_plan_review; aggressive+low → `auto_publish`. Document each rung + the
  self-edit guard (`WHALE_PROTECTED`) + that auto-finish needs krill's
  `allow_auto_finish` too.
- `.env.example`: ensure every knob is listed + accurate (route is `haiku`,
  timeout 240s, etc.).
- `PLAN.md`: reconcile with what shipped (it predates B0–B5). Either update it or
  mark superseded by `CLOSING-THE-CYCLE.md` for the autonomy work.

### bridge (this repo)
Docs: `README.md`, `CLAUDE.md`.
- Confirm the fleet description, ports, the **build-vs-restart** rule (krill =
  `npm run rebuild`), and the personas import are all current. Light touch.

## Constraints
- **Docs only.** No code, no schema, no behavior changes. If you find a code/doc
  mismatch that's a *code* bug, note it in your summary — don't fix it here.
- **Verify before you write.** Grep the code / run tests; don't document intent,
  document reality.
- **Per-repo commits**, conventional style (krill uses Conventional Commits).
  Commit only when asked, per the user's standing rule.
- Don't rewrite `CLOSING-THE-CYCLE.md` (it's the tracker/source of truth). You may
  reference it.

## Done when
- krill, whale, bridge docs each match current behavior (spot-checked vs code).
- A short written summary: what you changed per repo + any code/doc mismatches found.
- Changes committed (on the user's go).
