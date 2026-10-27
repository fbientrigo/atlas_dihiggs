# 012 — Complete v3 provenance across remaining handoff paths

**State:** PENDING.
**Dependency:** FIFO 002 convention migration.
**Effort / ROI:** 2–5 days / high.

Extend the validated v3 source identity and signed physical-coupling fields through remaining production/sample workflows. Check in particular the custom Mass-vs-Jet card writer and recast sample manifests; do not rewrite or regenerate frozen datasets, seed outputs, R9, or historical Pack B artifacts.

Acceptance:

- Every new v3 model-point handoff preserves schema, source commit, source checksum, active mass convention ID/text, and prescription.
- Sign-sensitive producers use `GHphiphi = -g_physical_hphiphi_GeV` and reject unresolved effective mappings.
- Historical magnitude-only paths require an explicit replay label and preserve their original result bytes.
- Focused tests cover provenance loss, sign changes, mismatch rejection, and manifest propagation.
