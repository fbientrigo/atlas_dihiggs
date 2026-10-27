---
title: "Module // recast_viewer"
description: "Source-neutral interactive event display and cutflow explorer."
---

<div class="wired-card">
  <div class="wired-card-header">
    <span>// module · recast_viewer</span>
    <span class="wired-pill">DIAGNOSTIC EVENT DISPLAY</span>
  </div>
  <div class="wired-grid">
    <div><strong>REPOSITORY:</strong> <a href="https://github.com/fbientrigo/atlas_recast_viewer">fbientrigo/atlas_recast_viewer</a></div>
    <div><strong>PINNED COMMIT:</strong> <code>b049d37</code></div>
    <div><strong>PRIMARY ROLE:</strong> Interactive Event Visualization</div>
  </div>
</div>

## Scientific Responsibility

The `recast_viewer` application provides a source-neutral, static interactive visualization tool for reconstructed ATLAS DV+jets events and selection cutflows:

- **3D Visualization**: Built with Three.js offering 3D event rendering, $R\text{–}z$ and $x\text{–}y$ track projections, and orbit controls.
- **Cutflow Diagnostics**: Interactive boolean counterfactual toggles allow researchers to inspect the effect of individual selection cuts on event topologies.
- **Diagnostic Tool Contract**: Strictly designed as a diagnostic instrument; does not represent displays as reconstructed ATLAS detector data or full detector GEANT4 simulation.
- **Adapters**: Supports multiple input formats via `OriginalRecastAdapter` and `LocalInstrumentedReferenceAdapter`.

---

## Authoritative Documentation Links

- [GitHub Repository](https://github.com/fbientrigo/atlas_recast_viewer)
- [Repository README](https://github.com/fbientrigo/atlas_recast_viewer#readme)
- [Data Contract](https://github.com/fbientrigo/atlas_recast_viewer/blob/main/docs/DATA_CONTRACT.md)
- [Roadmap](https://github.com/fbientrigo/atlas_recast_viewer/blob/main/docs/ROADMAP.md)
- [Validation Report](https://github.com/fbientrigo/atlas_recast_viewer/blob/main/docs/VALIDATION.md)

---

## API Reference

Symbols for this module are listed per source file in the [API reference](/api/); the coverage table links to each group.
