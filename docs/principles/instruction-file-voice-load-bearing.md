---
name: instruction-file-voice-load-bearing
description: Principle — voice, first-person framing, and grammar in instruction files (CLAUDE.md etc.) are load-bearing. Naive compression that strips them changes model behavior, even when it looks semantically clean.
metadata:
  type: feedback
---

In instruction/memory files, the voice and grammar are not decoration — they are functional. First-person framing ("I read files before editing") and sentence structure shape how the model behaves when reading the file. Compression that looks lossless on inspection can still change behavior because it strips the load-bearing voice.

**Why:** We compressed CLAUDE.md ~19% smaller; on inspection it looked clean, no semantic loss. But an A/B in real use showed: original = lean output, compressed = bloated/garbled output. I first misblamed ultra mode — wrong. Gustavo pointed to the real A/B: stripping the first-person voice/grammar was the cause. I conceded the mechanism.

**How to apply:** Before compressing any instruction/memory file, back up first, then A/B test real output (original vs compressed) rather than trusting visual inspection. Preserve first-person voice and grammatical structure even at a token cost. "Looks semantically identical" is not evidence of behavioral equivalence. Connects to [[token-economics-span-sessions]] — smaller is not automatically cheaper if it degrades behavior.
