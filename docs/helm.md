# helm — the operator layer above the fleet

> Design doc. Status: **not built** — this is the architecture to build
> against when it starts. Companion reading:
> [`operator-leverage.md`](operator-leverage.md) (why the operator's
> attention is the bottleneck) and the safety section of
> [`../CLAUDE.md`](../CLAUDE.md) (the brakes helm must never weaken).

## The problem

The fleet moved the constraint from *typing* to *deciding*: every park,
gate, blocker, and proposal waits on one human noticing it, loading its
context, and acting. Observed reality: most of that time is **attention**
(discovering that something waits, reassembling context), not **judgment**
(the decision itself is usually seconds once prepared). helm automates
attention completely and judgment only where evidence earns it.

helm is an AI operator that sits in bridge — watching the pipeline the way
a human operator does (watcher, SSE, blocker queue, parked reviews, whale
proposals) — and prepares, suggests, or takes the actions a human otherwise
polls for.

## Why this is the most dangerous component in the system

Every brake in the fleet exists because model judgment fails in specific
ways. helm sits **on top of the brakes**. Designed carelessly, it is
"remove all gates" with extra steps. Two failure modes are structural, not
hypothetical:

- **Correlated judgment.** The implementer, reviewer, verifier, and helm
  are all the same model family. helm approving a deliverable is Claude
  agreeing with Claude about Claude — it collapses the independence the
  cold-review fork deliberately preserves. A track record on easy cases
  does not transfer to the hard case that matters.
- **Prompt injection.** helm reads pipeline artifacts — dumps, diffs, task
  comments, PR bodies — and acts on what it reads. Every author of those
  artifacts (including a compromised dependency's changelog in a diff) is
  a potential steerer of the component holding the keys. helm's input is
  attacker-reachable by design.

Both dictate the same conclusion: helm's *authority* must be tiered,
earned, and floored — its *awareness* can be total.

## Architecture: three tiers

### Tier 1 — Sentinel (watch + prepare + notify; zero authority)

Subscribes to what already exists:

- krill SSE (`task.transitioned`, `task.stuck`, parks) + the blocker queue
  (already a structured "human needed" inbox)
- whale proposals / plan runs / follow-up warnings
- the meters: `stage_usage` (cost, resumed), override rate, impact ledger

For every event that would otherwise wait for the human to notice, Sentinel
prepares a **decision card**: what happened, the diff/plan summary, impact
hypothesis vs verify evidence, cost so far, its **recommendation with
reasons**, and one-tap actions. Delivery: notification + a bridge surface.

The operator's follow-along drops from polling three UIs to reading cards.
This is ~80% of the win at ~0% of the risk, and it generates the training
data for Tier 2 for free: every card records `recommended` vs
`human_did`.

### Tier 2 — Deputy (earned authority, per decision class)

The fleet already invented the mechanism: **override rate governs
autonomy.** Applied here:

- A **decision class** is a narrow, named situation: "activate next
  BACKLOG task when nothing else is active", "click Recover on an orphaned
  claim", "approve plan gate on a low-risk, non-protected task",
  "resume a paused todo-picker after a follow-up was consumed".
- Sentinel logs its recommendation *before* the human acts. When
  recommendation == human action for **N consecutive instances of a class**
  (suggest N=10 to start), the class **graduates**: helm acts directly,
  with a receipt (what, why, evidence) in an audit trail the human reviews
  asynchronously.
- **One disagreement demotes the class** to suggest-only and resets the
  counter. Demotion is cheap and automatic; promotion is slow and earned.
- Graduation state is config the human can read and edit — never inferred
  silently.

Deputy actions carry the same always-conclude discipline as the fleet:
per-hour action caps, episode counters on repeated action against the same
task, and a park-for-human when its own confidence is low or inputs look
anomalous (injection heuristics: instructions addressed to the operator
inside artifacts, action requests that exceed the card's scope).

### Tier 3 — the never-floor (helm's self-edit guard)

Classes that **never graduate**, at any track record:

- Deliverable approval (anything that merges), on any project — and
  doubly on protected repos. Merges are the irreversible boundary; the
  correlated-judgment problem lives exactly here.
- Arming `auto_publish` / changing dials / editing graduation config.
- Anything touching helm's own code or prompts (helm never self-modifies —
  that loop goes through the normal fleet with human review).
- Spending money beyond metered inference (purchases, deploys to paid
  infra, external service signup).

The floor is enforced in code (an action allowlist per tier), not in the
prompt — a steered helm must hit a wall, not a suggestion.

## Composition with the existing dial

The dial and helm answer different questions and compose:

- **Dial** (conservative → ludicrous): *which classes of task may run
  unattended* — static policy, set by the human.
- **helm**: *should this particular instance proceed, and who handles the
  ops noise around it* — per-case judgment with cross-system context
  (whale + krill + git + meters + ledger in one view; no single stage has
  that).

helm never widens the dial's permissions; it can only add friction (flag a
task the dial would have auto-finished) or absorb toil beneath it.

## Build phases

1. **helm-0, Sentinel**: event ingestion (SSE + blocker poll + proposal
   poll) → decision cards → notification with deep links. No actions at
   all. Ship, live with it, measure how many cards/day and how often its
   recommendation matches the human.
2. **helm-1, recommendation tracking**: recommendations recorded and
   scored automatically against what the human did (the override-rate
   pattern, applied to helm itself). Pure metering, still no authority.
3. **helm-2, Deputy on two classes**: BACKLOG activation + orphan Recover
   (both reversible, both already have fleet-side safety nets). Audit
   trail + caps + demotion live from day one.
4. **helm-3, widen by evidence**: plan-gate approvals on low-risk
   non-protected tasks, picker resume, blocker triage — each class
   individually graduated, never in batches.

Each phase ends with the same live-fire discipline the fleet's tracker
used: run real traffic, record numbers, only then widen.

## What helm is not

- Not a replacement for the deliverable gate — the human approving merges
  **is the product** (see operator-leverage.md: verification is what makes
  fleet output sellable).
- Not a second dial — it composes with the one that exists.
- Not self-improving — its own changes ride the normal pipeline like any
  self-edit, behind the same guard.
