---
title: "Workspace Modules Overview"
description: "Architecture, roles, and repository contracts across the four independent Git submodules."
---

<div class="wired-card">
  <div class="wired-card-header">
    <span>// module inventory</span>
    <span class="wired-pill">4 submodules</span>
  </div>
  <p>
    The workspace coordinates four independent repositories pinned as Git submodules. Each module maintains its own codebase, build system, test harness, and scientific contracts. To avoid documentation drift, each module's internal contracts and implementation details are maintained within its own repository.
  </p>
</div>

## Submodule Architecture Matrix

| Module | Primary Scientific Responsibility | Authority Role | Pinned Commit | Docs on GitHub |
|---|---|---|---|---|
| [**`dihiggs`**](/modules/dihiggs/) | 2HDM Type-I parameter evaluation, decay widths, branching ratios, scans | **Theory Convention Authority** | `47fcfe8` | [dihiggs docs](https://github.com/fbientrigo/dihiggs#readme) |
| [**`dihiggs_ufo`**](/modules/dihiggs-ufo/) | UFO models (Pack A) and Pythia 8 decay configurations (Pack AA) | Model Release Baseline | `9a7ba38` | [dihiggs_ufo docs](https://github.com/fbientrigo/dihiggs_ufo#readme) |
| [**`dihiggs_hep_cross`**](/modules/dihiggs-hep-cross/) | MadGraph production drivers, cross sections, and campaign state | **Numerical Result Authority** | `df95b4b` | [dihiggs_hep_cross docs](https://github.com/fbientrigo/dihiggs_hep_cross#readme) |
| [**`dihiggs_boundary`**](/modules/dihiggs-boundary/) | Integration of theory observables, limits, and production cross sections into boundary atlases | Yield Calculation Authority | `8f032a7` | [dihiggs_boundary docs](https://github.com/fbientrigo/dihiggs_boundary#readme) |

---

## Detailed Module Specifications

Explore the individual module documentation pages for in-depth scientific descriptions, contracts, key drivers, and source code reference links:

- [**`dihiggs` Module**](/modules/dihiggs/) &mdash; Theory evaluation, 2HDMC base library integration, and parameter scans.
- [**`dihiggs_ufo` Module**](/modules/dihiggs-ufo/) &mdash; UFO model definitions and Pythia decay machinery.
- [**`dihiggs_hep_cross` Module**](/modules/dihiggs-hep-cross/) &mdash; Production cross sections, MadGraph run configuration, and banner verification.
- [**`dihiggs_boundary` Module**](/modules/dihiggs-boundary/) &mdash; Signal yield integration, HiggsBounds/Signals limits, and boundary dataset construction.
