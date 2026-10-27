# Workspace Modules

The workspace is organized into six independent repositories pinned as Git submodules. Each module maintains its own codebase, build system, test harness, and scientific contracts. 

To avoid documentation drift, each module's internal contracts and implementation details are maintained within its own repository. Consult the links below for authoritative details.

---

## `dihiggs`

- **Repository**: [fbientrigo/dihiggs](https://github.com/fbientrigo/dihiggs)
- **Primary Responsibility**: Canonical 2HDM Type-I parameter evaluation, decay widths, branching ratios, lifetime calculation, and parameter space scans.
- **Physics Ownership**: Holds the **theory convention authority** for the entire project.
- **Key Executables**:
    - `dihiggs/app/Lambda1EvaluatorV2`: Point evaluation for explicit $(m_H, \lambda_1)$ target inputs using schema `dihiggs.lambda1.v2`.
    - `dihiggs/app/DihiggsPointV2Evaluator`: Rectangular grid evaluation in $(m_H, M_2)$ using schema `dihiggs.point.v2`.
- **Key Documents**:
    - [README](https://github.com/fbientrigo/dihiggs#readme)
    - [Project Physics Authority](https://github.com/fbientrigo/dihiggs/blob/main/docs/PROJECT_PHYSICS_AUTHORITY.md)
    - [Canonical Evaluators v2 Contract](https://github.com/fbientrigo/dihiggs/blob/main/docs/contracts/canonical_evaluators_v2.md)
    - [Quickstart Guide](https://github.com/fbientrigo/dihiggs/blob/main/docs/quickstart.md)

---

## `dihiggs_ufo`

- **Repository**: [fbientrigo/dihiggs_ufo](https://github.com/fbientrigo/dihiggs_ufo)
- **Primary Responsibility**: Universal FeynRules Output (UFO) models, MadGraph integration interfaces, and Pythia 8 decay configurations.
- **Scientific Status**:
    - **Pack A**: Frozen production baseline (`pi_ufo_baseline_v1_frozen_hotfix1.zip`, SHA-256: `58f1e976...`).
    - **Pack A MC**: Multi-seed integration stability studies (30 independent seeds, Birge ratio 0.99).
    - **Pack AA**: Pythia decay mechanics, lifetime, and branching ratio validation.
    - **Pack B**: Candidate infrastructure and operator preflight suite.
- **Key Documents**:
    - [README](https://github.com/fbientrigo/dihiggs_ufo#readme)
    - [Current State Summary](https://github.com/fbientrigo/dihiggs_ufo/blob/main/CURRENT_STATE.md)
    - [Artifact Registry](https://github.com/fbientrigo/dihiggs_ufo/blob/main/ARTIFACT_REGISTRY.json)
    - [Contract Index](https://github.com/fbientrigo/dihiggs_ufo/blob/main/docs/CONTRACT_INDEX.md)

---

## `dihiggs_hep_cross`

- **Repository**: [fbientrigo/dihiggs_hep_cross](https://github.com/fbientrigo/dihiggs_hep_cross)
- **Primary Responsibility**: Tracked MadGraph production drivers, cross-section ingestion, campaign state tracking, and current-campaign data authority.
- **Physics Ownership**: Holds the **numerical-result authority** for MadGraph production cross sections.
- **Key Drivers**:
    - `scripts/run_physical_point_madgraph.py`: Executes MadGraph for canonical physical points using the `physical_2HDM` prescription.
    - `scripts/madgraph_banner_verification.py`: Verifies generated run banners before trusting cross sections.
- **Key Documents**:
    - [README](https://github.com/fbientrigo/dihiggs_hep_cross#readme)
    - [Current Data Authority Contract](https://github.com/fbientrigo/dihiggs_hep_cross/blob/main/docs/CURRENT_DATA_AUTHORITY.md)
    - [Current Campaign Registry](https://github.com/fbientrigo/dihiggs_hep_cross/blob/main/state/CURRENT_CAMPAIGN.yaml)

---

## `dihiggs_llp_recast`

- **Repository**: [fbientrigo/dihiggs_llp_recast](https://github.com/fbientrigo/dihiggs_llp_recast)
- **Primary Responsibility**: ATLAS displaced-vertex plus jets (DV+jets) search reproduction, scalar adaptation, and acceptance $\times$ efficiency ($A_{\text{eff}}$) response mapping.
- **Scientific Baseline**:
    - Upstream frozen baseline: commit `d4047c744062094c9f88e507bb1ccf69e9fe88d6`.
    - Canonical 150 GeV benchmark: $m_{H_2} = 150\text{ GeV}$, $c\tau = 4.32622\text{ mm}$, $H_2 \to b\bar{b}$, `Trackless_Aeff = 0.01573386`.
    - Canonical analysis mode: `original/published Trackless` (R8/R10 response). The separate `modified` analysis mode is a distinct selection and not interchangeable.
- **Key Documents**:
    - [README](https://github.com/fbientrigo/dihiggs_llp_recast#readme)
    - [Canonical Trackless Status](https://github.com/fbientrigo/dihiggs_llp_recast/blob/main/docs/CANONICAL_TRACKLESS_STATUS_20260807.md)
    - [R8 Result Brief](https://github.com/fbientrigo/dihiggs_llp_recast/blob/main/docs/R8_PI_RESULT_BRIEF.md)

---

## `dihiggs_boundary`

- **Repository**: [fbientrigo/dihiggs_boundary](https://github.com/fbientrigo/dihiggs_boundary)
- **Primary Responsibility**: Composing theory observables, HiggsBounds/HiggsSignals limits, direct MadGraph production cross sections, and versioned LLP detector responses into analysis-ready boundary datasets.
- **Scientific Scope**:
    - Combines $(m_{H_2}, g_{hH_2H_2}, c\tau, \text{BR}_{bb})$ with direct $\sigma_{\text{production}}$ and Trackless $A_{\text{eff}}(c\tau)$.
    - Evaluates $\sigma_{4b} = \sigma_{\text{production}} \times \text{BR}_{bb}^2$, $\sigma_{\text{visible}} = \sigma_{4b} \times A_{\text{eff}}$, and $N_{\text{expected}} = \mathcal{L} \times \sigma_{\text{visible}}$.
    - Does **not** execute MadGraph or Pythia directly.
- **Key Documents**:
    - [README](https://github.com/fbientrigo/dihiggs_boundary#readme)
    - [LLP Signal Contract](https://github.com/fbientrigo/dihiggs_boundary/blob/main/docs/llp_signal_contract.md)
    - [Boundary ATLAS v1 Contract](https://github.com/fbientrigo/dihiggs_boundary/blob/main/docs/boundary_atlas_v1_contract.md)
    - [LLP Signal v1 Modernization](https://github.com/fbientrigo/dihiggs_boundary/blob/main/docs/modernization_llp_signal_v1.md)

---

## `recast_viewer`

- **Repository**: [fbientrigo/atlas_recast_viewer](https://github.com/fbientrigo/atlas_recast_viewer)
- **Primary Responsibility**: Source-neutral, static interactive visualization tool for the ATLAS DV+jets recast.
- **Features**:
    - Three.js 3D event displays, $R\text{–}z$ and $x\text{–}y$ projections, and OrbitControls.
    - Detailed cutflow inspection and boolean counterfactual toggling.
    - Built-in bilingual support (Spanish/English).
    - Diagnostic tool: does not represent displays as reconstructed ATLAS detector data or full detector simulation.
- **Key Documents**:
    - [README](https://github.com/fbientrigo/atlas_recast_viewer#readme)
    - [Data Contract](https://github.com/fbientrigo/atlas_recast_viewer/blob/main/docs/DATA_CONTRACT.md)
    - [Roadmap](https://github.com/fbientrigo/atlas_recast_viewer/blob/main/docs/ROADMAP.md)
