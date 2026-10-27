# Start here: new machine setup

The root checkout is the versioned entry point. It pins six independent
repositories to exact commits and applies a small, reviewed workspace
overlay. Five pins are on their published default branches. The `dihiggs`
pin includes two already committed commits that are not yet on the public
default branch; `patches/dihiggs-base.bundle` carries those Git objects with a
verified checksum. This preserves the current 125.20 GeV authority without
rewriting its source or publishing it. The bootstrap will never overwrite an
existing checkout. It reuses a directory only when the pinned commit and
overlay match; otherwise it reports the mismatch and leaves the directory
untouched.

## Requirements

- Linux or WSL, Git, Python 3.10+, and a C++17 compiler with GNU Make and GSL
  for the `dihiggs` build.
- Network access for cloning the six repositories and pip for the light
  workspace environment.
- MadGraph, Pythia, ROOT, rclone, and HEP data are not installed or downloaded
  by bootstrap. The lake query client is optional and requires DuckDB.

## Clone and initialize

```sh
git clone <workspace-url> atlas_dihiggs
cd atlas_dihiggs
python3 -P scripts/bootstrap_workspace.py
```

This checks out the exact commits listed in `lake/repos.tsv`, imports the
versioned `dihiggs` commit bundle when needed, applies overlays under
`patches/`, and creates `.venv` with only `pytest`
and `PyYAML`. The script is safe to rerun. Set `ATLAS_VENV_PATH` to use a
different environment directory. Repository clones use Git's partial-clone
filter and defer checkout until after selecting the pinned commit. DuckDB can
be installed separately for the optional lake query client; bootstrap does
not configure a remote or move data.

Activate the environment and run the lightweight checkout check:

```sh
source .venv/bin/activate
python -P scripts/check_workspace.py
```

The checker verifies repository revisions/overlays, parses the campaign YAML,
and reports current data-authority status. It does not compile physics code,
run a simulation, access remote storage, or validate scientific results.

The minimal environment also runs the convention guards. HEP-cross campaign
and plotting tests need that repository's additional declared dependencies:

```sh
python -m pip install -r dihiggs_hep_cross/requirements.txt
```

Install these only when working on those stages; they are not required by
the workspace checker or the first theory-point smoke test.

## End-to-end workflow

Follow these stages in order. Each repository's contract defines its exact
inputs and output schemas; do not substitute a result from another point or
campaign because its filename looks similar.

1. **Evaluate a theory point (`dihiggs/`).** Read
   [`dihiggs/docs/quickstart.md`](../dihiggs/docs/quickstart.md), build the
   maintained evaluators, and run a one-point smoke evaluation. The output
   includes the point identity, theory predicates, widths, branching
   fractions, and lifetime fields defined by the evaluator schema.
2. **Prepare production (`dihiggs_hep_cross/`).** Use the tracked
   `scripts/run_physical_point_madgraph.py` driver with a canonical point that
   carries v3 source/schema/checksum provenance, active decimal `m_h`, the
   explicit `physical_2HDM` prescription, and consistent signed/raw/magnitude
   coupling fields, plus an approved UFO. Record the process, collision energy, H2
   mass, `GHphiphi` prescription, seed, and source artifacts. The card and banner use `GHphiphi = -g_physical_hphiphi_GeV`; verify the
   generated banner with `scripts/madgraph_banner_verification.py` before
   accepting its cross section. Magnitude-only input requires an explicit
   historical replay convention. Production needs the external MadGraph
   toolchain and is not part of bootstrap.
3. **Establish the recast baseline (`dihiggs_llp_recast/`).** Follow
   [`dihiggs_llp_recast/AGENTS.md`](../dihiggs_llp_recast/AGENTS.md): bootstrap
   the locked upstream source, build it without changing its physics logic,
   and reproduce a declared upstream benchmark before local adaptation.
   This stage may require Pythia/FastJet and validated event samples.
4. **Integrate the signal (`dihiggs_boundary/`).** Follow
   `dihiggs_boundary/docs/llp_signal_contract.md` and
   `docs/boundary_atlas_v1_contract.md`. Join production and recast inputs by
   `point_id`; validate that mass, lifetime, branching ratio, calibration
   domain, and provenance match. Boundary combines these inputs; it does not
   run MadGraph or Pythia.
5. **Inspect and share (`recast_viewer/`).** Follow its README and
   `docs/DATA_CONTRACT.md` to preprocess a validated recast dataset and check
   that the viewer labels source, units, selection, and capabilities. The
   viewer is diagnostic and does not promote physics results to current.
6. **Review authority (`dihiggs_hep_cross/`).** Before reporting any number,
   read `docs/CURRENT_DATA_AUTHORITY.md` and `state/CURRENT_CAMPAIGN.yaml`.
   The pinned registry currently names no authoritative MadGraph result.
   Successful computation alone does not promote a result.

Before stage 1, read [the workspace map](WORKSPACE_MAP.md),
`dihiggs/docs/PROJECT_PHYSICS_AUTHORITY.md`, and
`dihiggs/conventions/physics_conventions.yaml`. The named theory authority is
distinct from the numerical-result authority. Downstream v3 caches and
provenance sidecars are checked against the pinned source by task 002 of the
[implementation FIFO](../tasks/fifo/README.md).

## Updating the pins or overlay

Update one repository pin only after its commit is published and reviewed.
Add only the deliberate root-workspace overlay to that repository's patch;
never export an entire dirty working tree. Run the bootstrap against a clean
temporary destination and run the checker before updating the lock. Do not
edit the production authority registry as part of environment setup.
