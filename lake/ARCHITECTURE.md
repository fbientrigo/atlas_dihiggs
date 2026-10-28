# lake architecture

This file covers the end-to-end exploration pipeline, what each part owns, and where today's code differs from the target. Every number here was measured on 2026-10-27 from the metadata mirror (`~/.cache/lake/store`, 46 commits) with `lake.py ... --offline`.

## Flow

```
 dihiggs (canonical evaluator, 2HDMC)            lambda7 is a fixed config scalar, not a scan axis
        │  one dihiggs.point.v2 row per (leaf, profile proposal)
        ▼
 dihiggs_boundary  run  ──►  data/runs/<campaign>/  or  campaigns/survivor_*/
   (adaptive mesh: tan_beta slice × m_phi×Mbar rectangle "leaf";       raw_*_points.csv/.parquet  (all rows, lossless)
    16 LHS proposals in (X=lambda6·tanb, Delta) per leaf;              *_leaves.csv, *_state.json, manifest.json
    leaf has_survivor = any theory_ok_v1 == 1)
        │
        ▼  lake sync  (sources.tsv: dir → authority, prune, NAME=GLOB tables)
 remote  dihiggs_lake:store   (immutable, add-only)
   blobs/<sha256>.tar.zst      every file, lossless       ← restore / physics claims
   manifests/<cid>.json.gz     per-file sha256
   tables/<name>/commit=<cid>  Parquet copy of the point/leaf files
   commits/<cid>.json          authority, committer git, producer_git, conventions (new)
        │
        ▼  lake query / lake explored  (local mirror of commits/ + tables/, never blobs)
 views:  commits · <one per table> · regimes (per commit) · explored (per campaign × leaf)
        │
        ▼
 lake explored --lambda7 L --mh M --export explored.csv      (one row per leaf × commit, plain CSV)
        │
        ▼
 next run  survivor v2 --explored explored.csv: leaves already explored in this regime start from their counts
           (no --explored: resumes from its local campaign_state.json, which sources.tsv now never prunes)
```

## Who owns what

| Piece | Owns | Does not own |
|---|---|---|
| `dihiggs` | evaluating one point, mass convention (`physics_authority.convention_provenance`) | what to evaluate next |
| `dihiggs_boundary` | choosing points, leaf geometry, its own leaf verdicts (`coverage_state`, `decision_state`) | storage after the run |
| `lake.py` | lossless copies, verified deletes, the queryable index, and the `explored` coverage view | any physics rule beyond counting `theory_ok_v1` |
| `sources.tsv` | which local dir goes to which commit, its authority, whether it can be pruned, and which files become tables | — |

## The explored view (`lake.py:361-436`)

The `explored` view is computed from every table that has the point columns (`POINT_COLUMNS`): `boundary_points`, `boundary_seed_points` and `survivor_points` today. A new campaign table with these columns is picked up automatically. The view adds no storage and has no write path, so it can never fall out of sync with the points.

- One row per (regime, campaign, commit, leaf) holds the rectangle bounds, `n_points`, `n_valid` and `best_point_id` (the valid point with the largest |g_physical_hphiphi|).
- `status`:
  - `valid` means `n_valid > 0`.
  - `excluded` means 0 valid points out of at least 64. That is the boundary survivor campaign's `zero_success_max_attempts` (`tested_empty_95`), and it puts the one-sided 95% upper bound on the valid fraction below 4.6%.
  - `unknown` covers everything else. `upper95_valid_fraction` is always shown, so you can apply your own threshold.
- The regime is given by `lambda7` and `mh_GeV` (measured per row), plus `producer_commit`, `convention_id` and `convention_sha256` from `regimes`.
- `regimes` has one row per commit and is built in Python from `commits/*.json`. Old records have no `conventions`, so they get NULL there (backward compatible, tested).

```
python lake/lake.py explored --offline                                    # coverage per regime/status
python lake/lake.py explored --lambda7 nonzero --mh 125.2 --tan-beta 1e5 --mphi 150 --mbar 160
#   prints the leaves containing the point; exit 1 + "not explored" if none
```

The measured result today: all 1,327,904 boundary rows are lambda7 = 0. The run is mh 125.13 (historical) plus mh 125.20 (survivor v2), with tan_beta 1e2…1e7 and m_phi, Mbar in [130, 350] GeV. There are 0 leaves for lambda7 ≠ 0.

## Safety rules (enforced in code and tested in `test_lake.py`)

1. Remote objects are only ever added. No verb deletes or rewrites them.
2. `prune` deletes a local file only if all of these hold:
   - the remote md5 of every object verifies;
   - size, sha256 and the mtime cutoff all match;
   - the file is **not git-tracked** (`tracked()`, which uses `git ls-files --recurse-submodules`).

   If git cannot answer, prune refuses.
3. `prune` only rmdirs directories that it emptied, deepest first, and never the root.
4. A commit record is written only after the objects it names are verified.
5. `restore` refuses to overwrite a file whose content differs from the commit.
6. `sync` does not prune a commit whose root contains a nested `keep` row.
7. `prune` (direct or via `sync`) never deletes a file whose basename matches a `-GLOB` of a `sources.tsv` row at, above or below the commit root. The boundary rows are `yes -*_state.json -*.yaml`, which keeps the state a resumed run reads and the campaign config. The 2026-10-13 sync pruned `campaigns/survivor_adaptive_12520_tanbeta_v2/campaign.yaml`, so 3 boundary tests fail on a fresh checkout until it is restored from `8292bb`.
8. `sync` never commits a git-tracked file: git owns it (`test_lake.py` `sync_skips_tracked`). Older commits of repo-wide `keep` rows still hold tracked files; see `docs/DATA_FLOW.md` C3.

### Data-loss paths found and fixed

| # | Path | Fix |
|---|---|---|
| 1 | `cmd_prune` deleted git-tracked files. This is the 2026-10-13 hep_cross deletion of 379 tracked files. | git-tracked guard |
| 2 | `cmd_prune` `os.walk(root)` rmdir'd every empty dir under root. That included empty dirs inside a `.git` (`refs/tags`, `objects/info`), which can corrupt a repo, plus intentionally empty dirs and root itself. | rmdir only the parents of deleted files |
| 3 | `cmd_restore` extracted over existing files, which silently replaced newer local edits (e.g. restoring into a module). | refuse on differing content, `--skip-old-files` |
| 4 | `cmd_commit` wrote `commits/<cid>.json` before verifying. A failed or partial upload left a record, so `sync` treated the files as covered and never re-uploaded them. Prune still refused, but the data was never safely in the remote. | verify, then write the record |
| 5 | `cmd_sync` checked only rows at or above the commit root, so a `keep` row nested under a prunable root was ignored. | nested rows count too |

`lake.py` went from 392 lines before this change to 486 after: +94 lines, of which the explored, regimes and CLI code is about 70. Task H (export, compact, keep globs) brought it to 523; option (b) made it 524.

## lambda7 status of the hep_cross groups pruned on 2026-10-13 (measured, nothing restored)

Evidence for these verdicts:
- the forensics restores of `f72af7`/`a347d8`, which lake sha256-verified;
- `git grep` at hep_cross `HEAD` for `results/` and `artifacts/`, whose files are sha-equal to the lake copies;
- every CSV column matching `lambda_?7|lam7|l7`, tabulated by value.

| Group (cid) | Verdict | Evidence |
|---|---|---|
| `campaigns/20260901_photonic_requalification` (`f72af7`) | **lambda7 = 0, superseded** | 21 CSVs with a lambda7 column, every value 0 (`validated/photonic_requalified.csv`, `work/targets.csv`, `work/calculator_runs/*/{in,out}*.csv`) |
| `campaigns/physical_vs_effective_coupling_v1` (`a347d8`) | **Mixed.** Benchmark products are lambda7 = 0; the validation of the general coupling formula is lambda7-general. | lambda7 = 0: `inputs/benchmark_points.csv` (3/3), `m2_study/*.csv` (85/85). lambda7 ≠ 0 test points: `validation/numerical_crosschecks.csv` (−0.03, 0.02, 0.05, 0.01), `validation/SOL_HIGH_INDEPENDENT_NUMERICS.csv`, `source_level_coupling_audit/*` (0.21, 0.05, −0.06, −0.9), plus the 2HDMC `THDM.cpp` patch. The derivation and validation code is not superseded. |
| `results/` (`7e0782`) | **lambda7 = 0 wherever a 2HDM point is recorded; the rest is lambda7-agnostic** | Every lambda7 value in `git grep HEAD -- results` is 0 (`pilot_points_input.json`, `presentation_update/{manifest.json,points.csv}`, `presentation_update_v2`, `r9…/model_scan_provenance.json`). `r10` effective-coupling scan, `scale_cards`, `pilot_cards`: effective ctau/g/BR inputs, no 2HDM parameters (lambda6/tanb appear in 1 of 71 r10 files, 0 of 25 card files). |
| `artifacts/` (`9752fb`) | **lambda7 = 0, superseded** | The single point `H2scan_mH150_tb300000` traces to `point.json` → dihiggs `92ad4d8:benchmarks/FIRST_H2_RECAST_CANDIDATE.json`, which has `"lambda7_input": 0.0` |

These groups have no lake tables, so `lake query` cannot see their parameters. The verdicts come from file content, not from the catalog.

## Precision policy

Rule: anything that feeds a physics claim stays lossless in the blob. Every committed file is in `blobs/` byte-for-byte and sha256-checked on restore. Tables are an index and can be rebuilt from blobs.

Implemented (P3, option (b), chosen by the user 2026-10-27; opt-in per table, new commits only): `NAME=GLOB@compact` in `sources.tsv`. `compact()` splits the table into two parts:
- `part-0` holds the valid rows (`theory_ok_v1 = 1`), unchanged. It is written even when empty, so the output columns stay in the table schema (`explored` needs `g_physical_hphiphi_GeV`).
- `part-1` holds every other row, but only the columns in the `COMPACT_KEEP` allowlist, unchanged: `campaign_id`, `run_id`, `point_id`, `yukawa_type`, `*_input*` (tan β, masses, sin(β−α), M², m12², λ6, λ7, mh), `m_phi_GeV`, `M_plot_GeV`, `X_lambda6_times_tan_beta`, `lambda6_from_X`, `Delta_heavy_GeV`, `profile_index`/`profile_replicate`/`profile_seed`, `outer_cell_id`/`outer_*_index`, `mesh_*`, the `*_min_GeV`/`*_max_GeV` bounds, `theory_ok_v1`, and the rejection code `rejection_stage`/`rejection_reason`.

A stored invalid point is the record that it was already run, so these columns stay exact; nothing is quantized. The rejection code is the existing `rejection_reason` string (`check_positivity_false`, `check_unitarity_false`, `check_perturbativity_false`), which Parquet stores dictionary-encoded, so it costs about nothing. Every other column of an invalid row (reconstructed couplings, widths, BRs, ctau, check flags) is dropped from the table and stays in the blob: `SELECT width_* … WHERE theory_ok_v1 = 0` returns NULL on compact commits, and `lake restore` gives the full rows. `test_lake.py` checks that:
- valid rows are bit-identical;
- the kept columns of invalid rows are bit-identical (tan β = 1e7 + 0.617…), the rest are NULL, the reason code is present;
- an input-key join between a plain commit and a compact commit matches every row;
- `explored` gives the same rows for a plain and a compact commit, and `--export` is unchanged;
- a table with no valid row still writes the (empty) valid part.

Enabled for `boundary_points` and `survivor_points`. Option (a), float32 outputs, is removed: one mode is simpler than two. Remote tables already written are not rewritten; any commit tagged `"compact": "invalid_outputs_float32"` stays readable as it is.

Measured with `compact()` on the concatenated mirror tables (read-only), and checked with `EXCEPT ALL` against the source: 0 differing rows in the valid part and in the kept columns of the invalid part.
- `boundary_points`: 163.4 MB → **22.8 MB** (5.6 valid + 17.2 invalid), −86%.
- `survivor_points`: 19.6 MB → **8.7 MB** (4.0 + 4.8), −56%.

### Measured on the local mirror (read-only; outputs in `/tmp/lake_p3`)

Each table was concatenated into one zstd Parquet file, and each option was applied to that file.

| Option | `boundary_points` (1,225,856 rows, 3.4% valid) | `survivor_points` (102,048 rows, 21.2% valid) | Lossy in the table? |
|---|---|---|---|
| today (float64, all rows) | 163.4 MB | 19.6 MB | — |
| (a) float32 invalid outputs (removed) | 87.0 MB (5.6 valid + 81.3 invalid), −47% | 14.1 MB, −28% | invalid outputs at 1e-7 relative |
| (b) invalid rows keep only inputs + `rejection_stage`/`rejection_reason` (**implemented**; predecessor's denylist variant) | 23.1 MB, −86% | 9.4 MB, −52% | invalid outputs gone from the table, still in the blob |
| (c) invalid rows → per (leaf, `profile_seed`) list of `profile_index` | 6.2 MB, −96% | 4.0 MB, −80% | inputs must be regenerated |
| (d) lossless: sort by leaf, zstd level 3 / 9 / 19 | 163.4 / 163.1 / 154.9 MB | 19.6 / 19.5 / 18.5 MB | no |
| (a)+(d) zstd 19 | 81.4 MB | 13.6 MB | as (a) |

On (c), proposals are deterministic. `_contexts()` was re-run with the restored `campaign.yaml` and `campaign_state.json` of `8292bb`, and it regenerated 100,000 of 100,000 survivor rows bit-exactly: `X`, `Delta`, `lambda6_from_X` and `profile_seed`. Regenerating still needs the exact config, the leaf geometry and the same `_lhs`/`_contexts` code. A code change would silently change what "already run" means.

**Recommendation.** For the stated purpose, knowing exactly what ran so it is never re-run, (b) is the better compression. It keeps every input exact and keeps the rejection reason, and it is 3.8× smaller than (a) on `boundary_points`. Each invalid point's outputs stay one `restore` away in the blob. (c) is smaller still, but it ties the meaning of the table to a code version, so it is not recommended. (d) alone is not worth it, at ≤5%. The user chose (b); it is now what `@compact` means.

## Gaps between the target and today's code

1. **lambda7 ≠ 0 is not explored by the boundary pipeline.** Every boundary config pins `lambda7: 0.0`:
   - `dihiggs_boundary/configs/adaptive_m2_boundary_v1.yaml:13`
   - `survivor_adaptive_12520_v1.yaml:10`
   - `adaptive_m2_exploration_v1.yaml:13`
   - `profiled_m2_boundary_v1.yaml:11`

   It is passed through as a constant (`adaptive_m2_mesh.py:220`, `survivor_adaptive_campaign.py:220`), not scanned. The lambda7 ≠ 0 work lives in `dihiggs/campaigns/lambda7_*` (`BENCHMARKS.csv`, `LAMBDA7_AB_COMPARISON.csv`). That data uses another schema, has no table in `sources.tsv`, and does not show up in `explored`.
2. **"Valid" means theory-valid only.** `_theory_ok` (`profiled_m2_scan.py:35`) checks only `theory_ok_v1 == 1`. Over all point rows, `sum(experimental_evaluated) = 0`, so HiggsBounds/HiggsSignals (`runner.py`) never ran on these campaigns.
3. **A region is 2-D per tan_beta slice.** lambda6 (via X) and Delta are profiled inside each leaf with 16 LHS proposals (`adaptive_m2_mesh.py:327`). So `explored` answers whether the (tanb, m_phi, Mbar) box was explored, not which (lambda6, Delta) were tried. The rows answer the second question.
4. **The next run asks the lake: survivor v2 only (P1, done).** `survivor_adaptive_campaign --explored <export.csv>` seeds leaves; `sources.tsv` keeps `*_state.json`. Not wired: the older `adaptive_m2_mesh` and `adaptive_exploration` (`_occupied`, `adaptive_exploration.py:51`), which still read local state only, and the v1 survivor campaign (refuses `--explored`).
5. **Per-row producer provenance is missing.** `producer_commit` is `"unknown"` in 100% of rows. The producer is known only from the run manifest, via `commits.producer_git` → `regimes.producer_commit`.
6. **The convention SHA is missing for old commits.** `mass_convention_authority` sits inside the run manifests, which are in blobs only. New commits capture it as `conventions`. For old commits, `mh_input_GeV` per row (125.13 vs 125.20) is the measured proxy.
7. **There are two leaf vocabularies.** The boundary writes `coverage_state` (`adaptive_m2_mesh.py:133`) and `decision_state` (`survivor_adaptive_campaign.py:191`) with different rules. Lake recomputes one `status` from the points, and the boundary's own labels remain in the `boundary_leaves` and `survivor_leaf_aggregate` tables.

## P1: how the next run reads coverage (dihiggs_boundary `main`, f2b81cd)

`lake explored [filters] --export FILE.csv` writes the view as plain CSV. DuckDB writes shortest round-trip floats, and tan β ≈ 1e7 round-trips exactly (tested). The boundary run reads that CSV with the stdlib, so it never imports lake, DuckDB or rclone.

`survivor_adaptive_campaign.load_explored(path, cfg, convention_id)` keeps a row only when all of these hold:
- `lambda7` equals the config value exactly;
- `mh_GeV` equals it within a relative 1e-9;
- `convention_id` equals the evaluator's, when the lake knows it. The 2026-10-13 commits have none, so there `mh` is the proxy.

It keys the row by the leaf id **and** its rectangle and tan β. Otherwise a mesh with another `root_cells` (the smoke run uses 4, production uses 20) would reuse the same id strings for different boxes. Across commits and campaigns it takes the max `n_points` per leaf, not the sum. A growing campaign re-commits its earlier rows, and undercounting only re-runs a batch (`ponytail:` note in the code).

`_seed()` sets `prior_attempts`, `prior_successes` and `prior_best_point_id` on each leaf the run creates: the roots of a fresh state, and every refinement child. `_update_leaf()` adds the prior counts to the local rows. As a result:
- an explored leaf is not batched;
- an excluded leaf (≥ 64 attempts, 0 valid) is never eligible;
- a valid leaf keeps refining as before;
- a partial leaf continues at replicate `ceil(attempts / batch)`, with a fresh LHS seed.

Seeded attempts count toward the slice quota. The manifest records `explored_seed` (sha256, matched and seeded leaves, seeded attempts).

### End-to-end demo

This used the real 2HDMC evaluator, the smoke v2 config restored from `8292bb`, the tan β = 1e7 slice and a local-dir remote, in the scratchpad `demo/`.

| Run | `--explored` | Fresh evaluations | Seeded |
|---|---|---|---|
| 1, λ7 = 0 | — | 256 (43 valid; the other rows were rejected at the positivity, unitarity or perturbativity stage) | 0 |
| `lake commit … survivor_points=…csv@compact` → `explored --lambda7 0 --export` | | 16 leaves (4 valid, 12 unknown), convention `mh_125p20_active_2026` | |
| 2, λ7 = 0, fresh dir | yes | **0** | 16 leaves / 256 attempts |
| 3, λ7 = 0.01 | yes (same file) | **256**, not blocked | 0 matched |

`lake explored --lambda7 nonzero --tan-beta 1e7 --mphi 150 --mbar 160` then reports `not explored` (exit 1). Test: `dihiggs_boundary/tests/test_survivor_explored_seed.py`, with a fake evaluator. It checks the skip, that λ7 ≠ 0 is not blocked, that a convention mismatch is ignored, and that a partial leaf continues.

## Restore experiment (2026-10-27)

`lake.py restore 20261013T001001Z-a347d8` (`hep_cross campaigns/physical_vs_effective_coupling_v1`) restored 214 files in 15.1 s wall time to a scratch dir. It used 0.8 s CPU and 68 MB RSS, and the 1.16 MB blob came from Drive. 214/214 files match the manifest sha256 when re-hashed independently.

Compared with `dihiggs_hep_cross` HEAD `df95b4b51`:

| Category | Files | Where |
|---|---|---|
| equal | 104 | `2hdmc_build` 73, `ufo` 16, `validation` 5, `derivation` 3, `madgraph_smoke` 3, `inputs` 2, `README.md`, `TEAM_COUPLING_BRIEF.md` |
| differ | 22 | `2hdmc_build` 10 (binaries, `THDM.cpp/h`, `Makefile`), `coupling_comparison` 5, `m2_study` 5, `COUPLING_STUDY_REPORT.md`, `logs` 1 |
| lake-only | 88 | `source_level_coupling_audit` 55, `validation` 19, `2hdmc_build` 10, `coupling_comparison` 2, `ufo` 1, `SOURCE_LEVEL_HPHIPHI_DERIVATION.md` |
| git-only | 2 | `coupling_comparison/make_plot{,_M2}.py` |

Nothing was copied into the module.

## Proposals (user decision)

- **P1.** Done for the survivor v2 campaign. See above.
- **P2.** Add tables for the lambda7 ≠ 0 campaigns (`dihiggs/campaigns/lambda7_*`, currently `keep` with no tables). They have no mesh columns, so they would appear in `commits` but not in `explored`. A lambda7 ≠ 0 boundary run (a config with `lambda7` ≠ 0, or lambda7 as a scan axis) is what would populate `explored`.
- **P3.** Done: `@compact` is option (b), invalid rows keep inputs, ids and rejection reason (see Precision policy). Option (a) was removed.
- **P4.** Retire superseded lambda7 = 0 data by authority label (`historical`), not by deletion. The blobs are the only copy of the 30 newer hep_cross files (forensics §1).
- **P5.** Done: `site/src/content/docs/lake.md` covers the safety rules, regimes, explored, compact tables and the `--explored` loop.
