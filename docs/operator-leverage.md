# Operator leverage — what a fleet like this is worth, and where to point it

The fleet multiplies **build throughput**: a well-scoped task goes
dump → plan → implement → review → verify → PR in minutes-to-hours, at
single-digit dollars, while the operator does something else. It is natural
to ask: *"could I work for more than one company with this?"* This doc is the
honest analysis of that question. Three plays look similar and are not.

## Play 1 — multiple employments ("overemployment"): the trap

The worst version of the idea, for reasons that have nothing to do with
throughput:

- **Contracts.** Most employment agreements carry exclusivity and
  IP-assignment clauses. Output volume and commit timestamps from a fleet
  are visibly superhuman — discovery is not hypothetical.
- **The structural killer: you can't feed an employer's code through a
  personal fleet.** Their repo sitting in your personal worktrees, their
  diffs flowing through your personal Claude subscription, PRs authored by
  your agent — that violates almost any company's security policy before it
  ever becomes a legal question. The fleet is unusable on exactly the
  codebases that pay the salary, unless the employer explicitly sanctions
  the tooling.
- **The fleet multiplies building, not presence.** N employers = N sets of
  meetings, politics, tacit context, and on-call — the parts no executor
  stage absorbs. The operator's attention is already the pipeline's
  bottleneck (every activation and every deliverable gate is a human
  decision); employment multiplies demands on exactly that scarce resource.

## Play 2 — contractor / agency-of-one: the legitimate version

Multiple **clients** is legal, normal, and expected — this is what "more
than one company" actually looks like when it works:

- Price **deliverables, not hours**. The fleet turns a fixed-bid project's
  cost structure into tokens + operator review time; the margin between the
  bid and that cost is the leverage, and it is yours to keep.
- Client authorization to use AI tooling goes **in the contract, in
  writing**. Clean, explicit, no policy landmines.
- The fleet's gates map naturally onto client work: plan review = scope
  sign-off, deliverable gate = QA before the client sees anything, the
  impact ledger = the invoice's justification line.

## Play 3 — your own portfolio: the uncapped version

Selling surplus capacity to employers prices it at its floor. Pointing it at
your own products keeps the upside:

- Salary leverage is capped at N × salary and fragile at N ≥ 2 (Play 1).
- Product leverage is uncapped and compounds — every fleet improvement
  raises the ceiling on everything it builds thereafter.
- The fleet was itself built this way (self-edit loop): the machine
  improving the machine is the same motion as the machine building the
  portfolio.

## The realistic shape

Not either/or:

1. **One job, done excellently in less time** — where the fleet is
   sanctioned or on your own tooling-friendly work. Side benefit: the impact
   ledger writes the metric-driven career story ("X as measured by Y,
   through Z") from real, verify-backed data.
2. **Surplus capacity → contracting or products**, chosen by what you need:
   cash flow now → contracting (Play 2); conviction in a product → equity in
   yourself (Play 3).

## Constraints to price in before scaling

- **Quota is the unit of capacity.** A single subscription's session window
  saturates on one active operator's projects. Multi-client throughput means
  API billing or additional seats — trivial against any of these revenue
  models, but a real line item in a contract bid.
- **The operator is the bottleneck, by design.** Gates (activation, plan
  review where armed, deliverable approval) exist so nothing merges
  unattended. Scaling clients scales *judgment* demand, not build demand —
  the fleet moved the constraint from typing to deciding, and no play
  removes it.
- **Verification is the product.** What makes fleet output sellable is that
  it arrives reviewed, verified, and impact-framed. Skipping gates to go
  faster spends the exact asset being sold.
