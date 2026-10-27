# 001 — Reproducible workspace and onboarding

**State:** DONE — verified on 2026-10-21.
**Owner:** workspace maintenance.
**Effort / ROI:** 1–3 days / very high.

Provide one root entry point, fixed repository commits, deliberate overlays,
and a minimal Python environment. Keep simulation toolchains and remote data
outside bootstrap.

Acceptance:

- A fresh directory receives all six exact pinned commits and their overlays.
- Re-running against the same checkout makes no changes.
- A checkout at another commit or with unrelated local changes is left intact
  and produces an actionable error.
- `scripts/check_workspace.py` passes offline with pytest and PyYAML only.
- Onboarding explains the order, repository ownership, science authority, and
  which heavyweight steps have not been performed.

Validation evidence:

- All six pinned repositories and overlays were installed in an isolated
  workspace. The public DiHiggs clone imported the bundled commits before
  checking out the pinned authority revision.
- `python3 -P scripts/bootstrap_workspace.py` completed; repeating it left
  repository revisions, statuses, and delivery-file hashes unchanged.
- `.venv/bin/python -P scripts/check_workspace.py` passed offline with the
  newly created minimal environment.
- `scripts/test_bootstrap_workspace.py` checks bundle installation,
  idempotence, and preservation of local changes.
- The two canonical evaluators built with the minimal quickstart targets.
  Both one-point orchestrator examples completed and their manifests
  identified the pinned authority commit and checksum.
- Independent review is complete. No new commit or publication was performed;
  the root delivery is prepared for Git review.
