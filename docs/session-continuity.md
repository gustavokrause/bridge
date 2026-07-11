# Session continuity (`--resume`) in krill — design record + what shipped

> Companion to tracker item **B4** in [`FLEET-PRINCIPLES-AUDIT.md`](../FLEET-PRINCIPLES-AUDIT.md).
> Status: **BUILT 2026-07-10 — V1 + V2 + event-driven chaining.** The original
> "wait for volume" decision assumed dollars were the binding resource; in
> practice the fleet runs on a Claude subscription and was **burning the
> session window** — the quota-headroom trigger fired at once, not at 50
> tasks/day. Shipped scope and the A/B method are at the end of this doc; the
> analysis below is the design record (V3's first-review resume stays
> deliberately rejected — self-review).

## The idea

Every krill stage spawns a cold `claude` process (`runner.ts:84-119`). The
diff, plan, files, and comments get re-tokenized at full price in each of
PLAN → IMPLEMENT → AI-REVIEW → VERIFY → resolver. `--resume <session_id>`
would carry one warm session across the chain, so bytes tokenized once become
prompt-cache reads (~0.1×) downstream. The original audit called this the
single biggest lever (40–70%). Verification killed that number.

## Why the naive version doesn't work

1. **Session id is discarded.** `parseRunUsage` (`runner.ts:44-61`) reads only
   usage/cost from the `--output-format json` envelope; the `session_id` field
   is never persisted. Fixable in an afternoon — listed only because the plan
   assumed it already existed. (whale's runner now captures session_id in its
   usage rows — precedent exists; krill still discards it.)
2. **Prompt cache is per-model; stages switch models.** `model-map.ts` pins
   Opus on PLANNING and Sonnet on IMPLEMENTING/VERIFY; AI-REVIEW ladders —
   Sonnet first pass, **Opus on contested re-reviews** (B2). A resume across
   a model boundary gets **zero** cache benefit — the accumulated transcript
   is re-tokenized at full input price on the new model. The savings only
   ever existed for same-model hops.
3. **Stage-scoped MCP auth is incompatible as-is.** Tokens are minted per
   `{taskId, stage}` (`mcp-auth.ts:19-32`), revoked in `finally` after each
   spawn, and tools authorize by stage (`task_verify` is invalid under an
   `ai_review` token). A resumed session's token and `--mcp-config` file are
   dead by the next stage. Solvable (krill owns this auth model — see
   variants), but it's a design change, not a flag.
4. **TTL economics invert on krill's real schedule.** Prompt cache lives 5
   minutes; stages are picked by cron ticks minutes apart. A resumed chain
   that misses the TTL pays cache-**write** on an ever-growing transcript each
   stage — plausibly **more** than today's bounded cold spawns.
5. **Cold spawns are partly a feature.** AI-REVIEW resuming the implementer's
   own session reviews with the implementer's context and biases — independent
   review dies. Fresh-context review is quality architecture, not just cost.

## Variants that could make it work

Ordered by feasibility. All assume the session-id capture fix (trivial) and a
fresh stage-scoped `--mcp-config` re-issued per resumed run (krill mints its
own tokens, so this is local work — verify in the spike that `--resume`
accepts `--mcp-config` and `--model` overrides).

### V1 — Retry-loop resume (same stage, same model, same role)
On AI-REVIEW decline → IMPLEMENTING retry, or VERIFY fail → re-verify, resume
the **previous attempt's own session** and feed only the delta (decline
reason / failing assertion). Same model, same role (no independence loss),
and the retry usually happens minutes after the original — closest to the TTL
window. **Gain: 50–70% per retry cycle. Highest value, lowest risk.**

*Revised after the B2 ladder shipped:* the ladder narrowed V1's scope. A
task's first review runs Sonnet and a **contested re-review runs Opus** — so
resuming a declined review's own session now crosses a model boundary (zero
cache value) *and* the cold Opus fork is deliberate quality architecture
there. V1 remains clean only for IMPLEMENTING retries (Sonnet→Sonnet) and
VERIFY retries (Sonnet→Sonnet). The "400k–1M tokens per decline cycle" worst
case in `OPERATIONAL_COST.md` also predates the ladder — the first observed
post-ladder decline→fix→approve cycle cost $3.50 total, which shrinks what V1
can save in absolute terms.

### V2 — Same-model adjacent pair: IMPLEMENTING → VERIFY
Both run Sonnet today. VERIFY resumes the implementing session: the diff,
files, and plan are already in context. Needs event-driven chaining (trigger
VERIFY immediately on transition instead of waiting for the cron slot) to
stay inside the 5-min TTL. Independence cost is mild — verify checks
behavior, not judgment. **Gain: 20–40% of VERIFY input.**

### V3 — Ladder-enabled full chain (enabler SHIPPED — tracker B2)
B2's cheap-first ladder is live: a task's first review pass runs Sonnet, so
the clean path is now IMPLEMENT → REVIEW → VERIFY **all Sonnet** — a
same-model chain where full resume is coherent, with the Opus contested
re-review as a deliberate cold fork (which also restores independent review
exactly where judgment is contested). V3 is buildable today; what it still
costs is the MCP-auth rework + event-driven chaining (or V5) to stay inside
the cache TTL, and it spends the fresh-eyes benefit of a cold first review.

### V4 — No resume at all: artifact handoff (SHIPPED — tracker B1)
Persist what each stage derived and inject it into the next cold spawn. No
CLI coupling, no auth rework, no TTL dependency, keeps review independence.
Captures a large share of the same win — it removes the re-*derivation*
(tool-call round trips re-reading the repo), which is a real cost even when
tokens can't be cache-read. **Shipped as tracker B1**: the unified diff is
persisted once at IMPLEMENTING end (`diff_text`, capped) and served to
AI-REVIEW/VERIFY via `task_context()` — proven live. Remaining V4 headroom:
a structured stage summary and the verify checklist could ride the same
channel if evidence ever shows stages still re-deriving.

### V5 — Extended cache TTL
The API supports 1-hour cache TTL at a higher write price, which would make
cron-gap resumes viable. Unverified whether the Claude Code CLI exposes it;
check in the spike. If it does, it changes V2/V3's math materially.

## Honest gains table

| Variant | Scope | Estimated gain | Risk / status |
|---|---|---|---|
| V1 retry resume | impl-retry + verify-retry cycles only (ladder made re-reviews an Opus cold fork by design) | 50–70% per retry, but absolute retry cost already fell post-ladder (~$3.50 observed cycle) | Low risk, shrunken prize |
| V2 impl→verify | VERIFY input (minus B3's static skips) | 20–40% | Low-mild (TTL scheduling work) |
| V3 full Sonnet chain | whole clean path | up to ~50% of chain input | Medium; enabler (B2) shipped; costs MCP-auth rework + TTL chaining + cold-first-review benefit |
| V4 artifact handoff | all stages | **shipped** (B1 diff persistence); headroom: stage summary, verify checklist | None |
| V5 1h TTL | multiplier on V2/V3 | removes the scheduling constraint | Unknown (CLI support unverified) |

The blanket "40–70% of lifecycle input" from the original audit is not
recoverable — it assumed cache benefits across model boundaries that cannot
exist. The realistic ceiling is V1+V2 (or V1+V3), and the ladder + B1 + B3
already banked much of what that ceiling was worth.

## Decision history

**2026-07-10, first call (post-LF-2): not scheduled.** Priced in notional
dollars (~$0.10–1.00/task residual after B1–B3), the rework wasn't worth it
at a few tasks/day; the plan was to wait for ~50–100 tasks/day.

**2026-07-10, reversed the same day: BUILT (V1 + V2 + chaining).** New fact:
the fleet runs on the operator's Claude **subscription** — the binding
resource is the plan's session-window quota, not dollars, and it was already
saturating. Token reduction pays immediately at any task volume; the
"quota headroom" trigger effectively fired on day one. The per-task dollar
table above remains correct — it just measured the wrong constraint.

### What shipped (krill, 2026-07-10)

- **Session capture** — every stage run's `session_id` persists per stage on
  the task (`tasks.session_map`, JSON `{stage: {id, model, at}}`).
- **V1 retry-resume** — an IMPLEMENTING redo (decline / verify-fail) resumes
  its own prior implementing session; a VERIFY retry resumes its prior attempt.
- **V2 impl→verify** — VERIFYING resumes the implementing session (both
  Sonnet): diff, files and plan arrive as cache reads instead of re-derivation.
- **Event-driven chaining** — verdict transitions (impl→next stage,
  decline→re-implement, verify-fail→re-implement, approve→verify) kick the
  next stage's tick immediately instead of waiting out the cron slot, keeping
  same-model hops inside the 5-min cache TTL. Fire-and-forget: every tick
  guard (claims, stage_enabled, backoff) still applies and the cron stays the
  fallback.
- **Guards** (policy: `krill/src/claude/resume.ts`) — same-model only (prompt
  cache is per-model), fresh-only (≤300s; past the TTL a resume pays
  cache-write on the whole transcript), **AI-REVIEW never resumes**
  (fresh-eyes review and the contested Opus fork stay cold by design).
  Kill switch: `KRILL_RESUME=0`.
- **The feared MCP-auth rework proved unnecessary** — each resumed spawn gets
  a fresh stage-scoped token and `--mcp-config` like any spawn; the resumed
  transcript only supplies context. Stage-auth boundaries unchanged.
- **A/B instrumentation** — `stage_usage.resumed` marks warm runs; all prior
  rows are the cold baseline. Compare with:
  `SELECT stage, resumed, COUNT(*), AVG(cache_read_tokens),
  AVG(cache_creation_tokens), round(AVG(cost_usd),3), AVG(duration_ms)
  FROM stage_usage WHERE stage IN ('implementing','verify')
  GROUP BY stage, resumed;`

Spike-proven before building: `--resume` composes with `--print`,
`--output-format json`, `--mcp-config`, and same-model re-runs; session id
stays stable and history persists across the resume (~28k cache reads).

### Still deliberately NOT built

- **V3 first-review resume** — the reviewer inheriting the implementer's
  session is self-review; fresh-eyes first review and the cold contested Opus
  fork are quality architecture, and review is the cheapest stage anyway.
- **V5 (1-hour cache TTL)** — CLI support unverified; re-check if chaining
  proves insufficient to stay inside the 5-min window in practice.
- Revisit either only if the A/B rows show warm hops still missing cache
  (chaining too slow) or review spend becomes material.
