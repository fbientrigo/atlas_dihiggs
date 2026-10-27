# Workspace map

Each folder below is an independent Git repository. The root repository owns
the onboarding, pins, patches, and lightweight environment checks.

| Repository | Owns | Start with |
|---|---|---|
| `dihiggs/` | Canonical 2HDM point evaluators, decay widths, and theory scans | `README.md`, `docs/PROJECT_PHYSICS_AUTHORITY.md`, `docs/contracts/` |
| `dihiggs_boundary/` | Boundary datasets and interfaces to experimental constraints and LLP signal inputs | `README.md`, `docs/`, `python/dhb/` |
| `dihiggs_hep_cross/` | MadGraph drivers, cross-section ingestion, campaign state and data authority | `README.md`, `docs/CURRENT_DATA_AUTHORITY.md`, `state/CURRENT_CAMPAIGN.yaml` |
| `dihiggs_llp_recast/` | Upstream ATLAS DV+jets recast reproduction and project adaptations | `AGENTS.md`, `README.md`, `configs/upstream.lock.json` |
| `dihiggs_ufo/` | UFO model sources, packaging, and model validation | `README.md`, `ARTIFACT_REGISTRY.json` |
| `recast_viewer/` | Source-neutral event and cutflow viewer with preprocessing adapters | `README.md`, `docs/DATA_CONTRACT.md`, `docs/ROADMAP.md` |

## Authority and provenance

- Theory convention authority: `dihiggs/docs/PROJECT_PHYSICS_AUTHORITY.md`
  together with `dihiggs/conventions/physics_conventions.yaml`.
- Downstream repositories keep byte-identical v3 convention caches with
  `conventions/physics_conventions.lock.yaml` sidecars; the root checker
  verifies each cache against the pinned canonical Git commit.
- Current numerical-result authority: `dihiggs_hep_cross/docs/CURRENT_DATA_AUTHORITY.md`
  and `dihiggs_hep_cross/state/CURRENT_CAMPAIGN.yaml`. Only explicitly named
  artifacts may support current numerical claims.
- Cross-section provenance must include the parameters and artifacts required
  by that authority contract. A MadGraph summary row without its banner/source
  is insufficient.
- Recast validation starts from the locked upstream revision and benchmarks;
  local reinterpretation follows only after that baseline is reproduced.
- Root `patches/` are workspace overlays on published repository pins. They
  are not independent physics authorities.

`lake/` contains the optional local data-query client and its data metadata.
Remote lake data is not required for source checkout, environment setup, or
the lightweight validation command.
