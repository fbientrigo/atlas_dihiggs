---
title: "ATLAS DiHiggs & LLP Recast"
description: "Wired research documentation and API reference for the 2HDM Type-I long-lived scalar and ATLAS DV+jets recast workspace."
template: splash
hero:
  tagline: "PROTOCOLS // 2HDM TYPE-I LONG-LIVED SCALARS // RECAST OBSERVATORY"
  actions:
    - text: "Getting Started"
      link: /getting-started/
      icon: right-arrow
      variant: primary
    - text: "Explore Pipeline"
      link: /pipeline/
      icon: external
    - text: "API Coverage Matrix"
      link: /api/
      icon: document
---

<div class="wired-card">
  <div class="wired-card-header">
    <span>// PROTOCOL: ATLAS_DIHIGGS_WORKSPACE</span>
    <span class="wired-pill green">SYSTEM: NOMINAL</span>
  </div>
  <p style="margin-bottom: 0.75rem;">
    Welcome to the <strong>ATLAS DiHiggs &amp; Long-Lived Particle (LLP) Recast</strong> workspace documentation and API observatory.
  </p>
  <p style="font-size: 0.85rem; color: var(--sl-color-gray-3); margin-bottom: 0;">
    This multi-repository environment coordinates an end-to-end phenomenological research pipeline investigating long-lived neutral scalar bosons (<em>H</em><sub>2</sub>) within the <strong>Two-Higgs-Doublet Model (2HDM) Type-I</strong> framework. By focusing on parameter regimes where <em>H</em><sub>2</sub> exhibits macroscopic decay lengths (<em>c</em>&tau; ~ mm to m) and decays dominantly to bottom quarks (<em>H</em><sub>2</sub> &rarr; <em>b</em>b̄), the project reinterprets (recasts) ATLAS displaced-vertex plus jets (DV+jets) search results to extract novel exclusion bounds and evaluate high-luminosity discovery potentials.
  </p>
</div>

## Scientific Architecture

The workspace coordinates six Git submodules, passing from Lagrangian theory evaluation to detector response simulation and interactive 3D visualization:

```mermaid
flowchart LR
    TH["dihiggs<br/>2HDM Theory Evaluator"] --> UFO["dihiggs_ufo<br/>UFO & Pythia Models"]
    UFO --> MG["dihiggs_hep_cross<br/>MadGraph Cross Sections"]
    MG --> BD["dihiggs_boundary<br/>Boundary & Limits"]
    RC["dihiggs_llp_recast<br/>ATLAS DV+jets Recast"] --> BD
    RC --> VW["recast_viewer<br/>Event & Cutflow Display"]
```

## Modular Components

<div class="wired-grid">
  <div class="wired-card" style="margin-bottom: 0;">
    <div class="wired-card-header">
      <span>dihiggs // THEORY</span>
      <span class="wired-pill red">AUTHORITY</span>
    </div>
    <p style="font-size: 0.85rem; margin-bottom: 0.75rem;">
      Canonical 2HDM Type-I parameter evaluation, decay widths, branching ratios, lifetime calculation, and parameter space scans. Single source of truth for theory conventions.
    </p>
    <a href="/modules/dihiggs/">View Module Specification &rarr;</a>
  </div>

  <div class="wired-card" style="margin-bottom: 0;">
    <div class="wired-card-header">
      <span>dihiggs_ufo // UFO</span>
      <span class="wired-pill">BASELINE</span>
    </div>
    <p style="font-size: 0.85rem; margin-bottom: 0.75rem;">
      Universal FeynRules Output models (Pack A) and Pythia 8 decay engines (Pack AA) for long-lived scalar event generation.
    </p>
    <a href="/modules/dihiggs-ufo/">View Module Specification &rarr;</a>
  </div>

  <div class="wired-card" style="margin-bottom: 0;">
    <div class="wired-card-header">
      <span>dihiggs_hep_cross // MADGRAPH</span>
      <span class="wired-pill red">RESULTS</span>
    </div>
    <p style="font-size: 0.85rem; margin-bottom: 0.75rem;">
      Matrix-element event generation, production cross-section calculations (&sigma;<sub>production</sub>), run banner verification, and numerical result authority.
    </p>
    <a href="/modules/dihiggs-hep-cross/">View Module Specification &rarr;</a>
  </div>

  <div class="wired-card" style="margin-bottom: 0;">
    <div class="wired-card-header">
      <span>dihiggs_llp_recast // RECAST</span>
      <span class="wired-pill">FROZEN</span>
    </div>
    <p style="font-size: 0.85rem; margin-bottom: 0.75rem;">
      Reproduction of the frozen ATLAS displaced-vertex plus jets search baseline, trackless jet selections, and <em>A</em><sub>eff</sub>(<em>c</em>&tau;) response curves.
    </p>
    <a href="/modules/dihiggs-llp-recast/">View Module Specification &rarr;</a>
  </div>

  <div class="wired-card" style="margin-bottom: 0;">
    <div class="wired-card-header">
      <span>dihiggs_boundary // BOUNDARY</span>
      <span class="wired-pill">LIMITS</span>
    </div>
    <p style="font-size: 0.85rem; margin-bottom: 0.75rem;">
      Enrichment of theory observables with HiggsBounds/HiggsSignals limits, direct production cross sections, and recast efficiencies into analysis-ready boundary atlases.
    </p>
    <a href="/modules/dihiggs-boundary/">View Module Specification &rarr;</a>
  </div>

  <div class="wired-card" style="margin-bottom: 0;">
    <div class="wired-card-header">
      <span>recast_viewer // DISPLAY</span>
      <span class="wired-pill">3D VIEWER</span>
    </div>
    <p style="font-size: 0.85rem; margin-bottom: 0.75rem;">
      Interactive 3D Three.js event display, track geometry inspection, and cutflow counterfactual toggle interface.
    </p>
    <a href="/modules/recast-viewer/">View Module Specification &rarr;</a>
  </div>
</div>

---

## Authority & Governance

Scientific integrity across six independent repositories requires strict governance:

- **Zero Timestamp Authority**: Never infer validity from file timestamps or presence on disk. Only artifacts registered in `CURRENT_CAMPAIGN.yaml` are authoritative.
- **Convention Separation**: Theory definitions are strictly separated from numerical cross sections and event samples.
- **Code Reference**: Continuous static code audits inspect Doxygen XML and Griffe AST to ensure full traceability down to exact GitHub lines.

Check the [Physics Authority & Provenance](/authority/) contract and the [API Reference](/api/) for complete details.
