# Session 02 — UI sync (krill / whale / bridge)

You are in the **bridge** control room (read `CLAUDE.md` + `AGENTS.md` here first).
This session updates the **UIs** to surface what shipped in `CLOSING-THE-CYCLE.md`
(A1–A3, B0–B5). Many new capabilities exist in the data + API but aren't visible
or controllable in the interface yet. Make them visible and usable.

## Start

```bash
npm run status                       # fleet up? (krill :3000, whale :4100)
```

Read first:
1. `bridge/CLOSING-THE-CYCLE.md` — source of truth for what was built.
2. The actual API responses + schema, so the UI shows **real** fields, not guesses
   (`curl localhost:3000/api/tasks`, `/api/projects`; `curl localhost:4100/api/...`).

Scope note: this is UI-layer work. You may read APIs and add UI components /
controls; do **not** change workflow logic, schema, or the autonomy rules. If a
field the UI needs isn't exposed by an API, surface that in your summary (or add a
read-only API field if trivial) — don't change behavior.

## krill (`../krill`) — the main UI work (Next.js)

UI lives in `src/app/` (`(board)/`, `projects/`, `settings/`, `tasks/[id]`).
Currently the board doesn't show the new flags (the user couldn't see
`skip_plan_review`). Surface, verify each against `/api/tasks` + `/api/projects`:

- **Task detail / board**: show `skip_plan_review`, `auto_publish` (auto-finish),
  `depends_on` (and blocked-by-unfinished-dep), and the delivery form — PR url vs
  `local:<branch>`. Make a task that **auto-finished** (PUBLISHING→DONE, no
  deliverable review) legible.
- **Project settings** (`projects/` or `settings/`): expose per-project **publish
  policy** (`create_pr` / `push_remote` / `merge_to_main` — show auto-detected
  value, allow override) and the **`allow_auto_finish`** toggle (default off; this
  is the dangerous one — label it clearly).
- **Paused state**: the circuit breaker can set `project.paused` — show it and
  offer resume, so a breaker-tripped project is obvious, not silently stalled.
- Existing global toggles (`automation_enabled`, `todo_picker`) should be easy to
  find (the user had to hunt for them).

Rebuild after UI changes: krill serves the production build →
`cd .. && npm run rebuild` (bridge) to see them live.

## whale (`../whale`) — light polish (single-page `src/ui.mjs`)

The pipeline UI shipped this session (tabs, flow preview, onboard, batch push,
refine/Input, double-confirm, lane pills). Verify it's all wired + usable; polish
gaps only:
- Proposed items: confirm **flow preview**, **auto-finish** indication, and
  **refined-count** show; consider showing a task's `deps` and refine history.
- Confirm the **arm-time double-confirm** dialog reads clearly for auto-finish.
- whale restarts from source: `cd ../whale && lsof -ti tcp:4100 | xargs kill; npm start`.

## bridge (this repo) — no GUI

bridge's "UI" is `bin/status.sh`. Optionally enrich it to show new fleet state:
projects with `allow_auto_finish` on, any `paused` (breaker-tripped) projects,
auto-finished task counts. Optional, low priority.

## Constraints
- **UI layer only** — no workflow/schema/autonomy logic changes.
- **Verify against real API data** before rendering a field.
- **Per-repo commits**, conventional (krill = Conventional Commits); commit only on
  the user's go.
- Don't touch `CLOSING-THE-CYCLE.md`.

## Done when
- krill UI surfaces the new flags + project policy/permission + paused state, and
  is rebuilt + verified live.
- whale UI polish confirmed.
- A short summary: what changed per repo + any missing API fields you hit.
