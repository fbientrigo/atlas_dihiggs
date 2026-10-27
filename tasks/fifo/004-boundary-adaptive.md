# 004 — Close profiled/adaptive Boundary delivery

**State:** PENDING. **Effort / ROI:** 3–6 days / high.

Adaptive/profiled scan modules, configs, CLI entry points, checkpoints, and
tests exist locally. Integrate the coherent code/config/test set and document
the supported run and resume path.

Acceptance: a clean checkout runs a bounded deterministic smoke campaign,
resumes from its checkpoint, preserves attempted points and rejection reasons,
and validates output schema and provenance. No full physics boundary claim is
made from a smoke campaign.
