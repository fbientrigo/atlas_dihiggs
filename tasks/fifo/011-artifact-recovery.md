# 011 — Document campaign artifact recovery

**State:** PENDING. **Effort / ROI:** 2–5 days / high reproducibility value.

Recovery and provenance rules are scattered between lake tooling and campaign
notes. Audit one representative campaign's local/remote artifact references,
hashes, and restore path; do not synchronize or prune data as part of this
task.

Acceptance: a documented offline-capable inventory identifies canonical
artifact IDs, source, hashes, status, and safe restore command; missing or
non-authoritative inputs remain clearly blocked; restore verifies checksums;
the workflow is tested without deleting source artifacts.
