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
| 1.1 | **No-verdict runs loop forever.** AI-REVIEW / PLANNING / IMPLEMENTING have no incomplete-run counter. A run that exits without driving a transition is re-picked next tick, forever. AI-REVIEW is worst — full **Opus** cost each loop. | `ai-review.ts:54-57`, `planning.ts:60-65`, `implementing.ts:64-69` vs `verify.ts:99-163` | Extract VERIFY's brake into a **shared primitive**; each stage logs an episode-scoped `[<stage>-incomplete]` marker and parks at `NEEDS_REVIEW` after `max_ai_decline_cycles`. | M |
| 1.2 | **Stuck detection is notify-only.** A task hung past `max_stage_duration` emits an SSE event and waits; the only "recovery" is TTL lapse → re-pick → re-hang. Infinite retry, not conclusion. | `stuck.ts:72-86` (comment: "no auto-recovery"), `cron.ts:82-90` | After N stuck observations (or `age > k·max_stage_duration`), force-conclude: `forceReleaseClaim` + `NEEDS_REVIEW(stuck)` + `pauseLineForHuman`. | M |
| 1.3 | **Orphaned claims wait up to 30 min.** A process that dies mid-stage strands its claim until TTL (1800s) or a human clicks Recover. No dead-process scanner. | `boot-id.ts:9-10`; `forceReleaseClaim` sole caller is the UI route `api/tasks/[id]/recover/route.ts:24` | Boot-time + periodic scanner force-releases claims where `claim_gen != getBootId()` (unambiguously dead) → next tick re-picks immediately. | S |
| 1.4 | **Escalation has no lifetime cap.** `task_escalate` resets `resolver_tried:false` each time, so escalate → auto-resolve → back-to-stage → re-escalate can cycle indefinitely. | `mcp-tools.ts:504-510`, `escalation.ts:46-72` | Track `escalation_count`; after `max_ai_decline_cycles` go straight to `pauseLineForHuman` instead of re-running the resolver. | S |
| 1.5 | **Loop-brake counts comment volume, not episodes.** `countAiAutoActions` counts all AI comments since the last human comment — cross-stage, not episode-scoped. Can mis-trip (premature park) or never reset. | `loop-brake.ts:19-36`, consumed at `mcp-tools.ts:372,442`, `publishing.ts:384` | Count stage-tagged, episode-scoped markers (`since stage_entered_at`), like VERIFY's own counter. | M |
| 1.6 | **Publishing conflict can loop.** The non-tripped branch retries with no dedicated attempt counter; if a resolve run appends no AI comment, the counter never advances. | `publishing.ts:383-407` | Add a `[publish-conflict-attempt]` episode counter parallel to `countPublishFailures`; park after MAX regardless of comment side-effects. | S |
| 1.7 | **Resolver can run in the live repo.** If the worktree is gone but the task is `NEEDS_REVIEW(question)`, the resolver runs Opus in the real project folder as fallback cwd — can mutate outside a worktree. | `escalation.ts:77-80` | If no worktree/workspace exists, defer to human; never execute in the live repo. | S |
| 1.8 | **No orphaned-worktree GC.** Worktrees are removed only on a clean transition; a dead-process or deleted-task worktree leaks disk and can collide with `ensureWorkspace` on retry. | `cleanup.ts:42` (sole `removeWorktree` caller) | Boot-time + periodic GC: drop worktrees under `worktrees_root` with no matching active task. | M |
| 1.9 | **Spec endorses the wrong design.** `OVERVIEW.md:281,316` still codify "log + notify, no auto-retry loop" for stuck tasks — the spec actively contradicts the VERIFY fix. | `OVERVIEW.md:281,316` | Update the spec to mandate the VERIFY pattern (bounded brake → park → pauseLine) for every stuck-eligible stage. | S |

**The class fix (do this, not 1.1–1.9 one by one):** build **one** "always-conclude"
primitive — episode-scoped attempt counter + brake + park + `pauseLineForHuman` —
and apply it to every stage and to a force-conclude scanner. That's the
[pipeline-self-resolves](docs/principles/pipeline-self-resolves.md) move: fix the
class. Generalizing VERIFY closes 1.1, 1.2, 1.4, 1.5, 1.6 at once.

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
| 2.1 | **Every stage is a cold spawn — no session reuse.** No `--resume`/`--continue`. The expensive input (diff, files, plan, comments) is re-tokenized full-price in PLAN→IMPL→REVIEW→VERIFY→resolver. Cron stagger (10–60s) blows the 5-min cache TTL, and dynamic content arrives via tool results (not the cached prefix) so it can't hit cache anyway. | `runner.ts:84-114`, `cron.ts:40-100` | Carry **one warm session** across a task's stage chain via `--resume <session_id>` (persist session id on the task). Bytes tokenized in IMPLEMENTING become cache-reads (0.1×) in REVIEW/VERIFY. | **40–70%** of input on AI-REVIEW + VERIFY + resolver — the single biggest lever | L |
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
| 3.7 | **Docs oversell.** PLAN.md/README sell a "living distiller" that maintains context "from real ground." It doesn't exist; CONTEXT.md is a static audit with a staleness sidecar. | `PLAN.md:90,107-108`, `README.md:5,32,41` vs code | Build the distiller (3.1) or correct the docs. Don't ship the false claim. | S |

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
