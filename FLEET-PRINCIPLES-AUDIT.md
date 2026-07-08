# Fleet Principles Audit — whale + krill

> **Caio (AI/Orchestration).** I read the whole fleet against the four operating
> principles in [`docs/principles/`](docs/principles/), then traced the real code
> (not the docs) for evidence. This is not a feature wishlist. It's a gap report:
> what each principle demands, what the fleet already ships, and the exact places
> the architecture still violates it — with `file:line` and a concrete fix.
>
> **The challenge first, before any list:** you encoded an intent-compression
> philosophy into how *you* work with Claude — capture the WHY once, reuse it,
> drive repeated derivation toward zero. Your fleet's architecture does the
> opposite. At every boundary it **re-derives from cold**: whale re-derives your
> intent on every plan run, krill re-tokenizes the same diff/context on every
> stage. The machine preaches the principle and then doesn't practice it. That
> single disease — *re-derivation instead of capture-and-reuse* — is the highest-
> leverage thing to fix, and it shows up under three of the four principles.

---

## The four principles (lens)

Full text in [`docs/principles/`](docs/principles/):

1. **[Pipeline self-resolves](docs/principles/pipeline-self-resolves.md)** — a
   pipeline must robustly handle *any* task and **always conclude** (escalate,
   never timeout-loop or silently stall). Brittle on a trivial task = dead on a
   heavy one. Fix the **class**, never patch one case.
2. **[Token economics span sessions](docs/principles/token-economics-span-sessions.md)**
   — judge cost across the **whole lifecycle**, not one call. Heavier upfront is
   fine if every later stage is leaner.
3. **[Intent-library method](docs/principles/intent-library-method.md)** — capture
   the human's WHY/intent as reusable principles, **lead with cause-level reads**,
   compress repeated intent-transfer toward zero.
4. **[Instruction-file voice is load-bearing](docs/principles/instruction-file-voice-load-bearing.md)**
   — voice/grammar in prompts & personas is functional; compression that *looks*
   lossless can change behavior. A/B real output before trusting it.

---

## The central finding: the fleet re-derives what it should capture

Two of the biggest gaps are the **same disease at two layers**:

| Layer | What it re-derives every time | What it should do |
|---|---|---|
| **whale** | Your intent / WHY — re-read from raw dumps on every plan run; CONTEXT.md is a static repo audit, never fed by dumps/refine/reject | Capture intent once into a living store; reuse it; measure when re-derivation is needed |
| **krill** | The diff / files / plan — re-tokenized full-price on every cold `claude` spawn (PLAN→IMPL→REVIEW→VERIFY) | Carry one warm session forward; the bytes tokenized once become cache-reads downstream |

Same shape. Same fix philosophy: **pay once upfront, reuse cheaply after** — which
is exactly [token-economics-span-sessions](docs/principles/token-economics-span-sessions.md)
*and* [intent-library-method](docs/principles/intent-library-method.md). Fixing
these two is ~80% of the value in this document.

And a meta-callout you should sit with: the **VERIFYING** stage was rebuilt to be
proportional, budget-aware, and always-concluding (commit `de5b4fc`) — the
case that produced [pipeline-self-resolves](docs/principles/pipeline-self-resolves.md).
But that fix was applied to **one stage only**. It was never generalized into a
shared primitive. So the principle's own origin fix *violated the principle* — it
patched one case instead of fixing the class. Every other stage that can hang
(AI-REVIEW, PLANNING, IMPLEMENTING, stuck, orphaned claims) still loops or strands.
You fixed the symptom and shipped it.

---

## Principle 1 — Pipeline self-resolves

**Already shipped (credit):** VERIFYING has an episode-scoped incomplete-run
counter → brake at `max_ai_decline_cycles` → park at `NEEDS_REVIEW(verify)` +
`pauseLineForHuman` (`krill/src/workflow/stages/verify.ts:99-163`). AI-REVIEW
decline, verify-fail, publishing hard-error and conflict all park at human review.
The happy path and the *AI-judgment* paths conclude well. **Net: ~70% to
"self-resolves any task."** The missing 30% is every **infrastructure-failure**
path — a crash, a hang, or a run that simply never transitions.

| # | Gap | Evidence | Fix | Effort |
|---|---|---|---|---|
| 1.1 | **No-verdict runs loop forever.** ⚠ **Corrected 2026-07-08** (see Verification pass): true for **AI-REVIEW only** — PLANNING/IMPLEMENTING drive their own transitions in code and always conclude on normal exit; their loop risk is the **throw/timeout path**. AI-REVIEW loops at full **Opus** cost each pass. | `ai-review.ts:43-64` vs `verify.ts:99-170`; throw paths `planning.ts:65-70`, `implementing.ts:69-74` | AI-REVIEW: mirror VERIFY's brake (tracker A3). PLANNING/IMPLEMENTING: bounded retry-on-throw (tracker A4). | M |
| 1.2 | **Stuck detection is notify-only.** A task hung past `max_stage_duration` emits an SSE event and waits; the only "recovery" is TTL lapse → re-pick → re-hang. Infinite retry, not conclusion. | `stuck.ts:72-86` (comment: "no auto-recovery"), `cron.ts:82-90` | After N stuck observations (or `age > k·max_stage_duration`), force-conclude: `forceReleaseClaim` + `NEEDS_REVIEW(stuck)` + `pauseLineForHuman`. | M |
| 1.3 | **Orphaned claims wait up to 30 min.** A process that dies mid-stage strands its claim until TTL (1800s) or a human clicks Recover. No dead-process scanner. | `boot-id.ts:9-10`; `forceReleaseClaim` sole caller is the UI route `api/tasks/[id]/recover/route.ts:24` | Boot-time + periodic scanner force-releases claims where `claim_gen != getBootId()` (unambiguously dead) → next tick re-picks immediately. | S |
| 1.4 | **Escalation has no lifetime cap.** `task_escalate` resets `resolver_tried:false` each time, so escalate → auto-resolve → back-to-stage → re-escalate can cycle indefinitely. | `mcp-tools.ts:504-510`, `escalation.ts:46-72` | Track `escalation_count`; after `max_ai_decline_cycles` go straight to `pauseLineForHuman` instead of re-running the resolver. | S |
| 1.5 | **Loop-brake counts comment volume, not episodes.** `countAiAutoActions` counts all AI comments since the last human comment — cross-stage, not episode-scoped. Can mis-trip (premature park) or never reset. | `loop-brake.ts:19-36`, consumed at `mcp-tools.ts:372,442`, `publishing.ts:384` | Count stage-tagged, episode-scoped markers (`since stage_entered_at`), like VERIFY's own counter. | M |
| 1.6 | **Publishing conflict can loop.** ⚠ **Corrected 2026-07-08**: overstated — the conflict path is bounded by the shared `countAiAutoActions` brake, and publishing already has a dedicated hard-failure counter (`countPublishFailures` MAX=3 → park) the audit missed. Residual: the conflict sub-path leans on the cross-stage counter (see 1.5). | `publishing.ts:382-412` (conflict), `:54-64,195` (dedicated counter) | Covered by episode-scoping the shared brake (tracker A9); no dedicated conflict counter needed. | S |
| 1.7 | **Resolver can run in the live repo.** If the worktree is gone but the task is `NEEDS_REVIEW(question)`, the resolver runs Opus in the real project folder as fallback cwd — can mutate outside a worktree. | `escalation.ts:77-80` | If no worktree/workspace exists, defer to human; never execute in the live repo. | S |
| 1.8 | **No orphaned-worktree GC.** Worktrees are removed only on a clean transition; a dead-process or deleted-task worktree leaks disk and can collide with `ensureWorkspace` on retry. | `cleanup.ts:42` (sole `removeWorktree` caller) | Boot-time + periodic GC: drop worktrees under `worktrees_root` with no matching active task. | M |
| 1.9 | **Spec endorses the wrong design.** `OVERVIEW.md:281,316` still codify "log + notify, no auto-retry loop" for stuck tasks — the spec actively contradicts the VERIFY fix. | `OVERVIEW.md:281,316` | Update the spec to mandate the VERIFY pattern (bounded brake → park → pauseLine) for every stuck-eligible stage. | S |

**The class fix (do this, not 1.1–1.9 one by one):** ⚠ **Corrected 2026-07-08**
— "one primitive for every stage" was over-generalized: PUBLISHING and the
escalation resolver already brake, and PLANNING/IMPLEMENTING need a
retry-on-throw counter, not a no-verdict brake. The correct decomposition is
three pieces (tracker A1/A3/A4): a **force-conclude scanner** as the universal
backstop, a VERIFY-mirror brake on **AI-REVIEW only**, and bounded
retry-on-throw for the code-driven stages. Still the
[pipeline-self-resolves](docs/principles/pipeline-self-resolves.md) move — the
scanner is the class fix; the per-stage brakes are precision.

---

## Principle 2 — Token economics span sessions

**Already shipped (credit):** per-stage metering into `stage_usage`
(`usage.ts`, `usage-rollups.ts`), bundled planning writes (`task_set_plan_bundle`),
a cache-friendly system prefix (`--exclude-dynamic-system-prompt-sections`), Sonnet
on VERIFY, bounded decline brake. **Verdict: krill optimizes _per-call_ cost, not
_lifecycle_ cost.** The metering tells you what you spend; it doesn't stop you
paying full input price 3–5× for the same bytes.

| # | Waste | Evidence | Fix | Savings | Effort |
|---|---|---|---|---|---|
| 2.1 | **Every stage is a cold spawn — no session reuse.** Cold spawn confirmed. ⚠ **Corrected 2026-07-08**: the `--resume` fix is **not viable as written** — session id never captured, per-stage model switching collides with resume, stage-scoped MCP auth tokens break it, and TTL-blown accumulating context plausibly costs *more*. Also: dynamic-content-via-tool-results is a deliberate cache lever (`--exclude-dynamic-system-prompt-sections`), not pure defect; cron slots are fixed 10s apart, not "10–60s". | `runner.ts:84-119`, `cron.ts:40-47`; blockers: `runner.ts:44-61`, `mcp-auth.ts:19-32`, `model-map.ts` | Demoted to design spike (tracker B4). Real near-term cuts: B1 (persist diff), B2 (model ladder), B3 (verify skip). | ~~40–70%~~ unproven — see Verification pass | L |
| 2.2 | **AI-REVIEW and VERIFY re-derive the diff.** IMPLEMENTING already computed the diff (`diffNamesAgainstBase`) but forwards only the path list; each downstream pass re-shells `git diff` and re-expands every file. Diff text re-tokenized 2–3×. | `implementing.ts:81-88` (diff computed, discarded), `ai-review-dev.md:7`, `verify-dev.md:2` | Persist the unified diff once at end of IMPLEMENTING; feed it inline to REVIEW/VERIFY. | 20–40% of REVIEW+VERIFY input | M |
| 2.3 | **Flat tiering, no cheap-first ladder.** Opus pinned on PLANNING + AI-REVIEW unconditionally; the escalation resolver runs **Opus on every fork**. Trivial plans and clean diffs burn Opus at ~5× Sonnet. | `model-map.ts:5-16`, `escalation.ts:82` | Haiku/Sonnet first-pass for AI-REVIEW that approves obvious-clean diffs and escalates only ambiguous ones to Opus; resolver on Sonnet, Opus only on defer. **Meter the decline-flip rate** (quality guard). | 30–60% of AI-REVIEW Opus spend; ~50%/fork | M |
| 2.4 | **Retries re-spawn full context.** Each decline / verify-fail / no-verdict retry is a cold process reloading everything (`OPERATIONAL_COST.md:27-28` already shows 1–2M-token decline cycles). Brake caps the *count*, not the *per-retry cost*. | `mcp-tools.ts:393-399`, `verify.ts:121-163`, `loop-brake.ts:43` | Feed only the **delta** (decline reason / failing assertion) into a resumed session. Rides on 2.1. | 50–70% per retry cycle | M |
| 2.5 | **VERIFY re-runs build/tests even when static.** Non-docs static changes still pay a full VERIFY spawn even when AI-REVIEW just cleared the same diff. Only docs-only auto-skips. | `implementing.ts:122-133`, `verify-dev.md` | Let AI-REVIEW emit a "static-sufficient" signal that auto-skips the dynamic VERIFY spawn for low-blast-radius diffs. | one full 20–80k spawn on static-change majority | S |
| 2.6 | **Doc claims caching that doesn't exist.** `OPERATIONAL_COST.md:39` lists "prompt caching across passes" as an active lever; there is none (no `--resume`). Tuning off this doc over-credits phantom savings. | `OPERATIONAL_COST.md:39` vs `runner.ts:84` | Correct the doc to "prefix-only caching until session reuse lands." | — | S |

**Note:** 2.1, 2.2, 2.4 collapse into one change — **cross-stage session
continuity**. Do that first; it's the lever the whole lifecycle hangs on.

---

## Principle 3 — Intent-library method (the biggest conceptual gap)

**Already shipped (credit):** the deterministic triage bridge (risk rubric →
krill flags) works and is genuinely good. The consensus planner with persona
routing exists. **But the verdict is blunt: whale _re-derives_ your intent every
run — it does not capture-and-reuse it.** Every intent signal it records is
write-only, read solely for UI badges.

| # | Gap | Evidence | Fix | Effort |
|---|---|---|---|---|
| 3.1 | **There is no distiller.** The "living CONTEXT.md" is written exactly twice — a one-shot repo audit (onboard) and a manual UI PUT — and **never by the dump pipeline**. Raw dumps, your recurring WHYs, refine/reject signals are never folded in. CONTEXT.md is a code summary, not an intent store. `grep distill src/` = empty. | `context-store.ts:91` (sole writer), callers `pipeline.ts:106` (onboard) + `api/context/route.ts:25` (manual) | Build the real distiller: after each plan run, fold served dumps + refine/reject signal into CONTEXT.md under **Decisions / Standing principles / Open questions** — append-and-merge, not regenerate. **Biggest single intent-capture win.** | M |
| 3.2 | **The planner is contractually symptom-level.** "Every WORK REQUEST must yield at least one task"; bench decomposes into "the smallest shippable tasks." It is *forbidden* from stepping back to ask "what class of problem is this." A recurring build break becomes N patch-tasks, never "this reveals a missing CI gate." | `stages.ts:246-254`, `consensus.ts:263`, `stages.ts:237` | Add an **altitude pass** before propose: Caio (or a "systemic" lens) classifies each dump SYMPTOM vs CAUSE and may emit one root-cause task that supersedes the per-dump patches, recorded as a principle in CONTEXT.md. | M |
| 3.3 | **Triage has no symptom-vs-cause axis.** A recurring trivial patch and a one-off trivial patch get the identical 🟢 bypass — the system auto-finishes the same class of patch forever without surfacing "you keep patching X." | `stages.ts:325-381` | Add a counter keyed on label/class: "Nth task of this class → candidate cause-fix," routed to human review regardless of risk tier. | S |
| 3.4 | **The override-rate eval is unimplemented.** `PLAN.md §9` calls override rate "the single metric that governs autonomy." Nothing measures it. `reject()` is a bare status flip, never counted, never fed back. The dial is moved by hand. | `pipeline.ts:324-326`; `grep override.rate src/` = empty | Count reject/refine/manual-flag-change per plan run; expose a rate; feed it to the distiller (high rate → context too thin) instead of only your hand on the dial. | M |
| 3.5 | **Refine discards the WHY.** Input re-plans one task and appends to `refine_log` — but `refine_log` is never read by any planner or distiller (only a UI count badge). Next run re-derives from scratch and can re-propose the exact thing you just redirected away from. | write `pipeline.ts:334-346`; sole reader `whale-app.tsx:1026` (`.length`) | On refine, extract the **principle** behind the redirect and persist it to CONTEXT.md / a `principles` table; at minimum feed `refine_log` into the next plan's context. | M |
| 3.6 | **consensus_log is write-only.** The "who proposed what and why" transcript is captured but never reused to improve routing — Caio cold-starts every run instead of learning it keeps mis-routing a class of dump. | write `stages.ts:319`; sole reader `whale-app.tsx:1114` | Feed prior-run owner/nomination patterns per project into Caio's nominate step so routing compounds. | S |
| 3.7 | **Docs oversell.** ⚠ **Corrected 2026-07-08**: PLAN.md yes (`:12-13,:90,:106-108,:189-190` sell the nonexistent distiller); README is **fine** — it attributes context to onboarding and never claims a distiller, only oversells "living". | `PLAN.md:12-13,90,106-108,189-190` vs code | Correct PLAN.md (tracker C8); README needs no change. | S |

**This is where your own principle bites hardest.** You wrote
[intent-library-method](docs/principles/intent-library-method.md) — capture WHY,
reuse it, compress repeated transfer toward zero — and built it into *your*
CLAUDE.md this very session. whale, the machine whose entire job is to hold your
intent so you stay high-level, **throws that intent away after every run.** Close
3.1 + 3.5 and whale starts doing for itself what you just did for yourself.

---

## Principle 4 — Instruction-file voice is load-bearing

**Already shipped (credit), and this one is genuinely strong by architecture:**
personas inject **verbatim** everywhere (`persona-loader.ts:51-60`,
`consensus.ts:255`); the plan→implement handoff is pinned to the full `plan` with
a **byte-identity regression test** so the lossy `plan_summary` never drives
downstream work (`mcp-tools.ts:137`, `plan-summary.test.ts:33`); CONTEXT.md is
reference-only with an explicit "do not restate" guard; prompts are directive, not
over-compressed. The obvious voice-stripping trap is designed around.

| # | Risk | Evidence | Fix | Effort |
|---|---|---|---|---|
| 4.1 | **No A/B / voice-regression harness.** Coverage is structural only; nothing compares *model behavior* before/after a persona or prompt edit. Personas **hot-reload** (`getTeam`), so a voice-stripping edit ships live with zero gate — exactly the failure mode you already hit once (the 19% compression that inspected clean but A/B-garbled). | `team.ts:4-5` (live reload, no gate); absence across `whale/tests`, `krill/tests` | Add a small **golden-output A/B harness**: freeze representative dumps, snapshot persona/plan outputs, diff (semantic or human spot-check) on any persona/prompt change. | M |
| 4.2 | **`planSingle` control gets labels, not voice.** The single-planner A/B control injects only name/area roster lines, while the consensus path injects each full `systemPrompt` — an unfair voice asymmetry between the two planner modes. | `consensus.ts:388-399` vs `:255` | If `planSingle` is meant as a fair control, inject the relevant personas' full context, not just labels. | S |
| 4.3 | **Onboard audit normalizes (low risk today).** It distills a *codebase*, not human prose, so no first-person WHY is at stake now — but if you ever route human dumps through an LLM into CONTEXT.md (see 3.1), pass them **verbatim**, don't let the audit normalize the voice away. | `pipeline.ts:98-106` | When building the distiller, preserve the user's own words for intent; structure around them, don't rewrite them. | S |

---

## Prioritized roadmap

> ⚠ **Superseded 2026-07-08** by the *Revised P0* in the Verification pass and
> the *Implementation tracker* at the end of this document. Kept for history.

Sequenced by leverage. Each tier is independently shippable.

### P0 — the three that matter most
1. **krill: cross-stage session continuity** (2.1 + 2.2 + 2.4). One warm
   `--resume` session per task chain. **40–70% lifecycle token cut**, the biggest
   single lever. (L)
2. **krill: generalize the VERIFY brake into one "always-conclude" primitive**
   (1.1, 1.2, 1.4, 1.5, 1.6 + a force-conclude scanner for 1.3). Closes the ~30%
   "doesn't conclude" gap — the [pipeline-self-resolves](docs/principles/pipeline-self-resolves.md)
   class fix the VERIFY patch should have been. (M)
3. **whale: build the distiller + intent store** (3.1 + 3.5). Fold dumps and
   refine WHYs into a living CONTEXT.md; stop re-deriving your intent every run.
   The [intent-library-method](docs/principles/intent-library-method.md) made real
   in the machine. (M)

### P1 — altitude + cheap wins
4. whale: altitude pass in the planner + "Nth-of-class → cause-fix" triage flag (3.2, 3.3). (M/S)
5. krill: cheap-first model ladder for AI-REVIEW + escalation resolver, metered (2.3). (M)
6. whale: implement the override-rate metric and feed it back (3.4). (M)
7. krill: static-sufficient VERIFY skip (2.5). (S)

### P2 — hardening + hygiene
8. A/B / voice-regression harness across whale + krill (4.1). Gate persona/prompt edits. (M)
9. krill: orphaned-worktree GC (1.8), resolver-in-live-repo guard (1.7), escalation lifetime cap (1.4). (S each)
10. Doc truth pass: `OVERVIEW.md:281` stuck design (1.9), `OPERATIONAL_COST.md:39` caching claim (2.6), `PLAN.md`/`README` distiller claim (3.7); `consensus_log` reuse (3.6); `planSingle` fairness (4.2). (S each)

---

## One-line scorecard

| Principle | Where the fleet stands |
|---|---|
| Pipeline self-resolves | **~70%.** Concludes on AI-judgment; loops/strands on crash, hang, or no-verdict. VERIFY fix never generalized. |
| Token economics span sessions | **Per-call only.** Metered but re-derives the same bytes 3–5×. Session reuse unbuilt. |
| Intent-library method | **Re-derives every run.** No distiller; every intent signal is write-only. The biggest gap. |
| Instruction voice load-bearing | **Strong by architecture, exposed procedurally.** Verbatim everywhere, but no regression gate on hot-reloaded personas. |

The through-line: **stop re-deriving, start capturing-and-reusing** — at the token
layer (sessions) and the intent layer (distiller). That is your own principle set,
turned on the fleet that's supposed to embody it.

— Caio (AI/Orchestration). Evidence traced from source on 2026-06-26; `file:line`
refs are to current `whale`/`krill` HEAD.

---

## Verification pass — 2026-07-08

Four independent read-only agents re-traced every claim against live source
(whale HEAD `cd4335e` — unchanged since audit; krill HEAD `8964923` — +5
bug-fix commits, no roadmap item consumed, no citation invalidated). Diagnosis
mostly holds; **the P0 plan needed surgery.** Corrections:

### Corrected claims

- **1.1 was wrong for 2 of 3 stages.** PLANNING and IMPLEMENTING drive their own
  transitions in code after the runner returns (`planning.ts:76-88`,
  `implementing.ts:161-171`) — they always conclude on a normal exit. Only
  **AI-REVIEW** is model-gated like VERIFY (`ai-review.ts:43-64`; transition
  depends entirely on the model calling `task_decide`). PLANNING/IMPLEMENTING's
  real loop is the **throw/timeout path** (comment + release + rethrow, no
  counter) — a different bug needing a retry-on-throw counter, not a no-verdict
  brake.
- **The "one shared primitive for every stage" fix was over-generalized.**
  PUBLISHING already brakes (`countPublishFailures` MAX=3 → park at
  `NEEDS_REVIEW(deliverable)`, `publishing.ts:54-64,195`, plus the
  `tripAutoFinishBreaker` project circuit breaker); the escalation **resolver**
  already always-concludes (`escalation.ts:107-132` defers to human on
  no-decision). Uncapped part is only `task_escalate` re-arming. 1.6 is bounded
  by the shared brake — "no dedicated counter" true, "can loop" overstated.
- **P0-1 (`--resume` session continuity) is not viable as written.** Three
  blockers found in the runner: (a) session id never captured
  (`parseRunUsage`, `runner.ts:44-61` discards it) — fixable; (b) **per-stage
  model switching collides with resume** — one warm session forces one model
  for the whole chain, fighting 2.3's Opus/Sonnet split; (c) **stage-scoped MCP
  auth breaks it** — tokens minted per `{taskId, stage}`, revoked in `finally`
  after each spawn, tools authorize by stage (`task_verify` invalid under an
  `ai_review` token). Resume means reworking the security model, not adding a
  flag. And the economics likely invert: stage prompts are user turns, so a
  resumed chain accumulates every prior stage's transcript; cron gaps blow the
  5-min cache TTL → cache-*creation* re-paid on a much larger context each
  stage — plausibly **more** than today's bounded cold spawns. Demoted to a
  design spike.
- **2.1's framing missed an existing lever.** `--exclude-dynamic-system-prompt-sections`
  (`runner.ts:104-108`) deliberately keeps the system prefix static and
  cache-hittable — dynamic-content-via-tool-results is by design, not pure
  defect. Cron stagger is fixed 10s slots on a 60s cycle, not "10–60s".
- **3.7 half-right.** PLAN.md sells the nonexistent distiller (`:90,:106-108,
  :189-190`); README correctly attributes context to onboarding and never
  claims a distiller — only oversells "living".
- **Whale's token economics were never audited.** `whale/src/lib/runner.ts` has
  the identical cold-spawn pattern (output-format `text` — can't even capture a
  session id today), and the consensus planner fans out multiple Opus/Sonnet
  calls per plan run. A surface at least as expensive as krill's, absent from
  this audit. Added as a work item.
- **P0-3 distiller has an unhandled destructive interaction.** `onboard()` and
  the manual PUT both whole-file-**replace** CONTEXT.md (`context-store.ts:93`);
  the "context stale — re-audit" UX encourages clobbering any folded
  Decisions/Principles. Onboard must become merge-aware or the distiller erases
  its own memory. Also: keep principles in the markdown file, not a DB table —
  whale's runtime **never migrates** (schema changes need a manual
  `db:migrate`), and CONTEXT.md auto-feeds the planner for free. The altitude
  pass (3.2) collides with `setEntriesPlanError` (`stages.ts:98-103`): a
  deliberately-superseded dump would be mislabeled a plan failure unless
  `markEntries` learns a "planned-by-parent" case. Provenance caveat:
  `source_entry_id` falls back to `reqs[0]` (`stages.ts:300-301`) — best-effort,
  can misattribute.

### New defects found (not in original audit)

- **Stuck scanner ignores `claimed_until`** (`stuck.ts:47-56`) — contradicts
  its own docstring and `OVERVIEW.md:281`; flags actively in-flight tasks as
  stuck, producing false noise. Pre-existing bug, independent of notify-only.
- **Uncredited safeguards**: `repoMissingBlock` preflight, empty-branch parks
  (implementing + publishing), implementing's post-run try/catch claim release.
  The "always-conclude" gap is narrower than the audit scored.

### Revised P0 (supersedes the roadmap above)

1. **krill: force-conclude scanner + AI-REVIEW brake + retry-on-throw** —
   replaces old P0-2. The scanner (teeth on `runStuckScanner`: force-release +
   park + `pauseLineForHuman` after a hard age cap) is one backstop catching
   *every* non-concluding path regardless of stage. Test net exists
   (`verify.test.ts:228`, `loop-brake.test.ts:66`).
2. **krill token cuts, resequenced** — replaces old P0-1: persist **diff text**
   at end of IMPLEMENTING and feed it inline to REVIEW/VERIFY (kills the 2-3×
   re-diff, no architecture change); cheap-first **model ladder** for
   AI-REVIEW + resolver with decline-flip metering; static-sufficient VERIFY
   skip. Session continuity → design spike only.
3. **whale: distiller + intent store** — kept, with three constraints:
   merge-aware onboard first, markdown-only store, separate hook in
   `refine()`/`reject()` (that signal doesn't exist at plan time).
4. **New: audit whale's token economics** (consensus fan-out cost unmeasured).

---

## Implementation tracker

> Reviewed by Caio 2026-07-08: approved with 4 changes, all applied — (1) eval
> criterion per tier, (2) C6 resequenced before the distiller (eval before
> scale), (3) A4 gated on observed evidence, (4) effort ratings restored.
> Plus: **live-fire checkpoints** — planned stops where implementation pauses
> and a real case runs through whale → krill to watch both systems tackle it.

Status legend: ⬜ **TODO** · 🟨 **IN PROGRESS** · ✅ **DONE** · 🚧 **GATED** (needs evidence from a checkpoint before it's armed)

### Live-fire checkpoints (the stop-and-watch intervals)

Each checkpoint = pause coding, run a **real case** end-to-end (real dump →
whale plan → push → krill stages → PR), watch both systems, collect numbers.
No checkpoint passes on green tests alone — the A1 lesson: tests run source,
the server runs the build; observe the *running fleet*.

| Status | ID | When | What runs / what we watch |
|---|---|---|---|
| ⬜ TODO | LF-0 | **Before any code** | Baseline. One representative task end-to-end. Collect: per-stage tokens from `stage_usage` rollups, wall-clock per stage, any stall/park events. This is the number every B-tier claim gets judged against — without it, savings are vibes (Caio). |
| ⬜ TODO | LF-1 | After A1+A2+A3 | Resilience run. Real case + watch the scanner's park log: healthy in-flight task must NOT be flagged (A2 proof); if anything hangs, it must conclude at the cap, not loop. **Gate decision:** A4 arms only if this log shows planning/implementing throw-loops actually occurring. |
| ⬜ TODO | LF-2 | After B1+B2+B3 | Cost run. Same class of task as LF-0, compare `stage_usage` vs baseline. Watch: AI-REVIEW/VERIFY input drop, decline-flip rate flat (B2 quality guard). Decide here whether the B4 spike is worth scheduling. |
| ⬜ TODO | LF-3 | After C1+C6 | Metric run. Plan real dumps, refine/reject as normal on the Proposed tab, confirm override-rate numbers actually appear per plan run and survive a re-onboard (C1 proof). |
| ⬜ TODO | LF-4 | After C2+C3 | Intent run. Check CONTEXT.md gained folded Decisions/Principles; refine a task with a clear WHY, run the next plan — it must **not** re-propose the redirected work. Override rate from LF-3 is the before-number. |

### Tier A — krill: pipeline always-concludes (revised P0-1)

**Eval (Caio):** zero tasks in a non-concluding state past the hard cap,
measured by the scanner's own park log — and zero false-parks of
actively-claimed healthy tasks. Verified live at **LF-1**.

| Status | ID | Item | Why | Effort |
|---|---|---|---|---|
| ⬜ TODO | A1 | **Force-conclude scanner** — upgrade `runStuckScanner` from notify-only to force-release + park at `NEEDS_REVIEW(stuck)` + `pauseLineForHuman` after hard age cap (`k·max_stage_duration` or N observations) | One backstop catches *every* non-concluding path (AI-REVIEW no-verdict, throw-loops, orphaned claims) regardless of stage — highest leverage, smallest change | M |
| ⬜ TODO | A2 | **Fix stuck scanner `claimed_until` bug** — filter out actively-claimed tasks (`stuck.ts:47-56`) | Scanner currently flags in-flight tasks as stuck; contradicts its own docstring and `OVERVIEW.md:281`; A1 with teeth would force-kill healthy work without this | S |
| ⬜ TODO | A3 | **AI-REVIEW incomplete brake** — mirror VERIFY's episode-scoped `[ai-review-incomplete]` counter → park at `NEEDS_REVIEW(declined)` after max cycles | Only remaining model-gated stage; a no-verdict run re-picks forever at full **Opus** cost each loop — cost-justified ahead of the scanner's slower age cap (3–5 Opus spawns would burn before A1 trips); proven pattern + existing test net | M |
| 🚧 GATED | A4 | **Bounded retry-on-throw for PLANNING/IMPLEMENTING** — episode-scoped attempt counter on the timeout/exception path → park after N. **Gate: build only if LF-1's park log shows these throw-loops actually occurring** | Their transitions are code-driven (no no-verdict loop); the throw-loop is theoretically real but has zero observed occurrences — don't build brakes for loops nobody has seen (Caio). A1 concludes them meanwhile | S |
| ⬜ TODO | A5 | **Escalation lifetime cap** — track `escalation_count` per task; after max, `pauseLineForHuman` instead of re-running the resolver | `task_escalate` resets `resolver_tried:false` every call (`mcp-tools.ts:521-527`) — escalate→resolve→re-escalate can cycle indefinitely (resolver itself already concludes) | S |
| ⬜ TODO | A6 | **Orphaned-claim boot scanner** — on boot + periodically, force-release claims where `claim_gen != getBootId()` | A dead process strands its claim up to 30 min TTL; `claim_gen` already identifies unambiguously-dead claims but nothing consumes it beyond UI badges | S |
| ⬜ TODO | A7 | **Orphaned-worktree GC** — boot-time + periodic sweep of worktrees with no matching active task | `removeWorktree` only fires on clean transitions (`cleanup.ts:42`); crashes/deletions leak disk and can collide with `ensureWorkspace` on retry | M |
| ⬜ TODO | A8 | **Resolver live-repo guard** — if no worktree/workspace exists, defer to human; never run with the live project folder as cwd | `escalation.ts:77-80` falls back to the real repo — an Opus run can mutate production code outside any worktree | S |
| ⬜ TODO | A9 | **Episode-scope the shared loop-brake** — count stage-tagged markers since `stage_entered_at` in `countAiAutoActions` | Current counter is cross-stage/cross-episode (`loop-brake.ts:19-36`): planning/escalate comments inflate the AI-REVIEW brake → premature or missed parks | M |
| ⬜ TODO | A10 | **Spec truth pass: `OVERVIEW.md:281,316`** — replace "log + notify, no auto-retry loop" with the bounded brake→park design | The spec actively codifies the notify-only behavior A1 removes; leaving it invites regression to the old design | S |

### Tier B — krill: token cuts (revised P0-2)

**Eval (Caio):** before/after tokens-per-task-lifecycle from the existing
`stage_usage` rollups. Baseline captured at **LF-0**, compared at **LF-2** on
the same class of task. Quality guard: decline-flip rate must stay flat after
B2. No baseline → no B-tier work starts.

| Status | ID | Item | Why | Effort |
|---|---|---|---|---|
| ⬜ TODO | B1 | **Persist diff text** — store the unified diff at end of IMPLEMENTING (it's already computed); feed it inline to AI-REVIEW + VERIFY prompts instead of "re-run git diff" | Diff text is re-derived and re-tokenized 2-3× per task (`ai-review-dev.md:7`, `verify-dev.md`); cheapest real cut, no architecture change | M |
| ⬜ TODO | B2 | **Cheap-first model ladder** — Sonnet first-pass for AI-REVIEW (approve obvious-clean, escalate ambiguous to Opus); resolver on Sonnet, Opus only on defer; **meter the decline-flip rate** as quality guard | Opus pinned unconditionally on AI-REVIEW + every resolver fork (`model-map.ts:5-16`, `escalation.ts:88`) at ~5× Sonnet; metering makes the quality tradeoff observable instead of assumed | M |
| ⬜ TODO | B3 | **Static-sufficient VERIFY skip** — AI-REVIEW emits a signal that skips the dynamic VERIFY spawn for low-blast-radius static diffs | Only docs-only auto-skips today (`implementing.ts:134-145`); every static code change pays a full spawn AI-REVIEW just cleared | S |
| 🚧 GATED | B4 | **Session-continuity design spike (not implementation)** — blockers, viable variants (V1 retry-resume … V5 extended TTL), and honest gains are written up in [`docs/session-continuity.md`](docs/session-continuity.md). **Gate: scheduled only if LF-2 shows B1–B3 left a gap worth the redesign; start with V1 (retry-loop resume) if retries still dominate** | The audit's biggest claimed lever (40-70%) doesn't survive contact with the runner: model pinning, per-stage auth tokens, and TTL-blown accumulating context plausibly make naive resume cost *more*. Constrained same-model variants remain viable | M |
| ⬜ TODO | B5 | **Doc truth pass: `OPERATIONAL_COST.md:39`** — "prompt caching across passes" → "static-prefix caching intra-spawn; no cross-pass session reuse" | Tuning decisions made off this doc credit phantom savings | S |

### Tier C — whale: intent capture (P0-3, constrained)

**Eval (Caio):** the override rate itself (C6) — which is why C6 now lands
**before** the distiller, not after. Target after C2/C3: override rate drops
across plan runs, and "re-propose what was just refined away" incidents hit
zero. Measured live at **LF-3** (metric exists) and **LF-4** (metric moves).
Order within the tier: **C1 → C6 → C2 → C3** — measure first, then change
what's measured.

| Status | ID | Item | Why | Effort |
|---|---|---|---|---|
| ⬜ TODO | C1 | **Merge-aware onboard** — `onboard()` + manual PUT must preserve Decisions / Standing principles / Open questions sections instead of whole-file replace | Prerequisite for C2/C3: the "context stale — re-audit" UX otherwise **erases the distiller's memory** every re-onboard (`context-store.ts:93` replaces the file) | M |
| ⬜ TODO | C6 | **Override-rate metric** — crude first cut off existing columns (refine_log lengths + rejected rows per `plan_run_id`); append-only events table later for reject-overwrites and pre-push flag changes | PLAN.md §9 calls this "the single metric that governs autonomy"; nothing measures it — the dial moves by hand. **Resequenced before C2/C3 (Caio): it's the eval for the whole tier — ship the ruler before the thing it measures.** Crude version needs no migration | S (crude) / M (events table) |
| ⬜ TODO | C2 | **Distiller** — after each plan run (end of `plan()`, `stages.ts:104`), fold served dump text + outcomes into CONTEXT.md via append-and-merge; markdown store only, no DB table | The core gap: whale re-derives intent from raw dumps every run; CONTEXT.md is a static repo audit today. Markdown auto-feeds the planner for free and dodges the runtime-never-migrates trap | M |
| ⬜ TODO | C3 | **Refine/reject principle capture** — hook in `refine()`/`reject()` (`pipeline.ts:324-346`): extract the WHY behind the redirect via a small LLM call, persist to CONTEXT.md | `refine_log` is write-only (sole reader: a UI badge count) — the next plan run can re-propose exactly what was just redirected away; this signal doesn't exist at plan time so C2 alone can't catch it | M |
| ⬜ TODO | C4 | **Altitude pass in planner** — pre-propose step classifies dumps SYMPTOM vs CAUSE, may emit one root-cause task superseding per-dump patches; wire a "planned-by-parent" case into `markEntries` | Planner is contractually symptom-level ("every request must yield ≥1 task", `stages.ts:246-254`); without the `markEntries` case, a superseded dump trips `setEntriesPlanError` and reads as a failure. Lands after C6 so its effect on override rate is observable | M |
| ⬜ TODO | C5 | **Nth-of-class triage flag** — counter keyed on task class; Nth recurrence → route to human review as cause-fix candidate regardless of risk tier | Triage is pure keyword regex on single-task text (`stages.ts:325-342`) — the system auto-bypasses the same trivial patch forever without surfacing "you keep patching X" | S |
| ⬜ TODO | C7 | **Feed `consensus_log` into nominate** — prior-run owner/nomination patterns per project into Caio's routing step | Routing cold-starts every run (`consensus_log` written at `stages.ts:319`, read only by the UI trail) — mis-routing a class of dump never compounds into learning | S |
| ⬜ TODO | C8 | **Doc truth pass: PLAN.md** — distiller claims at `:12-13`, `:90`, `:106-108`, `:189-190` (README is fine — attributes context to onboarding) | The doc sells a "living distiller" that doesn't exist; until C2 ships, planning off PLAN.md assumes phantom capability | S |

### Tier D — cross-cutting / hardening

**Eval (Caio):** D1's deliverable *is* numbers (per-plan-run cost of the
consensus fan-out). D2 passes when the harness catches a deliberately
voice-stripped persona edit that visual inspection would clear.

| Status | ID | Item | Why | Effort |
|---|---|---|---|---|
| ⬜ TODO | D1 | **Audit whale's token economics** — meter the consensus fan-out (multiple Opus/Sonnet cold spawns per plan run, `consensus.ts`); switch runner to `--output-format json` for usage/session capture | Blind spot: whale has the same cold-spawn pattern as krill plus a multi-call planner, and its cost was never measured — can't prioritize cuts without numbers | M |
| ⬜ TODO | D2 | **Voice A/B regression harness** — freeze representative dumps, snapshot persona/plan outputs, diff on any persona/prompt change | Personas hot-reload live with zero gate (`team.ts:4-5`); a voice-stripping edit ships instantly — the exact failure mode already hit once (the 19% compression that inspected clean but A/B-garbled) | M |
| ⬜ TODO | D3 | **Document `planSingle` as a deliberately-thin baseline** — a comment + doc line; do NOT fatten the control arm (Caio: it's thin by design) | Control injects name/area lines while consensus injects full persona context (`consensus.ts:388` vs `:255`) — undocumented, any A/B conclusion confounds "consensus vs single" with "voice vs no voice"; documenting the asymmetry is the whole fix | S |

### Sequencing (with the stop-and-watch intervals)

```
LF-0 baseline run (no code yet — capture stage_usage numbers)
  │
  ├─ Phase 1: A1 + A2 (backstop + its safety bug) → A3 (Opus-loop brake)
  │
LF-1 resilience run ──▶ gate decision: arm A4? (only if throw-loops observed)
  │
  ├─ Phase 2: B1 → B2 → B3 (token cuts; A5-A10 parallelizable here)
  │
LF-2 cost run ──▶ compare vs LF-0; gate decision: schedule B4 spike?
  │
  ├─ Phase 3: C1 (merge-aware onboard) → C6 (the ruler)
  │
LF-3 metric run ──▶ override rate visible + survives re-onboard
  │
  ├─ Phase 4: C2 (distiller) → C3 (refine WHY capture)
  │
LF-4 intent run ──▶ CONTEXT.md folds; no re-propose-after-refine; rate moves
  │
  └─ Phase 5: C4, C5, C7, C8 + D-tier (D1 anytime; D2 before next persona edit)
```

Self-edit guard applies to every item: all of these route through krill as
reviewed PRs, never merged unattended. Every phase ends with **build +
restart** before its LF run — a merged-but-stale server invalidates the
observation (the A1 lesson).
