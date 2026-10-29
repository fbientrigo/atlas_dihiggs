---
title: "Module // dihiggs_boundary"
description: "Integration of theory observables, limits, and production cross sections into boundary datasets."
---

<div class="wired-card">
  <div class="wired-card-header">
    <span>// module · dihiggs_boundary</span>
    <span class="wired-pill">LIMITS & INTEGRATION</span>
  </div>
  <div class="wired-grid">
    <div><strong>REPOSITORY:</strong> <a href="https://github.com/fbientrigo/dihiggs_boundary">fbientrigo/dihiggs_boundary</a></div>
    <div><strong>PINNED COMMIT:</strong> <code>8f032a7</code></div>
    <div><strong>PRIMARY ROLE:</strong> Boundary Integration & Limits</div>
  </div>
</div>

## Scientific Responsibility

The `dihiggs_boundary` module serves as the integration engine merging theory observables, experimental exclusion limits, and direct production cross sections:

- **Observable Synthesis**: Combines $(m_{H_2}, g_{hH_2H_2}, c\tau, \text{BR}_{bb})$ with direct $\sigma_{\text{production}}$ joined by `point_id`.
- **Limit Integration**: Enriches parameter points with experimental exclusion limits from HiggsBounds and HiggsSignals.
- **Execution Boundaries**: Does not execute MadGraph or Pythia directly; consumes certified upstream campaign artifacts.

---

## Authoritative Documentation Links

- [GitHub Repository](https://github.com/fbientrigo/dihiggs_boundary)
- [Repository README](https://github.com/fbientrigo/dihiggs_boundary#readme)
- [Boundary ATLAS Contract](https://github.com/fbientrigo/dihiggs_boundary/blob/main/docs/boundary_atlas_contract.md)

---

## API Reference

Symbols for this module are listed per source file in the [API reference](/api/); the coverage table links to each group.
