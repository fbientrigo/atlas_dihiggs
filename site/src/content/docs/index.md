---
title: "ATLAS DiHiggs & LLP Recast"
description: "Research workspace for long-lived scalars in the 2HDM Type-I and the reinterpretation of ATLAS displaced-vertex plus jets searches."
template: splash
---

<div class="home-hero">
  <p class="wired-eyebrow"><b>[00]</b> // workspace</p>
  <h1>ATLAS DiHiggs<br>&amp; LLP Recast</h1>
  <p class="lead">Long-lived scalars in the 2HDM Type-I, and the reinterpretation of ATLAS displaced-vertex plus jets searches. Six modules, one pinned workspace.</p>
  <div class="actions not-content">
    <a class="primary" href="/getting-started/">Get started</a>
    <a href="/pipeline/">Pipeline</a>
    <a href="/api/">API reference</a>
  </div>
</div>

<div class="wired-card">
  <div class="wired-card-header"><span>// quick start</span><span class="wired-pill">clone</span></div>

```sh
# all six modules
git clone --recursive https://github.com/fbientrigo/atlas_dihiggs.git

# or one module only
git clone https://github.com/fbientrigo/atlas_dihiggs.git
cd atlas_dihiggs && git submodule update --init dihiggs

# offline integrity check
python3 scripts/check_workspace.py
```

</div>

<div class="wired-grid">
  <div class="wired-card">
    <div class="wired-card-header"><span>// pipeline</span><span class="wired-pill">6 stages</span></div>
    <p>From 2HDM theory evaluation through UFO models, MadGraph cross sections and detector recast to the exclusion boundary.</p>
    <a href="/pipeline/">Read the pipeline →</a>
  </div>
  <div class="wired-card">
    <div class="wired-card-header"><span>// modules</span><span class="wired-pill">6 submodules</span></div>
    <p>What each repository owns, its inputs and outputs, and the contract it keeps with its neighbours.</p>
    <a href="/modules/">Browse modules →</a>
  </div>
  <div class="wired-card">
    <div class="wired-card-header"><span>// API reference</span><span class="wired-pill">C++ · Python</span></div>
    <p>Per-file symbols from Doxygen and griffe, each linked to its line at the pinned commit.</p>
    <a href="/api/">Open the API index →</a>
  </div>
  <div class="wired-card">
    <div class="wired-card-header"><span>// authority</span><span class="wired-pill">provenance</span></div>
    <p>Which physics conventions and campaign state are authoritative, and how provenance is checked.</p>
    <a href="/authority/">Read the rules →</a>
  </div>
</div>
