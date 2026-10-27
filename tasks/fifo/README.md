# Implementation FIFO

This queue holds the remaining cross-repository work identified in the
workspace audit. Work in numeric order. Keep one item `IN_PROGRESS` at a time;
close an item only when its acceptance checks pass and its evidence is
recorded. Reorder only by editing this list and explaining the dependency or
priority change in the task. Tasks 001 and 002 are complete. Task 003 is next;
remaining handoff coverage is tracked as 012.

Effort estimates are engineering time and exclude long simulation queues,
external reviews, or publication latency. ROI reflects project-wide value and
uncertainty in the remaining work. Completed tasks retain their acceptance
criteria and validation evidence.

| FIFO | Task | State | Effort | ROI |
|---:|---|---|---:|---|
| 001 | [Reproducible workspace and onboarding](001-reproducible-onboarding.md) | DONE | 1–3 days | Very high |
| 002 | [Migrate downstream physics conventions](002-convention-migration.md) | DONE | 3–7 days | Very high |
| 003 | [Finish T4 analytic bridge](003-t4-bridge.md) | PENDING | 2–5 days | High |
| 004 | [Close profiled/adaptive Boundary delivery](004-boundary-adaptive.md) | PENDING | 3–6 days | High |
| 005 | [Close production-to-recast signal path](005-production-recast-signal.md) | PENDING | 1–3 weeks | High scientific value; high uncertainty |
| 006 | [Add viewer sample comparison](006-viewer-comparison.md) | PENDING | 3–7 days | Medium-high |
| 007 | [Make Pack B handoff reproducible](007-pack-b-handoff.md) | PENDING | 2–5 days plus run/review time | Medium |
| 008 | [Close JEV/autoharness operation](008-jev-autoharness.md) | PENDING | 2–5 days | Medium-low until inputs stabilize |
| 009 | [Scope general physical certification](009-physical-certification.md) | PENDING | Several weeks; uncertain | Unclear until coverage is scoped |
| 010 | [Generate the scientific site from the registry](010-site-registry.md) | PENDING | 1–2 weeks | Low until onboarding is stable |
| 011 | [Document campaign artifact recovery](011-artifact-recovery.md) | PENDING | 2–5 days | High for reproducibility; scope to a representative workflow |
| 012 | [Complete v3 provenance across remaining handoff paths](012-v3-handoff-coverage.md) | PENDING | 2–5 days | High |
