---
title: "ATLAS DiHiggs & LLP Recast"
description: "Research workspace investigating long-lived scalars in the 2HDM Type-I framework and reinterpreting ATLAS displaced-vertex plus jets searches."
template: splash
hero:
  tagline: "Modular phenomenological research workspace investigating long-lived scalars in the 2HDM Type-I framework and reinterpreting ATLAS displaced-vertex plus jets searches."
  actions:
    - text: "Pipeline"
      link: /pipeline/
      variant: primary
    - text: "API Reference"
      link: /api/
      variant: secondary
---

<div class="wired-card">
  <div class="wired-card-header">
    <span>// QUICK START: REPOSITORY INITIALIZATION</span>
    <span class="wired-pill">WORKSPACE PROTOCOL</span>
  </div>

```sh
# 1. Clone complete workspace with all submodules
git clone --recursive https://github.com/fbientrigo/atlas_dihiggs.git

# 2. Or clone root workspace and initialize a single submodule
git clone https://github.com/fbientrigo/atlas_dihiggs.git && git submodule update --init <module>

# 3. Verify workspace integrity and submodule pins
python3 scripts/check_workspace.py
```

</div>

<div class="wired-grid">
  <div class="wired-card" style="margin-bottom: 0;">
    <div class="wired-card-header">
      <span>// PIPELINE</span>
      <span class="wired-pill">WORKFLOW</span>
    </div>
    <p style="font-size: 0.85rem; margin-bottom: 1rem; color: var(--sl-color-gray-1);">
      Six-stage scientific pipeline connecting 2HDM Lagrangian evaluation, UFO models, MadGraph cross sections, detector acceptance, and limit boundaries.
    </p>
    <a href="/pipeline/">Explore Pipeline Architecture &rarr;</a>
  </div>

  <div class="wired-card" style="margin-bottom: 0;">
    <div class="wired-card-header">
      <span>// MODULES</span>
      <span class="wired-pill">6 SUBMODULES</span>
    </div>
    <p style="font-size: 0.85rem; margin-bottom: 1rem; color: var(--sl-color-gray-1);">
      Architectural specifications and boundary contracts for theory evaluators, cross-section engines, recast drivers, and 3D visualizers.
    </p>
    <a href="/modules/">Inspect Submodules &rarr;</a>
  </div>

  <div class="wired-card" style="margin-bottom: 0;">
    <div class="wired-card-header">
      <span>// API REFERENCE</span>
      <span class="wired-pill">C++ &amp; PYTHON</span>
    </div>
    <p style="font-size: 0.85rem; margin-bottom: 1rem; color: var(--sl-color-gray-1);">
      Per-file C++ Doxygen AST and per-module Python Griffe references linked directly to pinned GitHub submodule commits.
    </p>
    <a href="/api/">Browse API &amp; Coverage &rarr;</a>
  </div>

  <div class="wired-card" style="margin-bottom: 0;">
    <div class="wired-card-header">
      <span>// AUTHORITY</span>
      <span class="wired-pill">PROVENANCE</span>
    </div>
    <p style="font-size: 0.85rem; margin-bottom: 1rem; color: var(--sl-color-gray-1);">
      Physics authority contracts, zero-timestamp inference rules, campaign state tracking, and numerical result verification.
    </p>
    <a href="/authority/">Review Governance Rules &rarr;</a>
  </div>
</div>
