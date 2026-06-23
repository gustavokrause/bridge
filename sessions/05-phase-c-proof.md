# Session 05 — Phase C: end-to-end auto-finish proof (WATCHED)

You are in **bridge** (read `CLAUDE.md` first). This is **Phase C** from
`CLOSING-THE-CYCLE.md` — the watched, real-execution proof that the cycle closes
autonomously *and* the safety holds. Real Claude runs real code on a real repo
here. Go slow, watch every step, keep the kill switch reachable.

## Preconditions
- Sessions 03 (onboarding) and ideally 04 (real-mode quality) done.
- A **throwaway, non-self-edit** project to target — NOT whale/krill (they can't
  auto-finish by design). Use a scratch repo so a bad merge costs nothing.
  Register it in krill (`POST /api/projects`); local (no remote) is fine.

## Arm (deliberate, double-gated)
1. krill `/settings`: `automation_enabled` ON, `todo_picker` ON.
2. krill: set the scratch project's `allow_auto_finish = true`.
3. whale: `.env` → `WHALE_BYPASS=aggressive`, restart whale.

## Run + watch
1. **Onboard** the scratch project (Context), **Dump** 2–3 low-risk requests → **Plan**.
2. Proposed tab: confirm flow preview shows **auto-finish → DONE** on the low ones.
3. **Push batch** → the **arm-time double-confirm** must fire → confirm.
4. Watch krill: tasks should run PLANNING → IMPLEMENTING → AI-REVIEW → PUBLISHING
   → **DONE with no deliverable gate** (auto-merged). Verify the merge landed.

## Safety drills (the point of C)
- **Breaker**: force failures (e.g. tasks that conflict / fail AI-review) until
  ≥2 auto-finish failures → confirm the project **pauses** (breaker) and stops
  snowballing.
- **Cascade-cancel**: cancel a task with dependents → dependents CANCEL.
- **Self-edit guard**: dump a whale/krill task under the same aggressive+armed
  setup → confirm it does **NOT** auto-finish (forced to human review).

## Also test — carried over from sessions 02–04 (your manual/quality checks)

These need your eyes/ground-truth, not just code. Surfaced while building 02–04.

**UI (session 02) — eyeball at `localhost:3000`:**
- Board shows the new **⚡ auto** badge on tasks with `auto_publish`.
- Task `BALEIA-7` (local-merge deliverable) renders **"local merge · <branch>"**,
  not a broken link. Header + review-aside both.
- Open a project → read-only **Publishing policy** block (`create_pr`/`push_remote`/
  `merge_to_main` = auto/on/off) + **allow_auto_finish** (⚠ flagged).
- **Decision pending (from 02, gated on 06):** do you want these four
  (`create_pr`/`push_remote`/`merge_to_main`/`allow_auto_finish`) **editable** in
  the UI, or stay read-only? Editing a safety dial from a no-auth LAN UI is the risk.

**Onboard accuracy (session 03) — read whale's CONTEXT:**
- `data/context/arqtrack.md` (whole saas-factory monorepo) + `meu-veleiro.md` —
  confirm they're accurate. Fix wrong bits by re-onboarding (Audit) the project.
  (krill/whale already verified vs code.)

**Real-mode stage quality (session 04) — exercise on a throwaway key, judge output:**
- **Planner**: Plan a project → tasks grounded in the project CONTEXT **+ the
  pending requests**, scoped, no codebase-wandering (Augusto kills creep)?
  (sandboxed — verify it stays so.)
- **Audit (onboard)**: produces accurate background CONTEXT (Goals/Stack/Structure)?
- **Refine**: Input a change on a proposed task → applies cleanly, re-triages
  sensibly, flow preview stays correct?
- Where weak, tune wording in `../whale/src/lib/stages.ts` (planReal / routeReal /
  refineProposal) or the onboard prompt in `pipeline.ts`; keep output contracts +
  tests green.
- *(Already fixed: the audit preamble leak — stored CONTEXT starts at `# CONTEXT`.)*

## After
- Disarm (turn `allow_auto_finish` back off, dial back to conservative) unless you
  intend to keep it on.
- Mark **C** in `bridge/CLOSING-THE-CYCLE.md` tracker with results.
- Summary: did it close unattended? did the breaker/guard hold? anything surprising?

## If anything looks wrong
Kill switch: krill `automation_enabled` OFF (global) or pause the project. Both
servers can be stopped from bridge: `npm stop`.
