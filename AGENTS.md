# bridge — fleet control

Control room for the AI-fleet. Full operating guide in [`CLAUDE.md`](CLAUDE.md).

Fleet: `ai-team` (personas, `../ai-team`) → `whale` (strategy, `../whale`, :4100)
→ `krill` (executor, `../krill`, :3000).

Ops: `npm start` (boot both) · `npm run status` (diagnose) · `npm stop`.

Personas + routing + risk rubric: see `../ai-team/AGENTS.md`.
