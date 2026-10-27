# Physics Authority & Provenance

To guarantee scientific reproducibility across a multi-repository workspace, physics numbers, model conventions, and calculation outputs are strictly governed by explicit authority contracts.

---

## Authority Separation Rule

There is an absolute separation between **theory conventions** and **numerical results**:

> **Theory Convention Authority**  
> [`dihiggs/docs/PROJECT_PHYSICS_AUTHORITY.md`](https://github.com/fbientrigo/dihiggs/blob/main/docs/PROJECT_PHYSICS_AUTHORITY.md) & [`dihiggs/conventions/physics_conventions.yaml`](https://github.com/fbientrigo/dihiggs/blob/main/conventions/physics_conventions.yaml)
>
> **Numerical Result Authority**  
> [`dihiggs_hep_cross/docs/CURRENT_DATA_AUTHORITY.md`](https://github.com/fbientrigo/dihiggs_hep_cross/blob/main/docs/CURRENT_DATA_AUTHORITY.md) & [`dihiggs_hep_cross/state/CURRENT_CAMPAIGN.yaml`](https://github.com/fbientrigo/dihiggs_hep_cross/blob/main/state/CURRENT_CAMPAIGN.yaml)

!!! danger "Zero Timestamp Authority"
    **Never infer physics authority from file timestamps or local directory presence.**  
    A result file existing on disk or carrying a recent modification date does not establish that it is authoritative. Only artifacts explicitly registered in the active campaign YAML are recognized as valid project results.

---

## Theory Conventions & Caches

The `dihiggs` repository serves as the single source of truth for all theory definitions:

- **Canonical Authority**: Defined by convention commit `087ba246e9a9fa34b16249b52629a62703893b5c` in `dihiggs`.
- **Active SM Higgs Mass**: Standard Model $m_h = 125.20\text{ GeV}$ (convention identifier: `mh_125p20_active_2026`). Historical values (e.g., $125.0\text{ GeV}$) are legacy/replay only.
- **Convention Schema**: `physics_conventions_v3` with SHA-256 `4f3a938ed54dbc779d25f691ce1dd06fe17af69751105dc3b69ccb6b7d92fff6`.

### Downstream Synchronization

Four downstream repositories maintain local copies of the convention file:

1. `dihiggs_boundary`
2. `dihiggs_hep_cross`
3. `dihiggs_ufo`
4. `dihiggs_llp_recast`

Each cache includes a lock sidecar at `conventions/physics_conventions.lock.yaml` recording the upstream repository, commit hash, and file SHA-256 digest. The workspace validation script (`python3 scripts/check_workspace.py`) enforces that all downstream caches are byte-identical to the canonical source.

---

## MadGraph Cross-Section Provenance

A MadGraph cross section must never be cited or used downstream without complete provenance metadata. To be considered valid, each calculation record must explicitly specify:

1. **$H_2$ Mass**: Explicit decimal mass in GeV (e.g., $130.0$, $150.0$).
2. **Coupling Prescription**: Explicitly designated as `physical_2HDM`.
3. **Trilinear Coupling**: Explicit $GH\phi\phi$ value ($GH\phi\phi = -g_{\text{physical, } h\phi\phi}$).
4. **Collision Process**: Exact process definition (e.g., $p p \to h \to H_2 H_2$).
5. **Center-of-Mass Energy**: $\sqrt{s}$ (e.g., $13\text{ TeV}$).
6. **UFO Model Identity**: Verified UFO model release and cryptographic checksum.
7. **Random Seed**: Integration seed used for generation.
8. **Banner Artifact**: Validated run banner verified using `scripts/madgraph_banner_verification.py`.

---

## Campaign State & Promotion

- The current campaign registry (`dihiggs_hep_cross/state/CURRENT_CAMPAIGN.yaml`) tracks active production campaigns.
- In clean environment checkouts, `madgraph.authoritative_results` is explicitly initialized to `null`.
- Successful completion of an execution run or pipeline script does **not** automatically promote results to current authority. Results undergo scientific review before inclusion in the campaign registry.
