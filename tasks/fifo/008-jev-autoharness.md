# 008 — Close JEV/autoharness operation

**State:** PENDING. **Effort / ROI:** 2–5 days / medium-low until upstream
inputs stabilize.

One-step decision/execution logic and local tests exist. Complete iterative
operation, interruption recovery, and a reproducible handoff only after tasks
001–005 settle their inputs.

Acceptance: deterministic run state records decisions, commands, outputs, and
recovery point; interrupted run resumes without duplicate or lost work; a
clean-checkout smoke validates policy limits and audit log.
