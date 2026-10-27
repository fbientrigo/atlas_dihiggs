# 003 — Finish T4 analytic bridge

**State:** PENDING. **Effort / ROI:** 2–5 days / high.

Local implementation evidence includes CLI dispatch, tests, `AnalyticBridge.cpp`,
and patches, but the bridge and build target were not versioned in the audited
checkout. Preserve the existing local implementation while preparing a
reviewable patch against the pinned `dihiggs` revision.

Acceptance: clean checkout builds T4 from tracked sources; a small deterministic
smoke input exercises dispatch and output validation; unsupported modes fail
clearly; no claim depends on untracked source or binary artifacts.
