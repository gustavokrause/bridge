# Session continuity (`--resume`) in krill — why not now, how it could work

> Companion to tracker item **B4** in [`FLEET-PRINCIPLES-AUDIT.md`](../FLEET-PRINCIPLES-AUDIT.md).
> Status: design notes, no implementation — and after LF-2, **decided: not
> scheduled**. B1 (diff persistence = V4), B2 (review ladder = V3's enabler)
> and B3 (static verify skip) shipped without any resume work and cut the
> Opus share of task cost 87% → 34%; an observed decline→fix→approve cycle
> cost $3.50 total. The remaining addressable spend no longer justifies the
> auth + scheduling rework. Kept as the design record with reopen criteria
> at the end. (2026-07-10 revision: the ladder also reshaped V1 — see below.)

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

## Decision (2026-07-10, post-LF-2)

**Not scheduled.** The checkpoint ran: B1–B3 shipped without any resume work
cut the Opus share of task cost 87% → 34%, VERIFY spawns disappear entirely
for static diffs, and the observed decline cycle cost $3.50 — the spend this
spike would attack no longer justifies the MCP-auth redesign plus TTL-aware
scheduling it requires.

## The volume strategy (why this waits, and when it stops waiting)

The residual gain is real but small **per task**, and the cost is
architectural. Priced at observed numbers (~$4.26/task chains):

| Variant | Realistic saving per task | What it buys that for |
|---|---|---|
| V2 (verify resumes impl session) | ~$0.10–0.15 (verify runs $0.35–0.46; B3 already deletes it for static diffs) | TTL-beating scheduling |
| V1 (retry resume) | only during decline cycles — brakes cap them at 3 and the observed post-ladder cycle cost $3.50 total | session plumbing |
| V3 (full warm Sonnet chain) | **~$0.50–1.00 on heavy tasks (10–20%) — the ceiling** | MCP-auth redesign + event-driven scheduling + cold fresh-eyes first review + coupling to `--resume` CLI behavior |

At a handful of tasks/day that ceiling is dollars per week against a
multi-day rework of two security/scheduling boundaries — negative ROI. The
original 40–70% prize was mostly harvested by cheaper means that shipped
instead: persist the diff (B1), ladder the models (B2), skip dead verifies
(B3).

**The flip is volume.** At ~50–100 tasks/day, $0.50–1.00/task is real money
and V3 becomes a legitimate project. Watch it with the meters that already
exist — `stage_usage` rollups (krill) and `/api/usage` (whale) give
tasks/day and $/task directly.

**Reopen when any one holds:**
- sustained task volume reaches ~50+/day (V3 pays for its rework in weeks);
- retry cycles (decline/verify-fail) climb back above ~30% of monthly krill
  spend — then start with V1 on the impl/verify retry paths only;
- the CLI exposes the 1-hour cache TTL (V5) — re-price V2/V3, since the
  scheduling rework drops out of the cost side.
