# Session continuity (`--resume`) in krill — why not now, how it could work

> Companion to tracker item **B4** in [`FLEET-PRINCIPLES-AUDIT.md`](../FLEET-PRINCIPLES-AUDIT.md).
> Status: design notes, no implementation. The naive plan ("one warm session
> per task chain") is dead; this doc records why, and the constrained variants
> that could still work.

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
   assumed it already existed.
2. **Prompt cache is per-model; stages switch models.** `model-map.ts` pins
   Opus on PLANNING/AI-REVIEW and Sonnet on IMPLEMENTING/VERIFY. A resume
   across a model boundary gets **zero** cache benefit — the accumulated
   transcript is re-tokenized at full input price on the new model. The
   savings only ever existed for same-model hops.
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
window. This targets the documented worst case: `OPERATIONAL_COST.md` shows
decline cycles at 400k–1M tokens each. **Gain: 50–70% per retry cycle.
Highest value, lowest risk.**

### V2 — Same-model adjacent pair: IMPLEMENTING → VERIFY
Both run Sonnet today. VERIFY resumes the implementing session: the diff,
files, and plan are already in context. Needs event-driven chaining (trigger
VERIFY immediately on transition instead of waiting for the cron slot) to
stay inside the 5-min TTL. Independence cost is mild — verify checks
behavior, not judgment. **Gain: 20–40% of VERIFY input.**

### V3 — Ladder-enabled full chain (depends on tracker B2)
If B2's cheap-first ladder moves AI-REVIEW's first pass to Sonnet, the clean
path becomes IMPLEMENT → REVIEW → VERIFY **all Sonnet** — a same-model chain
where full resume is coherent, with Opus escalation as a deliberate cold
fork (which also restores independent review exactly where judgment is
contested). B2 is the enabler; don't build V3 before it.

### V4 — No resume at all: artifact handoff (the fallback that always works)
Persist what each stage derived (diff text = tracker B1; a structured stage
summary; verify checklist) and inject it into the next cold spawn. No CLI
coupling, no auth rework, no TTL dependency, keeps review independence.
Captures a large share of the same win — it removes the re-*derivation*
(tool-call round trips re-reading the repo), which is a real cost even when
tokens can't be cache-read. **This is already the tracker's B1 and ships
first regardless.**

### V5 — Extended cache TTL
The API supports 1-hour cache TTL at a higher write price, which would make
cron-gap resumes viable. Unverified whether the Claude Code CLI exposes it;
check in the spike. If it does, it changes V2/V3's math materially.

## Honest gains table

| Variant | Scope | Estimated gain | Risk |
|---|---|---|---|
| V1 retry resume | decline/verify-fail cycles | 50–70% of each retry (the 1–2M-token cycles) | Low |
| V2 impl→verify | VERIFY input | 20–40% | Low-mild (TTL scheduling work) |
| V3 full Sonnet chain | whole clean path | up to ~50% of chain input | Medium; needs B2 first; review independence managed via Opus cold fork |
| V4 artifact handoff | all stages | smaller per-stage, but universal + already planned (B1) | None |
| V5 1h TTL | multiplier on V2/V3 | removes the scheduling constraint | Unknown (CLI support unverified) |

The blanket "40–70% of lifecycle input" from the original audit is not
recoverable — it assumed cache benefits across model boundaries that cannot
exist. The realistic ceiling is V1+V2 (or V1+V3 after B2).

## Decision gate

Per the tracker: **B4 is gated on LF-2.** Ship B1–B3, run the cost checkpoint,
and only open this spike if the remaining spend on retries/VERIFY justifies
the auth + scheduling rework. If LF-2 shows retry cycles still dominate,
start with V1 — it's the smallest surface and the biggest documented burn.
