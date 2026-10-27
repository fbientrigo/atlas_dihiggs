---
title: "Module // dihiggs_hep_cross"
description: "MadGraph production drivers, cross-section ingestion, campaign state, and numerical result authority."
---

<div class="wired-card">
  <div class="wired-card-header">
    <span>// MODULE_SPEC: dihiggs_hep_cross</span>
    <span class="wired-pill red">NUMERICAL RESULT AUTHORITY</span>
  </div>
  <div class="wired-grid" style="margin: 0; font-size: 0.82rem;">
    <div><strong>REPOSITORY:</strong> <a href="https://github.com/fbientrigo/dihiggs_hep_cross">fbientrigo/dihiggs_hep_cross</a></div>
    <div><strong>PINNED COMMIT:</strong> <code>df95b4b</code></div>
    <div><strong>PRIMARY ROLE:</strong> MadGraph Drivers & Campaign State</div>
  </div>
</div>

## Scientific Responsibility

The `dihiggs_hep_cross` module executes hard-scattering event generation, cross-section calculation, and manages campaign state across the workspace:

- **Numerical Result Authority**: Holds project authority for MadGraph cross sections registered in [`state/CURRENT_CAMPAIGN.yaml`](https://github.com/fbientrigo/dihiggs_hep_cross/blob/main/state/CURRENT_CAMPAIGN.yaml) and governed by [`docs/CURRENT_DATA_AUTHORITY.md`](https://github.com/fbientrigo/dihiggs_hep_cross/blob/main/docs/CURRENT_DATA_AUTHORITY.md).
- **Coupling Prescription**: Enforces the canonical `physical_2HDM` coupling convention with trilinear coupling $GH\phi\phi = -g_{\text{physical, } h\phi\phi}$.
- **MadGraph Drivers**: Automated batch matrix-element integration and systematic cross-section extraction.
- **Banner Verification**: Mandatory verification of generation banners prior to downstream citation.

---

## Key Drivers & Scripts

- `scripts/run_physical_point_madgraph.py`: Executes MadGraph for canonical physical points using the approved UFO model.
- `scripts/madgraph_banner_verification.py`: Verifies generated run banners for provenance fields (seed, beam energy, model ID, process).
- `scripts/11_ingest_madgraph_xsec.py`: Ingests and registers cross sections into campaign tables.

---

## Authoritative Documentation Links

- [GitHub Repository](https://github.com/fbientrigo/dihiggs_hep_cross)
- [Repository README](https://github.com/fbientrigo/dihiggs_hep_cross#readme)
- [Current Data Authority Contract](https://github.com/fbientrigo/dihiggs_hep_cross/blob/main/docs/CURRENT_DATA_AUTHORITY.md)
- [Current Campaign Registry](https://github.com/fbientrigo/dihiggs_hep_cross/blob/main/state/CURRENT_CAMPAIGN.yaml)

---

## API Reference

- [dihiggs_hep_cross C++ Adapters Reference](/api/cpp/project/hep_cross/)
- [dihiggs_hep_cross Python Reference (`llp_recast`)](/api/python/dihiggs-hep-cross/)
