# Ponytail over-engineering audit, 2026-10-28

Read-only audit of the root and the six modules at the pins in `docs/DATA_FLOW.md` (dihiggs `a3b4907`, boundary `1fab1c1`, hep_cross `e40d36a`, llp_recast `01fd17c`, ufo `c41f452`, recast_viewer `804a547`). Nothing was applied. N1–N9 are done and not re-proposed.

Scope: tracked code only. Skipped: data, vendored `2hdmc/`, `higgstools/`, `dataset/hbdataset-*`, MG5, `node_modules`, `site/api`, `graphify-out`, `tests/unit/catch.hpp`.

Method: "dead" = no other tracked file in any of the 7 repos mentions the script/module name (`git grep -F` on the stem, excluding the file itself). "Test/Makefile-only" means the only callers are a test or a Makefile target. Line counts are `wc -l`, approximate. `path:1` = whole file.

**physics-sensitive** = touches a physics number (cτ, σ, BR, widths, couplings), a UFO model, a convention, or authority semantics (what counts as the source of truth). Do not cut these without an owner reading the diff and rerunning the relevant gate.

## Top 15 across all repos (by lines saved)

| # | Repo | Tag | What | Lines | Flag |
|---|---|---|---|---|---|
| 1 | dihiggs | delete (decision) | `autoresearch/` (harness, TUI, 45 tests, configs, 8 guides): nothing outside `dihiggs/` references it, and it is absent from the DATA_FLOW chain. Move to lake or delete. Last touched 2026-10-27, so it needs an owner call, not a silent cut | 29,759 (17.6k code + 12.1k tests) | `harness/dihiggs_physics_contract.py:1`, `dihiggs_parsers.py:1` are physics-sensitive |
| 2 | dihiggs | delete | `mlpython/lake_pipeline/`: 7 uncalled scripts (`dihiggs_lake_audit_safe.py` 740, `parallel_coordinates_population.py` 331, `subsample_pipeline.py` 266, `plot_three_brs_fixed.py` 254, `subset_unique_values_to_json.py` 250, `select_focused_grid_values.py` 202, `focused_grid_inventory.py` 151) plus `lake_explorer.py` 507 and `consolidate_lake.py` 551, which root `lake/lake.py` (`explored`, `commit`, `ls`) now supersedes | 3,252 | no |
| 3 | ufo | shrink | `LLscalar_v3_UFO_original/` and `releases/r14_runtime/LLscalar_v3_UFO_runtime/` share 11 byte-identical files (`vertices.py` 1025, `particles.py` 415, `object_library.py` 373, `lorentz.py`, `decays.py`, …). Only `couplings.py`, `parameters.py`, `write_param_card.py` differ (N5). Keep the runtime dir and a 3-file overlay for `_original`, or a symlink | 2,268 | **physics-sensitive** (UFO) |
| 4 | hep_cross | delete (archive) | finished R9/R10 campaign scripts: `scripts/r9_build_iteration1.py` 500, `r9_run_model_scan.py` 548, `r9_ingest_madgraph_scaling.py` 165, `r10_make_figures.py` 407, `r10_ctau_efficiency_scan.py` 383, `verify_r9_artifacts.py` 61, `verify_r10_effective_scan.py` 134 plus their Makefile targets. Results are in lake. Only the Makefile and each other call them | 2,198 | **physics-sensitive** (σ·BR·A_eff thresholds, cτ scan) |
| 5 | hep_cross | delete (archive) | `scripts/run_mass_jet_control_campaign.py:1` (1174) + `tests/test_mass_jet_campaign.py:1` (229): test-only caller, abandoned campaign | 1,403 | **physics-sensitive** (control σ) |
| 6 | dihiggs | delete | 9 uncalled scripts: `scripts/build_christopher_fixed_lam1_comparison_notebook.py` 367, `run_gen_fixings_chunked.py` 278, `watch_autoresearch_run.py` 196, `matching_tolerance_diagnostics` 149, `run_chris_existing_plots.py` 125, `audit_m2_boundary_topology.py` 89, `list_campaign_columns.py` 55, `inspect_problem_campaigns.py` 47, `jev_smoke.py` 40 | 1,346 | `run_gen_fixings_chunked.py`, `run_matching_tolerance_diagnostics.py` physics-sensitive (widths) |
| 7 | ufo | delete | `evidence/pack_a/pack_a_native_failed_20260718T023622Z/{parameters,particles}.py`: byte-identical to `LLscalar_v3_UFO_original/` (particles 415, parameters 719) | 1,134 | **physics-sensitive** (failed-run evidence; keep a sha note instead) |
| 8 | boundary | delete | abandoned LHS-campaign chain, only the chain itself calls it: `scripts/run_lhs_batch_sharded.sh:1` 341, `run_lhs_batch.sh:1` 216, `plot_campaign_pixels.py:1` 177, `keep_working_lhs_campaign.sh:1` 120, `archive_adaptive_m2_boundary.py:1` 68, `compare_serial_vs_sharded_smoke.sh:1` 64, `smoke_evaluate_point.sh:1` 64, `inspect_tiny_boundary.sh:1` 45. Keep `split_point_csv.py`, `merge_shard_outputs.py`, `generate_refined_lhs_boundary.py` (used by tests) | 1,095 | no |
| 9 | hep_cross | delete | uncalled: `campaigns/20260901_photonic_requalification/inputs/production_reference/run_mg_xsec_masses.sh:1` 202, `…/scripts/calc2hdmc.py:1` 143, `scripts/run_scale_campaign.py:1` 309 (only caller is `save_and_plot.py`), `save_and_plot.py:1` 158, `r10_generate_summary.py:1` 114, `run_pilot_study.py:1` 74 | 1,000 | `run_mg_xsec_masses.sh` physics-sensitive (σ masses) |
| 10 | dihiggs | delete | uncalled: `campaigns/t2_t4_20261008T043858Z/scripts/finalize_calculator_scan_reports.py` 251, `compare_legacy_decay_regression.py` 110; `benchmarks/run_first_h2_bounded_scan.py` 170; `dihiggs/batch_scan.py` 90; `chris/build_chris_hybrid.sh` 33, `build_calclambda1_scan.sh` 16 | 670 | `compare_legacy_decay_regression.py` physics-sensitive |
| 11 | hep_cross | delete | `bootstrap_llp_recast.sh:1`: no caller anywhere in the seven repos (I did not check whether it is still a useful bootstrap) | 657 | no |
| 12 | boundary | delete | `python/dhb/adaptive_exploration.py:1` 157 (only caller is its 8-line wrapper `scripts/run_adaptive_exploration.py`), `configs/adaptive_m2_exploration_v1.yaml` 31, `python/dhb/classify.py:1` 50 (imported nowhere; the `classify_row` it describes exists twice in `atlas.py:201` and `atlas_v1.py:116`), `configs/theory_atlas_v0.yaml:1` 102 (named only in `classify.py`'s docstring), `scripts/aggregate_adaptive_boundary.py:1` 134 (test-only) | 482 | `classify.py` is verdict logic; physics-sensitive until confirmed unused at runtime |
| 13 | ufo | delete | `curation/repository_cleanup_20260723T081927Z/{inventory_script,generate_inventory_docs,generate_cleanup_validation}.py`: one-shot cleanup of a past date, no caller | 364 | no |
| 14 | all | stdlib | 47 hand-rolled `sha256(path)` helpers (listed below), 6–8 lines each → `hashlib.file_digest(f, "sha256").hexdigest()` inline (Python ≥ 3.11; the workspace runs 3.13) | ≈330 | helper itself no; callers that stamp provenance hashes are physics-sensitive only if the digest changes, and it does not |
| 15 | llp_recast | delete | `scripts/extract_lhe_summary.py:1` 50, `scripts/run_upstream_benchmark.sh:1` 17: no caller | 67 | no |

`net: -46,025 lines, -1 deps possible.` (−16,266 lines if #1 stays; −1 dep is the unused `playwright-core`, see recast_viewer.) Items 4 and 5 are Makefile- or test-wired, so "delete" means archive to lake and drop the targets. #3 and #7 overlap if the original is also trimmed. Counts are measured, not a promise.

## Ranked list per repo

### root (`/home/fabian/atlas_dihiggs`)
Lean. `lake/lake.py` (524), `site/scripts/gen_api.py` (355), `scripts/check_workspace.py` (61) each have a caller. One note:
1. shrink `lake/test_lake.py:1` (198) is the only test file and fine. No cuts.

### dihiggs
1. delete `autoresearch/` 29,759 lines (top-15 #1).
2. delete `mlpython/lake_pipeline/*` 3,252 (#2). Also `mlpython/lake_pipeline/physics_conventions.py:48` re-defines `ctau_mm_from_width_gev` and the `HBAR_C` pins that `conventions/physics_conventions.yaml` owns (physics-sensitive, see duplicates).
3. delete 9 scripts under `scripts/` 1,346 (#6).
4. delete t2_t4 / benchmarks / chris / batch_scan 670 (#10).
5. shrink `.sisyphus/`, `RECONNAISSANCE_REPORT.md`, `GEMINI.md`, `obsidian/`, `notes/` (agent/session scratch, ≈10 files): not code, move to lake.
6. yagni `scripts/gemini_worker_loop.py:1` (491) + `scripts/gemini_contract_templates.py:1` + `autoresearch/tests/test_gemini_worker_loop.py:1` (433): called by `GEMINI.md` and its own test only.
7. yagni `studies/llp_families_20261019/{backend_audit,independent_potential_check,regression_tests}.py` (114/51/127): nothing runs them. These are checks, not dead weight: **wire into `tests/` instead of deleting**. physics-sensitive.
8. yagni `scripts/jev_adapter.py:1` (949) / `jev_policy.py` (428) / `jev_decide_once.py` / `jev_run_once.py`: reachable only from their tests and each other, and from autoresearch. Delete with #1 if #1 goes.
9. stdlib 7 `sha256(path)` copies: `benchmarks/run_first_h2_bounded_scan.py:40`, `dihiggs/app/orchestrator/lambda1_v2.py:104`, `scripts/generate_golden_lambda1.py:46`, `scripts/run_yukawa_order_recompute_v1.py:21`, `…_v2.py:30`, `tests/test_golden_lambda1.py:95`.
10. yagni two generations of the yukawa recompute script (not diffed): `scripts/run_yukawa_order_recompute_v1.py` and `_v2.py` (physics-sensitive).

### dihiggs_boundary
1. delete LHS chain 1,095 (#8).
2. delete `adaptive_exploration.py`, `classify.py`, `theory_atlas_v0.yaml`, `aggregate_adaptive_boundary.py` 482 (#12).
3. yagni `python/dhb/atlas.py:1` (476) vs `atlas_v1.py:1` (311): two atlas generations, `classify_row` defined in both. v0 is still called by `profiled_m2_scan.py` and `make_boundary_atlas.sh`. Fold v0 into v1 only after the golden/atlas tests compare verdicts (physics-sensitive: verdict semantics).
4. yagni `scripts/aggregate_profiled_boundary.py:1` (384): test-only caller; same era as the profiled scan.
5. yagni 3 wrappers that only call `main()`: `scripts/run_adaptive_m2_mesh.py:1` (8), `run_survivor_adaptive_12520.py:1` (6), `aggregate_survivor_adaptive_12520.py:1` (9). `python -m dhb.adaptive_m2_mesh` does the same. Keep only if a doc quotes the script path.
6. delete config keys nobody reads: `profile.sampler` and `physics.mass_convention_id` in five configs under `configs/` (`adaptive_m2_boundary_v1.yaml`, `…_extension.yaml`, `adaptive_m2_exploration_v1.yaml`, `profiled_m2_boundary_v1.yaml`, `survivor_adaptive_12520_v1.yaml`). The mass convention is read from the dihiggs authority via `_mass_convention()` (`adaptive_m2_mesh.py:358`), not from this key, so the key is a decoy: physics-sensitive. `theory_atlas_v0.yaml` has 23 unread keys because the whole file is unread.
7. stdlib 6 sha256 copies: `python/dhb/adaptive_exploration.py:21`, `adaptive_m2_mesh.py:47`, `enrich.py:77`, `survivor_adaptive_campaign.py:41`, `scripts/aggregate_profiled_boundary.py:82`, `archive_adaptive_m2_boundary.py:15`, plus 3 in golden scripts/tests.
8. shrink `src/evaluate_point.cpp:1` (828) and `tests/test_golden_evaluate_point.py:1` (785): leave, golden oracle (N2 gate).
9. native `dataset/hbdataset-v1.7/**/*.py`: vendored HiggsBounds data scripts, out of scope.

### dihiggs_hep_cross
1. delete R9/R10 scripts 2,198 (#4).
2. delete `run_mass_jet_control_campaign.py` + test 1,403 (#5).
3. delete photonic/pilot/scale 1,000 (#9).
4. delete `bootstrap_llp_recast.sh` 657 (#11).
5. yagni numbered chain `scripts/03_…`, `04_…`, `05_…`, `08_…`, `09_link_2hdmc_to_diphoton.py` (1069), `10_…`, `11_…`, `13_h2_benchmark_handoff.py` (257) ≈ 2,900 lines: Makefile- and test-wired diphoton campaign (Aug/Sep). Nothing downstream of arrow 8 reads their outputs. Candidate for archive; **owner decision**, physics-sensitive.
6. delete config keys: `state/CURRENT_CAMPAIGN.yaml` `coupling_prescriptions.*` (28 keys incl. `PI_simplified.implemented`, `effective_m22_shifted.ufo_vertex_mapping_status`): no code reads `coupling_prescriptions`. They record authority status, so keep as documentation (move to a `.md`) or add a reader. physics-sensitive.
7. stdlib 10 sha256 copies: `scripts/13_h2_benchmark_handoff.py:33`, `r10_ctau_efficiency_scan.py:54`, `r9_build_iteration1.py:86`, `r9_ingest_madgraph_scaling.py:34`, `r9_run_model_scan.py:83`, `run_mass_jet_control_campaign.py:157`, `run_physical_point_madgraph.py:123`, `verify_r10_effective_scan.py:25`, `verify_r9_artifacts.py:19`.
8. shrink `git_head` at `scripts/run_mass_jet_control_campaign.py:167` and `dihiggs_llp_recast/scripts/check_upstream_layout.py:15`: both are `subprocess.run(["git","rev-parse","HEAD"])`; keep one.

### dihiggs_llp_recast
Lean already apart from two stubs.
1. delete `scripts/extract_lhe_summary.py:1` (50), `scripts/run_upstream_benchmark.sh:1` (17): no callers.
2. keep `scripts/make_aeff_grid_products.py:1` (229) and `scripts/run_aeff_grid_mission.py:1` (334): no repo reference, but DATA_FLOW names the first as the A_eff owner. Entry points, not dead. physics-sensitive.
3. stdlib `sha256`/`sha256_of` at `scripts/audit_strong_bm1_cards.py:19`, `build_r8_artifact_manifest.py:34`, `make_aeff_grid_products.py:37`, `run_aeff_grid_mission.py:53`, `verify_r8_artifacts.py:59`, `tests/test_strong_bm1_cards.py:11`; `src/dvrecast/manifest.py:1` (319) may already offer one, reuse it.
4. yagni `src/dvrecast/readiness.py:1` (198) and `r8_*` vs non-`r8_` pairs (`cutflow.py` / `r8_cutflow.py`, `geometry` / `r8_geometry.py`): two generations of the same step. physics-sensitive; review before folding.

### dihiggs_ufo
1. shrink `LLscalar_v3_UFO_original` ↔ `r14_runtime` byte-identical files 2,268 (#3).
2. delete `evidence/pack_a/…/{parameters,particles}.py` 1,134 (#7).
3. delete `curation/repository_cleanup_20260723T081927Z/*.py` 364 (#13), plus `review/cycle_*`, `review/event_bundle_cycle_*`, `curation/…/review/` (30+ md/json review transcripts, history only).
4. yagni `results/generator_closure/*/reproduce.sh` (5 files, 274 tracked files in total): results, not code, but they live in git rather than lake. physics-sensitive (closure σ evidence).
5. yagni `releases/pack_aa/` (802 files, 588 json): data in git; N3-style move to lake.
6. delete config keys: `studies/pack_a_seed_mc/config/ensemble_contract_v1.yaml` has 17 keys no code reads (`checkpoints.*`, `determinism_control.*`, `resource_isolation.*`, `seed_list`, …). The file is loaded (`config.py:19`), so the keys are documentation-in-YAML; trim to the keys the code uses. `studies/pack_aa_kinematic_validation/config/default.yaml`: `tolerances.d0_decay_closure.relative_momentum_tolerance`, `tolerances.d1_decay_closure` unread (physics-sensitive: closure tolerances).
7. stdlib 8 sha256 copies: `pack_aa/python/pack_aa.py:37`, `prepare_input.py:18`, `pack_b/operator/build_model_derived.py:57`, `pack_b_preflight.py:19`, `pack_b/tests/test_pack_b_preflight.py:15`, `studies/generator_closure.py:33`, `pack_a_worker.py:28`, `run.py:41`.

### recast_viewer
1. native drop devDependency `playwright-core` (`frontend/package.json:20`): no import anywhere in tracked source. -1 dep.
2. stdlib 3 sha256 copies: `preprocess/adapters/h2_mass_control.py:172`, `local_instrumented_reference.py:40`, `original_recast.py:236`. Put one in `preprocess/schema.py` instead of three.
3. yagni `frontend/src/i18n.ts:1` (103) + its call sites: verify a second language is shipped, otherwise inline the strings.
4. shrink three adapters `h2_mass_control.py` 661, `original_recast.py` 479, `local_instrumented_reference.py` 366 each re-implement `_load`/`_sha256`: share the loader. Not dead; lines saved ≈100, low confidence.

## Dead scripts never referenced (grep for callers)

Method above. Listed per repo; "entry point" rows are kept.

| Repo | Script | Lines |
|---|---|---|
| boundary | `scripts/aggregate_survivor_adaptive_12520.py`, `archive_adaptive_m2_boundary.py`, `compare_serial_vs_sharded_smoke.sh`, `inspect_tiny_boundary.sh`, `keep_working_lhs_campaign.sh`, `plot_campaign_pixels.py`, `run_adaptive_exploration.py`, `run_adaptive_m2_mesh.py`, `run_survivor_adaptive_12520.py`, `smoke_evaluate_point.sh`; module `python/dhb/classify.py` | 9, 68, 64, 45, 120, 177, 8, 8, 6, 64; 50 |
| hep_cross | `bootstrap_llp_recast.sh`, `campaigns/20260901_photonic_requalification/…/run_mg_xsec_masses.sh`, `…/scripts/calc2hdmc.py`, `scripts/r10_generate_summary.py`, `run_pilot_study.py`, `save_and_plot.py` | 657, 202, 143, 114, 74, 158 |
| llp_recast | `scripts/extract_lhe_summary.py`, `run_upstream_benchmark.sh`; entry points kept: `make_aeff_grid_products.py`, `run_aeff_grid_mission.py` | 50, 17 |
| dihiggs | `benchmarks/run_first_h2_bounded_scan.py`, `campaigns/t2_t4_…/scripts/{compare_legacy_decay_regression,finalize_calculator_scan_reports}.py`, `chris/build_*.sh`, `dihiggs/batch_scan.py`, 5 in `mlpython/lake_pipeline/`, 9 in `scripts/`, 3 in `studies/llp_families_20261019/` (checks, wire to tests), 2 in `studies/lambda7_tables_20261014/*.sh` | see lists above |
| ufo | `curation/repository_cleanup_20260723T081927Z/*.py` | 364 |
| recast_viewer, root | none | — |

## Duplicated helpers across modules (same function in 2+ repos)

| Helper | Where | Physics-sensitive? |
|---|---|---|
| `sha256` / `sha256_file` / `_sha256` / `sha256_of` | 47 definitions in dihiggs 6, boundary 9, hep_cross 10, llp_recast 7, ufo 8, recast_viewer 3 (listed per repo above) | no |
| `ctau_mm_from_width_gev` | `dihiggs/mlpython/lake_pipeline/physics_conventions.py:48`, `dihiggs_hep_cross/src/llp_recast/recast_math.py:9` | **yes**: cτ = ħc/Γ; same constant, two readers. After N1 only `constants.py` in hep_cross reads the YAML; `lake_pipeline` carries pinned literals as fallback |
| `ctau_tag` | `dihiggs_hep_cross/scripts/r10_ctau_efficiency_scan.py:62`, `dihiggs_llp_recast/scripts/run_aeff_grid_mission.py:61` | yes (names result directories by cτ; a format drift breaks lookups) |
| `sigma_4b_fb`, `visible_sigma_fb` | `dihiggs_hep_cross/src/llp_recast/r9_threshold.py:45,50`, `dihiggs_llp_recast/src/dvrecast/r8_normalization.py:24,31` (different signatures: pb+BR² vs fb+A_eff) | **yes**: σ(H2H2)·BR(bb)²·A_eff. One definition belongs in llp_recast (A_eff owner); hep_cross imports it |
| `git_head` / `_git` | `hep_cross/scripts/run_mass_jet_control_campaign.py:167`, `llp_recast/scripts/check_upstream_layout.py:15`, `boundary/python/dhb/profiled_m2_scan.py:42`, `llp_recast/tests/test_manifest.py:10` | no |
| `_load_manifest`, `_load_conventions`, `_mass_convention`, `_finite`, `_to_float`, `write_csv`, `sanitize_run_name`, `determine_status`, `parse_csv_floats` | 2–3 repos each (dihiggs/boundary/hep_cross/ufo); `_mass_convention` in boundary `adaptive_m2_mesh.py` and hep_cross | `_mass_convention`, `_load_conventions`, `determine_status` yes (authority) |
| `classify_row` | `boundary/python/dhb/atlas.py:201`, `atlas_v1.py:116` | yes (atlas verdicts) |

## Config keys nobody reads

- boundary: `profile.sampler`, `physics.mass_convention_id` (5 configs); all 23 keys of `configs/theory_atlas_v0.yaml` (file read by nothing).
- hep_cross: `state/CURRENT_CAMPAIGN.yaml` `coupling_prescriptions.*` (28 keys, authority status text).
- ufo: 17 keys of `studies/pack_a_seed_mc/config/ensemble_contract_v1.yaml`; 2 tolerance keys in `studies/pack_aa_kinematic_validation/config/default.yaml`.
- llp_recast, dihiggs: none found by the key scan (`conventions`, `configs` read by name). The scan matches key strings only, so a key read via `**cfg` or a dynamic getter would show as unread; check the owner before deleting. Rows marked physics-sensitive above need an owner.

## Abandoned campaign code (summary)

- dihiggs: `autoresearch/`, t2_t4 scripts, `scripts/*christopher*`, `chris/`, lake_pipeline plot/audit scripts.
- boundary: LHS refined-boundary chain, `adaptive_exploration`, profiled aggregate, atlas v0.
- hep_cross: R9/R10 sensitivity campaign, mass-jet control campaign, photonic requalification, numbered diphoton chain 03–13, pilot/scale scripts.
- ufo: July cleanup curation, review cycles, failed-native evidence.
- llp_recast: none beyond two stubs.

## What I did not check

Whether `autoresearch/` has an off-repo consumer (it is wired to the Gemini worker loop). Runtime-only callers (notebooks, shell history, cron, Makefile targets in the root). Python ≥ 3.11 for `hashlib.file_digest` in every module (higgstools declares 3.6 but is vendored). Neither the 4 pre-existing boundary test failures nor the golden mismatch were rerun. No test was run; this audit changed nothing.
