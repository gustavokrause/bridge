# Session 09 — Refactor whale to krill's stack  ⚠️ BIG, RISKY

You are in **bridge** (read `CLAUDE.md` first). Goal: rewrite whale from its
zero-dep stack (`node:http` + `node:sqlite` + a single inline-HTML `ui.mjs`) to
**the same stack as krill**, so the fleet has one mental model and whale's UI stops
generating hand-rolled-DOM papercuts (refresh, routing, contract drift).

This is a **port for parity first**, not a redesign. Behavior must match what's in
`CLOSING-THE-CYCLE.md` (B0–B5) and the live app before you touch anything.

## Why
- `ui.mjs` is ~190 lines of string-concatenated HTML, growing every feature; the
  refresh + tab-routing bugs were symptoms (patched in vanilla JS — see git log).
- **TS** would catch the contract bugs we've hit (the audit preamble leak, whale
  assuming krill's `POST /api/tasks` shape).
- krill already *is* this stack with reusable components — converging is cheaper
  than maintaining two patterns. krill also has **SSE** (`/api/stream`), which gives
  whale real push updates instead of the 5s poll.

## The target stack (match krill exactly — read its configs as the template)
Next 16 (App Router) · React 19 · TypeScript 5.7 · **drizzle-orm + better-sqlite3**
· drizzle-kit migrations · Tailwind 3 · Radix UI + lucide-react · zod · `tsx`
node:test integration tests. Copy krill's `tsconfig`, `next.config`, `drizzle.config`,
Tailwind/PostCSS, and the `src/components/ui/*` primitives (badge, switch, tabs,
toast, dialog, tooltip, select) as the base.

## Scope — DECIDED (2026-06-15)
- **Full Next port.** server.mjs routes → Next API routes; node:sqlite →
  drizzle/better-sqlite3. One stack, matches krill 1:1. (Not the UI-only option.)
- **Build step accepted.** whale loses "runs from source = live" and gains
  build-then-restart like krill — the user is fine with this (≈ same effort as
  stop/restart). Still update bridge so it's wired correctly: `bin/start.sh` /
  `rebuild.sh` (whale now needs `next build`; `rebuild` should build whale too) and
  `CLAUDE.md`'s build-vs-restart section (whale joins krill in the build column).
  Note the A1 caveat — a plain restart would serve stale code, so always build first.

## What to port (parity checklist)
- **DB** (`db.mjs`) → drizzle schema + migrations: `inbox_entries`, `proposed_tasks`
  (incl. `auto_publish`, `deps`, `refine_log`), and the **`config` singleton**
  (runner/models/bypass/auto_push/allow_new_projects — **no `protected` column**).
- **Logic modules** (`stages`, `pipeline`, `runner`, `persona-loader`,
  `context-store`, `krill-client`) → `.mjs` → `.ts`, add types, keep contracts.
  `runner` still spawns the `claude` CLI; `context-store` keeps `normalizeContext`.
- **API routes** → Next handlers, same paths/semantics:
  `/api/health`, `/api/inbox`, `/api/distill`, `/api/context`, `/api/onboard`,
  `/api/plan`, `/api/proposed` (+ `/:id/approve|reject|push|reassign|refine`),
  `/api/proposed/push-batch`, `/api/route`, `/api/config` (GET/PATCH).
- **UI** (`ui.mjs`) → React pages/tabs: Inbox · Context · Proposed · Settings.
  Routing is native (App Router / real URLs) — kills the hash hack. Replace the 5s
  poll with **SSE** (mirror krill's `/api/stream` + broadcast on mutations).
- **Config**: keep the live-override model — DB wins over env, no restart; Settings
  page edits the tunables; `protected` shown read-only.
- **Tests** (`smoke.test.mjs`, `context.test.mjs`, 11 total) → port to krill's
  `node --import tsx --test` setup. Keep the self-edit-guard + config-override tests.

## 🔴 Safety — do not lose this in the rewrite
- **Self-edit guard stays env-only with a hard `whale,krill` floor.** No DB column,
  no PATCH path, read-only in the UI. A no-auth LAN UI must never weaken it. Port the
  test that proves it.
- whale talks to krill **over HTTP only** (`KRILL_URL`), never its DB. Keep that.
- Keep port **4100**, the `WHALE_*` env names, and the autonomy ladder semantics
  (conservative/balanced/aggressive; aggressive+low → auto_publish; high/self-edit
  never bypass).

## Suggested sequence
1. Scaffold Next + copy krill configs + `ui/*` primitives.
2. drizzle schema + migrate + seed (parity with current tables).
3. Port logic modules `.mjs`→`.ts` (no behavior change); port tests; green.
4. Port API routes; curl-parity against the old server.
5. Build the React UI (4 tabs) on real routes; add SSE.
6. Wire bridge (build step) + update docs.

## Carry-in fix — krill→whale status sync (gap A)

whale is **fire-and-forget today**: it pushes a task, marks the `proposed_tasks` row
`pushed` + stores `krill_task_id`, then **never reconciles krill's outcome**. So the
Proposed tab shows stale rows and the planner re-proposes work that's already DONE in
krill (it reads CONTEXT, not krill's task list). Real example found 2026-06-15: whale
had a rejected "Remove dump textarea placeholder" while krill `BALEIA-7` (same intent)
was DONE — two disconnected instances.

Fix as part of this refactor (SSE makes it clean):
- **Reconcile** pushed proposals against krill: poll `GET /api/tasks/:id` (or krill's
  SSE) for each `krill_task_id`; reflect DONE/CANCELED/in-flight on the whale row and
  in the Proposed UI. A pushed-then-DONE task should read as done, not linger.
- **Plan-time awareness:** when planning, exclude/flag intents already DONE in krill
  for that project, so the planner stops re-proposing finished work.
- Keep the boundary: whale reads krill over HTTP only; this is read-back, not shared DB.

(Separately, **gap B — manual delete + hide-rejected — already shipped** in the
zero-dep UI: `DELETE /api/inbox/:id` + `/api/proposed/:id`, delete buttons, and the
Proposed view hides `rejected` by default. Port that behavior forward.)

## Done when
- Feature parity: dump→distill→plan→triage→push, onboarding, refine, batch+deps,
  flow preview, arm-time double-confirm, UI-config — all work on the new stack.
- Tests green (parity with the 11, ideally more); `tsc --noEmit` clean.
- Fleet runs: whale on its Next build at `:4100`; `npm run status` green.
- **Self-edit guard verified** (whale task forced 🔴; protected not UI-editable).
- bridge build-vs-restart docs + scripts updated; no stale `ui.mjs`/`node:sqlite`.

## Constraints
- Parity before polish. Don't redesign UX or autonomy rules in the same pass.
- Per-repo commits (whale = Conventional Commits, matching krill), on the user's go.
- This is large — expect multiple sessions. Land it behind green tests at each phase.
