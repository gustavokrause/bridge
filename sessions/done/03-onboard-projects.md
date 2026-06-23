# Session 03 — Onboard your real projects (whale awareness)

You are in **bridge** (read `CLAUDE.md` first). Goal: make whale genuinely aware
of your projects via **onboarding (B5)**, so the planner works from real grounding
instead of thin/empty CONTEXT. (See `CLOSING-THE-CYCLE.md` B5; awareness ≠
autonomy — auditing whale/krill is fine, the self-edit guard still gates them.)

## Start

```bash
npm run status                              # whale up (real), krill up
curl -s localhost:3000/api/projects        # the project registry (slugs, folder_path, has_repo)
```

## Do

For each project whale should know:
- **Code projects** (has a repo: e.g. `arqtrack`, `saas-factory` if it has code,
  `krill`, `whale`): run the read-only audit →
  `curl -s -X POST localhost:4100/api/onboard -H 'Content-Type: application/json' -d '{"key":"arqtrack"}'`
  Then open the Context tab (or `GET /api/context?key=arqtrack`) and **read the
  produced CONTEXT for accuracy** — fix anything wrong by dumping corrections +
  re-distilling. The audit is read-only; confirm the repo's `git status` is clean
  after.
- **Idea / pre-code projects** (no repo, e.g. `meu veleiro`): onboard returns
  "seed needed" — **seed by hand**: dump a solid profile (what it is, goals,
  constraints, your private context) hinted to that project, then Distill.

## Notes
- Audits run real Claude (Sonnet) reading the repo — can take 1–3 min each.
- The audit writes only to whale's `data/context/` (gitignored), never the repos.
- This is grounding only — don't plan/push tasks here (that's later sessions / C).

## Done when
- Every project you care about has an accurate `CONTEXT.md` in whale.
- Summary: which were audited vs seeded, and any whose CONTEXT needed correction.
