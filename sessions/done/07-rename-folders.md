# Session 07 — Rename: `ai-auto-worflow` → `krill`, `baleia` → `whale`  ✅ DONE 2026-06-14

Renamed two repo folders and fully rebranded the strategy brain (`baleia` → `whale`,
PT → EN). This is the record of what changed; old names appear only as the
old→new mapping.

## What was done
- **Folders:** `ai-auto-worflow → krill`, `baleia → whale` (git history travels).
- **whale repo (full rebrand):** env vars `BALEIA_* → WHALE_*`; self-edit guard
  default `BALEIA_PROTECTED "baleia,krill"` → `WHALE_PROTECTED "whale,krill"`;
  package name; DB default `data/whale.db`; context `data/context/whale.md`;
  comments + PLAN/README prose.
- **krill DB (`data/tasks.db`):** project `KRILL` `folder_path` → `…/krill`;
  project `BALEIA` → name `whale`, slug `WHALE`, `folder_path` → `…/whale`.
  Old task `BALEIA-7` stays as history; `task_counter` preserved → next is `WHALE-8`.
- **whale DB (`data/whale.db`):** `proposed_tasks.project_key` `baleia` → `whale`;
  db file + context file renamed.
- **bridge:** scripts (`KRILL_DIR` / `WHALE_DIR` / `WHALE_PORT`, `../krill`, `../whale`)
  + live docs (`CLAUDE.md` / `README.md` / `AGENTS.md`).
- **Cleanup:** removed empty `~/.ai-worktrees/BALEIA`.

## Verified
- whale **10/10**, krill **62/62** tests green.
- Fleet up: krill `:3000`, whale `:4100`, `runner=real`, `protected=whale/krill`,
  14 personas load.
- Key `whale` resolves to the krill `WHALE` project (name + slug both match).
- Self-edit guard confirmed protecting `whale`. No stale `ai-auto-worflow` / `baleia`
  paths in code or DB.

## Not in git
The DB edits (krill + whale runtime state) are gitignored — local-only, not backed
up off-machine.
