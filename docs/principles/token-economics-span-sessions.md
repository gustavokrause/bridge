---
name: token-economics-span-sessions
description: Principle — judge token/cost optimizations across the whole session lifecycle, not the first load. Heavier upfront load is fine if everything after is leaner and cheaper.
metadata:
  type: feedback
---

Token and cost optimizations must be judged across the full arc of usage, not the single first run. A change that loads MORE upfront is correct if everything it enables afterward is much more efficient and cheaper per session. Local "this is smaller" is the wrong metric; lifecycle cost is the right one.

**Why:** When optimizing the global Cloud / CLAUDE.md setup, the naive read was "compress to save tokens every session." Gustavo's higher-level read: a heavier first run that makes every subsequent drop far more efficient nets out cheaper and better. That whole-lifecycle vision is what I lacked and what changed the decision. Same shape as why investing in the intent library is worth the upfront cost ([[intent-library-method]]).

**How to apply:** When evaluating any token/cost/perf optimization, model the full session lifecycle, not the first invocation. Surface the upfront-vs-amortized tradeoff explicitly. Don't reject upfront investment just because the first load is bigger. Caution from [[instruction-file-voice-load-bearing]]: naive compression of instruction files can backfire — smaller is not automatically cheaper if behavior degrades.
