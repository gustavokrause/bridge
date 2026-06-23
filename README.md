# 🌉 bridge

Control room for the AI-fleet — `cd` here, open Claude Code, run the whole thing.

New here, or explaining it to someone? → [`docs/PITCH.md`](docs/PITCH.md).

```bash
npm start       # boot krill (:3000) + whale (:4100)
npm run status  # diagnose the fleet
npm stop        # stop both
```

The fleet:

```
ai-team/ (personas)  →  whale (strategy, :4100)  →  krill (executor, :3000)
```

Full operating guide + personas: [`CLAUDE.md`](CLAUDE.md). Sibling repos:
`../ai-team`, `../whale`, `../krill`.

`.claude/settings.json` sets `bypassPermissions` so the room is hands-free —
remove it if you want approval prompts back.
