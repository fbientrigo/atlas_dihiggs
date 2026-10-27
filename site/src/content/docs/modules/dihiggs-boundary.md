---
title: "Module // dihiggs_boundary"
description: "Integration of theory observables, limits, and recast efficiencies into boundary datasets."
---

<div class="wired-card">
  <div class="wired-card-header">
    <span>// MODULE_SPEC: dihiggs_boundary</span>
    <span class="wired-pill green">SIGNAL YIELD & INTEGRATION</span>
  </div>
  <div class="wired-grid" style="margin: 0; font-size: 0.82rem;">
    <div><strong>REPOSITORY:</strong> <a href="https://github.com/fbientrigo/dihiggs_boundary">fbientrigo/dihiggs_boundary</a></div>
    <div><strong>PINNED COMMIT:</strong> <code>8f032a7</code></div>
    <div><strong>PRIMARY ROLE:</strong> Boundary Integration & Limits</div>
  </div>
</div>

## Scientific Responsibility

The `dihiggs_boundary` module serves as the integration engine merging theory observables, experimental exclusion limits, direct production cross sections, and versioned LLP detector responses:

- **Observable Synthesis**: Combines $(m_{H_2}, g_{hH_2H_2}, c\tau, \text{BR}_{bb})$ with direct $\sigma_{\text{production}}$ and Trackless $A_{\text{eff}}(c\tau)$.
- **Limit Integration**: Enriches parameter points with experimental exclusion limits from HiggsBounds and HiggsSignals.
- **Signal Yield Calculations**:
  $$\sigma_{4b} = \sigma_{\text{production}} \times \text{BR}(H_2 \to b\bar{b})^2$$
  $$\sigma_{\text{visible}} = \sigma_{4b} \times A_{\text{eff}}$$
  $$N_{\text{expected}} = \mathcal{L} \times \sigma_{\text{visible}}$$
- **Execution Boundaries**: Does not execute MadGraph or Pythia directly; consumes certified upstream campaign artifacts.

---

## Authoritative Documentation Links

- [GitHub Repository](https://github.com/fbientrigo/dihiggs_boundary)
- [Repository README](https://github.com/fbientrigo/dihiggs_boundary#readme)
- [LLP Signal Contract](https://github.com/fbientrigo/dihiggs_boundary/blob/main/docs/llp_signal_contract.md)
- [Boundary ATLAS v1 Contract](https://github.com/fbientrigo/dihiggs_boundary/blob/main/docs/boundary_atlas_v1_contract.md)
- [LLP Signal v1 Modernization](https://github.com/fbientrigo/dihiggs_boundary/blob/main/docs/modernization_llp_signal_v1.md)

---

## API Reference

- [dihiggs_boundary C++ Evaluator Reference](/api/cpp/project/boundary/)
- [dihiggs_boundary Python Reference (`dhb`)](/api/python/dihiggs-boundary/)
