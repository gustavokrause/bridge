# Session 06 — Config: evaluate env → UI-overridable settings

You are in **bridge** (read `CLAUDE.md` first). This is an **evaluation / design**
session — produce a recommendation, do **not** implement. Question: which config
currently living in env vars should become **UI-overridable at runtime**, and how.

## Why
whale config is env-only (`config.mjs` reads `process.env` at module load → a
restart is needed to change anything). krill already solved this for some config:
a `global_config` table + `/settings` UI + `PATCH /api/config`. Evaluate extending
that pattern and migrating the right env vars to it.

## Start

```bash
npm run status
```
Inventory the current config:
- whale: `../whale/src/config.mjs` + `../whale/.env.example` (runner, BYPASS,
  AUTOPUSH, ALLOW_NEW_PROJECTS, PROTECTED, models, CLAUDE_BIN, timeout, PORT,
  KRILL_URL, PERSONAS_DIR, DB/context paths).
- krill: `../krill/.env.local` (CLAUDE_RUNNER, DB_PATH, WORKTREES_ROOT,
  PORT) + the existing `global_config` table + `/settings` UI (the template to copy).

## Classify each setting
Into one of:
- **UI-overridable (runtime tunable)** — behavior you'd want to flip without a
  restart, per-session: e.g. whale `BYPASS` dial, `AUTOPUSH`, `ALLOW_NEW_PROJECTS`,
  runner mode, model tiers. (krill: already does automation/stages/etc.)
- **Keep in env (boot / infra)** — wiring set once at startup: ports, `DB_PATH`,
  `WORKTREES_ROOT`, `PERSONAS_DIR`, `CLAUDE_BIN`, `KRILL_URL`.
- **Safety-critical (handle with care)** — `WHALE_PROTECTED` (self-edit guard
  list), `allow_auto_finish`, `aggressive` dial. *Could* be UI-editable but
  weakening them from a no-auth LAN UI is a real risk — evaluate whether these stay
  env-only (so the UI can't disable the self-edit guard) or are UI-editable behind
  an explicit confirm.

## Decide + propose
- **Precedence model**: recommend one — e.g. DB/UI override **wins** over env, with
  env as the bootstrap default/seed (or env-wins-for-secrets). Justify.
- **Shape for whale** (to mirror krill): a singleton config table + `GET/PATCH
  /api/config` + a settings tab; and the refactor needed — `config.mjs` must read
  **live** (a getter), not freeze values at import.
- **Migration list**: exactly which vars move to UI, which stay env, which are
  safety-gated.
- **Risks**: runtime dial changes mid-run; no-auth LAN UI editing safety dials;
  keeping `.env` as the override-of-last-resort.

## Constraints
- **Evaluation only — no code, no schema.** Output is a written recommendation.
- Ground it in the actual config + krill's existing `global_config`/`/settings`
  pattern (read them).

## Done when
- A clear recommendation: migrate-list, keep-list, safety-gated-list, precedence,
  and the whale implementation shape — enough to spin a follow-up build session.
- Note explicitly how the **self-edit guard / protected list** stays protected.
