# Session 04 — Real-mode quality pass (whale stages)

You are in **bridge** (read `CLAUDE.md` first). The whale stages
(distiller / planner / router / audit / refine) are **stub-tested exhaustively but
real-Claude only spot-checked**. This session exercises them on real inputs and
tunes the prompts so real mode is trustworthy before Phase C.

## Start

```bash
npm run status              # whale runner=real
cd ../whale && npm test    # baseline: stub tests should be green (keep them green)
```

## Do

On a **non-self-edit** project (e.g. `arqtrack`, ideally onboarded in session 03):
1. **Distiller**: dump a few varied notes → Distill → read the CONTEXT. Check it
   classifies requests as *Work requested* (not Open questions) and doesn't invent.
2. **Router**: dump untagged notes → `route?` → does it pick the right project from
   the known list (not guess)?
3. **Planner**: Plan the project → are tasks grounded in CONTEXT, scoped (Augusto
   killing creep), not codebase-wandering? (planner is sandboxed — verify.)
4. **Refine**: Input a change on a proposed task → does it apply cleanly, re-triage
   sensibly, keep flow preview correct?

For each weak spot, **tune the prompt** in `../whale/src/stages.mjs`
(distillReal / planReal / routeReal / refineProposal) — wording only, keep the
output contracts. Re-run after each change.

## Constraints
- Prompt/quality tuning in `whale/src/stages.mjs` is a **whale self-edit** →
  edit manually, keep `npm test` green (10/10), commit per change (user's go).
- Don't change the autonomy rules, flags, or krill. Don't push tasks to krill here.
- Watch for regressions to B0's guarantees (sandboxed planner, no wandering).

## Done when
- Distiller / router / planner / refine produce good output on a few real inputs.
- Prompts tuned; whale tests still green.
- Summary: what was weak, what you changed, before/after examples.
