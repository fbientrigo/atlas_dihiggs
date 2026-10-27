---
title: "Module // dihiggs_llp_recast"
description: "Public ATLAS displaced-vertex plus jets search reproduction and response mapping."
---

<div class="wired-card">
  <div class="wired-card-header">
    <span>// module · dihiggs_llp_recast</span>
    <span class="wired-pill">SEARCH BASELINE REPRODUCTION</span>
  </div>
  <div class="wired-grid">
    <div><strong>REPOSITORY:</strong> <a href="https://github.com/fbientrigo/dihiggs_llp_recast">fbientrigo/dihiggs_llp_recast</a></div>
    <div><strong>PINNED COMMIT:</strong> <code>4d62c29</code></div>
    <div><strong>PRIMARY ROLE:</strong> ATLAS DV+jets Recast</div>
  </div>
</div>

## Scientific Responsibility

The `dihiggs_llp_recast` module reproduces the published ATLAS displaced-vertex plus jets (DV+jets) search baseline and calculates detector response curves for long-lived scalars:

- **Upstream Frozen Baseline**: Pinned baseline commit `d4047c744062094c9f88e507bb1ccf69e9fe88d6`.
- **Canonical 150 GeV Benchmark**: $m_{H_2} = 150\text{ GeV}$, $c\tau = 4.32622\text{ mm}$, $H_2 \to b\bar{b}$, `Trackless_Aeff = 0.01573386`.
- **Analysis Modes**: Canonical `original/published Trackless` (R8/R10 response). The separate `modified` analysis mode is a distinct selection and not interchangeable.
- **Response Mapping**: Generates acceptance $\times$ efficiency ($A_{\text{eff}}(c\tau)$) lookup grids across proper lifetime regimes.

---

## Authoritative Documentation Links

- [GitHub Repository](https://github.com/fbientrigo/dihiggs_llp_recast)
- [Repository README](https://github.com/fbientrigo/dihiggs_llp_recast#readme)
- [Canonical Trackless Status](https://github.com/fbientrigo/dihiggs_llp_recast/blob/main/docs/CANONICAL_TRACKLESS_STATUS_20260807.md)
- [R8 Result Brief](https://github.com/fbientrigo/dihiggs_llp_recast/blob/main/docs/R8_PI_RESULT_BRIEF.md)

---

## API Reference

Symbols for this module are listed per source file in the [API reference](/api/); the coverage table links to each group.
