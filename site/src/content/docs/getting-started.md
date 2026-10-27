---
title: "Getting Started"
description: "Setup, submodule initialization, offline workspace validation, and external physics prerequisites."
---

<div class="wired-card">
  <div class="wired-card-header">
    <span>// SYSTEM_SETUP: INITIALIZATION & ENVIRONMENT</span>
    <span class="wired-pill green">VERIFIED READY</span>
  </div>
  <p style="margin-bottom: 0;">
    This guide walks through cloning the workspace, verifying the local submodule checkouts, executing the six-stage phenomenological pipeline, and configuring the required external physics compilers.
  </p>
</div>

## Workspace Setup

The root repository coordinates six Git submodules. You can clone the full workspace at once or initialize only specific modules as needed.

### 1. Cloning the Workspace

import { Tabs, TabItem } from '@astrojs/starlight/components';

<Tabs>
  <TabItem label="Full Checkout (All 6 Submodules)">
    To fetch the root workspace and all six submodules:
    ```bash
    git clone --recursive https://github.com/fbientrigo/atlas_dihiggs.git atlas_dihiggs
    cd atlas_dihiggs
    ```
  </TabItem>
  <TabItem label="Modular Checkout (Single Submodule)">
    To initialize only a specific submodule (e.g. `dihiggs` for theory evaluation):
    ```bash
    git clone https://github.com/fbientrigo/atlas_dihiggs.git atlas_dihiggs
    cd atlas_dihiggs
    git submodule update --init dihiggs
    ```
  </TabItem>
</Tabs>

### 2. Lightweight Verification Environment

The root repository provides an offline checker to verify submodule revisions, convention caches, and campaign state without requiring heavy physics compilers or simulation software.

Create and activate a minimal virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Verify workspace integrity:

```bash
python3 scripts/check_workspace.py
```

The checker confirms:
- Submodule gitlinks match pinned revisions.
- Local working trees have no untracked modifications.
- Physics convention caches in downstream modules are byte-identical to the canonical authority commit in `dihiggs`.
- Provenance sidecars (`conventions/physics_conventions.lock.yaml`) match the v3 schema.
- Campaign registry (`dihiggs_hep_cross/state/CURRENT_CAMPAIGN.yaml`) maintains a null result authority until formal sign-off.

---

## Toolchain & External Physics Prerequisites

While the root environment checker only requires Python with `pytest` and `PyYAML`, running full simulation and evaluation stages requires specialized scientific software:

| Toolchain / Dependency | Required By | Version / Spec | Purpose & Scope |
|---|---|---|---|
| **C++17 Compiler & GSL** | `dihiggs` | GCC 9+ / Clang 10+, `libgsl-dev` | Compiles 2HDMC evaluators and parameter scan binaries. |
| **MadGraph5_aMC@NLO** | `dihiggs_hep_cross` | Version 3.4+ | Hard-scattering event generation and cross section integration. |
| **Pythia 8 & FastJet** | `dihiggs_ufo`, `dihiggs_llp_recast` | Pythia 8.3+, FastJet 3.4+ | Parton showering, hadronization, displaced decay simulation, and jet clustering. |
| **HiggsTools / 2HDMC** | `dihiggs_boundary` | HiggsTools v1.2, 2HDMC v1.8 | Standard Model and BSM Higgs experimental limit testing (HiggsBounds / HiggsSignals). |
| **Node.js & npm** | `recast_viewer`, `site` | Node.js v20+, npm | Builds and runs the documentation site and 3D event viewer application. |
| **DuckDB & rclone** | `lake` (optional) | DuckDB 1.0+, rclone | Direct SQL query interface over Parquet lake tables and Google Drive synchronization. |

---

## Next Steps

- Consult the [Scientific Pipeline](/pipeline/) for the full physics workflow progression.
- Read [Physics Authority & Provenance](/authority/) for the mandatory data governance rules.
- Browse the [API Reference](/api/) for symbol-level documentation of all C++ and Python code.
