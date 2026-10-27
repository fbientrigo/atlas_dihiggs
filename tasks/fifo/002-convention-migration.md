# 002 — Migrate downstream physics conventions

**State:** DONE — focused validation and independent review completed on 2026-10-21.
**Owner:** convention migration.
**Effort / ROI:** 3–7 days / very high.

The downstream physics repositories now carry byte-identical v3 caches from `dihiggs@087ba246e9a9fa34b16249b52629a62703893b5c`, with source SHA-256 `4f3a938ed54dbc779d25f691ce1dd06fe17af69751105dc3b69ccb6b7d92fff6` and provenance sidecars. Boundary and HEP-cross locks/tests use SHA-256 and schema v3. The global checker verifies source bytes, cache bytes, sidecars, lock metadata, and the campaign's unpromoted result state.

HEP-cross loads constants from the v3 structure and fails closed when the cache or sidecar is missing or inconsistent. New-production MadGraph points require v3 provenance, active decimal `m_h`, explicit `physical_2HDM`, and internally consistent signed/raw/magnitude coupling fields; the card and banner use `GHphiphi = -g_physical_hphiphi_GeV`. Magnitude-only coupling is limited to explicitly identified historical replay. Effective prescription mappings remain unresolved and unimplemented.

Boundary's Atlas/evaluate_point v0/v1 and its 125.09 GeV HiggsSignals reference are now labelled replay-only. Historical results, R9 inputs, campaigns, and frozen Pack B behavior were not regenerated or relabelled. The discrepancy ledger now reflects the pinned authority snapshot.

Acceptance and evidence:

- Boundary: `tests/test_conventions.py`, `tests/test_external_tools.py` — passed.
- HEP-cross: `tests/test_constants.py`, `tests/test_external_tools.py`, `tests/test_run_physical_point_madgraph.py`, `tests/test_madgraph_banner_verification.py`, `tests/test_mass_jet_campaign.py` — passed (one MadGraph execution test skipped because the external process directory is absent).
- UFO and LLP recast: `tests/test_conventions_provenance.py` — passed in each repository.
- Root checker and six-repository bootstrap passed in the isolated workspace.
- Independent review findings were corrected and re-reviewed: the driver and
  banner verifier share strict v3 mass validation, and an entrypoint test
  checks card preparation with a simulated MadGraph execution.

The HEP-cross convention/card/banner tests passed in the minimal environment;
the complete focused campaign suite also passed with the repository's declared
scientific Python dependencies installed. The external MadGraph execution
test was skipped because its process directory is absent.

Remaining work is limited to migrating other sample/production handoff paths so every v3 input retains convention metadata and signed physical coupling semantics, while keeping unresolved effective mappings rejected. Track this separately as FIFO 012; it does not block the v3 cache contract or the checked HEP-cross driver.
