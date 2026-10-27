# 006 — Add viewer sample comparison

**State:** PENDING. **Effort / ROI:** 3–7 days / medium-high.

The viewer already adapts H2 samples and replays curated geometry. Implement
reference-vs-H2 comparison through canonical fields only.

Acceptance: unit and semantic compatibility are checked before rendering;
incompatible selection modes or provenance suppress comparison with a clear
reason; tests cover matched and rejected pairs; no raw-source-column joining.
