---
title: "Getting Started"
description: "Setup, submodule initialization, offline workspace validation, and external physics prerequisites."
---

<div class="wired-card">
  <div class="wired-card-header">
    <span>// setup</span>
  </div>
  <p>
    This guide walks through cloning the workspace, verifying the local submodule checkouts, running the pipeline, and configuring the required external physics compilers.
  </p>
</div>

## Workspace Setup

Needs Python 3.11+, `g++`, `make` and GSL (`libgsl-dev`). From a fresh clone:

```bash
git clone --recursive https://github.com/fbientrigo/atlas_dihiggs.git atlas_dihiggs
cd atlas_dihiggs
make setup    # .venv + deps + dhb; builds 2HDMC, evaluate_point, DihiggsPointV2Evaluator (~1.5 min)
make smoke    # autoresearch end-to-end smoke (~40 s)
.venv/bin/python scripts/check_workspace.py
```

The same three steps run in CI (`.github/workflows/smoke.yml`, Python 3.13).

The checker confirms:
- Submodule gitlinks match pinned revisions.
- Local working trees have no untracked modifications.
- The `dihiggs` gitlink carries the pinned convention bytes (SHA-256), and the `external_tools.lock.yaml` pins agree. No downstream module keeps a copy.
- Campaign registry (`dihiggs_hep_cross/state/CURRENT_CAMPAIGN.yaml`) maintains a null result authority until formal sign-off.

---

## Toolchain & External Physics Prerequisites

`make setup` covers the C++/GSL row; the other stages need their own software:

| Toolchain / Dependency | Required By | Version / Spec | Purpose & Scope |
|---|---|---|---|
| **C++17 Compiler & GSL** | `dihiggs` | GCC 9+ / Clang 10+, `libgsl-dev` | Compiles 2HDMC evaluators and parameter scan binaries. |
| **MadGraph5_aMC@NLO** | `dihiggs_hep_cross` | Version 3.4+ | Hard-scattering event generation and cross section integration. |
| **Pythia 8 & FastJet** | `dihiggs_ufo` | Pythia 8.3+, FastJet 3.4+ | Parton showering, hadronization, and jet clustering. |
| **HiggsTools / 2HDMC** | `dihiggs_boundary` | HiggsTools v1.2, 2HDMC v1.8 | Standard Model and BSM Higgs experimental limit testing (HiggsBounds / HiggsSignals). |
| **DuckDB & rclone** | `lake` (optional) | DuckDB 1.5+ (installed by `make setup`), rclone | Direct SQL query interface over Parquet lake tables and Google Drive synchronization. |

---

## Next Steps

- Consult [Data flow & ownership](/pipeline/) for who owns each stage and what each one hands to the next.
- Read [Physics Authority & Provenance](/authority/) for the mandatory data governance rules.
- Browse the [API Reference](/api/) for symbol-level documentation of all C++ and Python code.
