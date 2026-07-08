---
name: pipeline-self-resolves
description: Principle — a pipeline/system must self-resolve any task; brittle on a trivial case = dead on heavy cases. Fix the class, never patch one case.
metadata:
  type: feedback
---

When a pipeline (e.g. the Verify phase) melts down on a trivial task, the problem is NOT the trivial task — it is that the pipeline can't robustly handle anything. A system that's brittle on an easy input is worse on a heavy one. The fix must make the system self-resolve (proportional + budget-aware + always-concludes: escalate, never timeout-loop), not special-case the one input that exposed it.

**Why:** A ridiculous copy-to-clipboard UI button stalled the Verify phase. My instinct was "it's a UI task, skip_verify and make the PR." Gustavo reframed: the pipeline exists to offload work — if it can't decently handle a trivial task, it certainly can't handle real ones. We implemented a systemic fix and Verify got dramatically better. He said the bloated UI task was never the point — the robust pipeline was. Patch fixes the symptom; the goal fixes the cause.

**How to apply:** When a small/trivial input breaks a shared system, treat the input as a probe that revealed a systemic weakness. Name the class of problem, fix the system so it self-resolves any task, do not bypass the single failing case. The "just skip it / it's trivial / make the PR and move on" instinct is the tell that I'm aiming too low. Related: [[intent-library-method]]. Anti-patch-reflex rule is in global CLAUDE.md.
