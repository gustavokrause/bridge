# Session 08 — Backup (off-machine)  ✅ DONE 2026-06-14

Pushed every repo to a private GitHub remote so nothing lives only on this disk.
Ran before the rename (07) and re-pushed after.

## What was done
- **whale** (was `baleia`) → `gustavokrause/whale` — **private**, pushed.
- **krill** (was `ai-auto-worflow`) → `gustavokrause/krill` — already had the remote,
  **PUBLIC**, pushed.
- **bridge** → `gustavokrause/bridge` — **private**, pushed.
- **ai-team** → `gustavokrause/ai-team` — **private**, pushed.

Secret scan before pushing: clean — no `.env`, `.db`, keys, or emails tracked.

## Open items
- **krill is PUBLIC** (pre-existing choice). Flip to private with:
  ```bash
  gh repo edit gustavokrause/krill --visibility private --accept-visibility-change-warning
  ```
- **`data/` runtime state is NOT backed up** (gitignored on purpose): krill
  `data/tasks.db`, whale `data/whale.db` + `data/context/`, `.env*`. Consciously
  local-only. To back it up, copy out-of-band, e.g.:
  ```bash
  rsync -a ~/code/krill/data ~/code/whale/data ~/Backups/fleet-data-$(date +%F)/
  ```
