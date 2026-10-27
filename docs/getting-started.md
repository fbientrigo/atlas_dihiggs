# Getting Started

This guide walks through cloning the workspace, verifying the local checkout, executing the six-stage phenomenological pipeline, and setting up the required external physics toolchains.

---

## Workspace Setup

The root repository coordinates six Git submodules. You can clone the full workspace at once or initialize only the specific modules you need.

### Cloning the Workspace

=== "Full Checkout"
    To fetch the root workspace and all six submodules:
    ```bash
    git clone --recursive <workspace-url> atlas_dihiggs
    cd atlas_dihiggs
    ```

=== "Modular Checkout"
    To initialize only a specific submodule (e.g., `dihiggs` for theory evaluation):
    ```bash
    git clone <workspace-url> atlas_dihiggs
    cd atlas_dihiggs
    git submodule update --init dihiggs
    ```

### Lightweight Environment

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

## End-to-End Scientific Workflow

The complete analysis pipeline progresses through six sequential stages. Each module defines explicit input and output contracts; never substitute an output from an unrelated campaign or parameter point.

### 1. Evaluate a Theory Point (`dihiggs/`)
Run 2HDMC-based point evaluation to check theoretical viability and calculate decay parameters:
- Reference contract: `dihiggs/docs/contracts/canonical_evaluators_v2.md`.
- Active authority: $m_h = 125.20\text{ GeV}$ (`mh_125p20_active_2026`).
- Executes `Lambda1EvaluatorV2` (target $\lambda_1$) or `DihiggsPointV2Evaluator` (rectangular grid in $M_2$).
- Computes parameter construction, perturbativity, unitarity, positivity, decay widths, branching ratios ($H_2 \to b\bar{b}$), and proper lifetime ($c\tau$).

### 2. Prepare Production (`dihiggs_hep_cross/`)
Run MadGraph matrix-element calculations for validated physical points:
- Uses `scripts/run_physical_point_madgraph.py` with an approved UFO model from `dihiggs_ufo`.
- Employs the canonical `physical_2HDM` coupling prescription with $GH\phi\phi = -g_{\text{physical, } h\phi\phi}$.
- Generates process cross sections ($\sigma_{\text{production}}$) and records full provenance (seed, energy, mass, banner).
- Banner must be verified with `scripts/madgraph_banner_verification.py`.

### 3. Establish the Recast Baseline (`dihiggs_llp_recast/`)
Reproduce the frozen ATLAS displaced-vertex plus jets (DV+jets) recast:
- Frozen baseline commit: `d4047c744062094c9f88e507bb1ccf69e9fe88d6`.
- Canonical benchmark: $m_{H_2} = 150\text{ GeV}$, $c\tau = 4.32622\text{ mm}$, $H_2 \to b\bar{b}$.
- Computes reconstructed acceptance times efficiency response $A_{\text{eff}}(c\tau)$ using the original/published Trackless analysis selection.
- Distinct from the diagnostic `modified` analysis mode.

### 4. Integrate Signal & Constraints (`dihiggs_boundary/`)
Merge physics stages into analysis-ready boundary datasets:
- Joins theory observables, production cross section $\sigma_{\text{production}}$, and recast response $A_{\text{eff}}(c\tau)$ by `point_id`.
- Enriches points with experimental limits from HiggsBounds and HiggsSignals.
- Computes signal yield observables:
    $$\sigma_{4b} = \sigma_{\text{production}} \times \text{BR}(H_2 \to b\bar{b})^2$$
    $$\sigma_{\text{visible}} = \sigma_{4b} \times A_{\text{eff}}$$
    $$N_{\text{expected}} = \mathcal{L} \times \sigma_{\text{visible}}$$
- Enforces strict domain validation: rejects unphysical extrapolation beyond calibrated domains.

### 5. Inspect and Share (`recast_viewer/`)
Visualize event kinematics, decay geometry, and cutflows:
- Processes verified recast datasets via `OriginalRecastAdapter` or `LocalInstrumentedReferenceAdapter`.
- Provides 3D Three.js event rendering, vertex inspection, transverse impact parameter ($d_0$) tracking, and counterfactual cut analysis.
- Serves as a diagnostic tool without substituting for reconstructed detector data.

### 6. Review Authority (`dihiggs_hep_cross/`)
Validate and formally register results:
- Review `docs/CURRENT_DATA_AUTHORITY.md` and `state/CURRENT_CAMPAIGN.yaml`.
- Ensure all provenance requirements are satisfied before citing numerical results.
- Successful completion of code execution does not automatically promote results to current authority.

---

## Toolchain & System Prerequisites

While the root environment checker only requires Python with `pytest` and `PyYAML`, running full simulation and evaluation stages requires specialized scientific software:

| Toolchain / Dependency | Required By | Purpose / Notes |
|---|---|---|
| **C++17 Compiler & GSL** | `dihiggs` | GCC 9+ or Clang 10+ with GNU Make and GNU Scientific Library (`libgsl-dev`) to compile 2HDMC evaluators. |
| **MadGraph5_aMC@NLO** | `dihiggs_hep_cross` | Version 3.4+ for hard-scattering event generation and cross section integration. |
| **Pythia 8 & FastJet** | `dihiggs_ufo`, `dihiggs_llp_recast` | Parton showering, hadronization, long-lived particle decay simulations, and jet clustering. |
| **HiggsTools / 2HDMC** | `dihiggs_boundary` | HiggsTools v1.2 (HiggsBounds v1.7, HiggsSignals v1.1) and 2HDMC v1.8 for experimental limit testing. |
| **Node.js & npm** | `recast_viewer` | Node.js v18+ and npm to build and run the static frontend application. |
| **DuckDB & rclone** | `lake` (optional) | DuckDB for SQL querying over Parquet lake tables; rclone for synchronizing Google Drive blobs. |
