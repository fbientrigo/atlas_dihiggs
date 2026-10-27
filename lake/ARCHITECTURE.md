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
 next run  ── today: reads its own local *_state.json, NOT the lake (gap 4)
```

## Who owns what

| Piece | Owns | Does not own |
|---|---|---|
| `dihiggs` | evaluating one point, mass convention (`physics_authority.convention_provenance`) | what to evaluate next |
| `dihiggs_boundary` | choosing points, leaf geometry, its own leaf verdicts (`coverage_state`, `decision_state`) | storage after the run |
| `lake.py` | lossless copies, verified deletes, the queryable index, and the `explored` coverage view | any physics rule beyond counting `theory_ok_v1` |
| `sources.tsv` | which local dir goes to which commit, its authority, whether it can be pruned, and which files become tables | — |

## The explored view (`lake.py:335-406`)

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

### Data-loss paths found and fixed

| # | Path | Fix |
|---|---|---|
| 1 | `cmd_prune` deleted git-tracked files. This is the 2026-10-13 hep_cross deletion of 379 tracked files. | git-tracked guard |
| 2 | `cmd_prune` `os.walk(root)` rmdir'd every empty dir under root. That included empty dirs inside a `.git` (`refs/tags`, `objects/info`), which can corrupt a repo, plus intentionally empty dirs and root itself. | rmdir only the parents of deleted files |
| 3 | `cmd_restore` extracted over existing files, which silently replaced newer local edits (e.g. restoring into a module). | refuse on differing content, `--skip-old-files` |
| 4 | `cmd_commit` wrote `commits/<cid>.json` before verifying. A failed or partial upload left a record, so `sync` treated the files as covered and never re-uploaded them. Prune still refused, but the data was never safely in the remote. | verify, then write the record |
| 5 | `cmd_sync` checked only rows at or above the commit root, so a `keep` row nested under a prunable root was ignored. | nested rows count too |

`lake.py` went from 392 lines before this change to 486 after: +94 lines, of which the explored, regimes and CLI code is about 70.

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

Implemented: nothing lossy. Measured options for the 156 MB `boundary_points` table (1.23M rows, 3.4% theory-valid):

| Option | Table size | Saving | Risk |
|---|---|---|---|
| today (float64, all rows) | 156 MB | — | — |
| float32 for invalid rows | 76 MB invalid + 5 MB valid | ~49% | Loses the 1e-6-level residuals, e.g. the lambda1/m12 round-trip diagnostics that rejection analysis uses |
| keep only valid rows in tables; invalid → `explored` counts | 5.4 MB | ~96% | `count(*)` and rejection-reason queries change meaning, and need a blob restore to recover |

Both options are lossless overall, because the blob keeps everything. Both still change what table queries return, so they are listed as proposals.

## Gaps between the target and today's code

1. **lambda7 ≠ 0 is not explored by the boundary pipeline.** Every boundary config pins `lambda7: 0.0`:
   - `dihiggs_boundary/configs/adaptive_m2_boundary_v1.yaml:13`
   - `survivor_adaptive_12520_v1.yaml:10`
   - `adaptive_m2_exploration_v1.yaml:13`
   - `profiled_m2_boundary_v1.yaml:11`

   It is passed through as a constant (`adaptive_m2_mesh.py:220`, `survivor_adaptive_campaign.py:220`), not scanned. The lambda7 ≠ 0 work lives in `dihiggs/campaigns/lambda7_*` (`BENCHMARKS.csv`, `LAMBDA7_AB_COMPARISON.csv`). That data uses another schema, has no table in `sources.tsv`, and does not show up in `explored`.
2. **"Valid" means theory-valid only.** `_theory_ok` (`profiled_m2_scan.py:35`) checks only `theory_ok_v1 == 1`. Over all point rows, `sum(experimental_evaluated) = 0`, so HiggsBounds/HiggsSignals (`runner.py`) never ran on these campaigns.
3. **A region is 2-D per tan_beta slice.** lambda6 (via X) and Delta are profiled inside each leaf with 16 LHS proposals (`adaptive_m2_mesh.py:327`). So `explored` answers whether the (tanb, m_phi, Mbar) box was explored, not which (lambda6, Delta) were tried. The rows answer the second question.
4. **The next run does not ask the lake.** `adaptive_exploration._occupied` (`adaptive_exploration.py:51`) and `survivor_adaptive_campaign._historical_rectangles` (`:106`) read local `*_state.json` files. Those are exactly the files `sync --yes` prunes (`data/runs`, `campaigns/survivor_*` are `prune=yes`), and today `dihiggs_boundary/campaigns/` is empty. See proposal P1.
5. **Per-row producer provenance is missing.** `producer_commit` is `"unknown"` in 100% of rows. The producer is known only from the run manifest, via `commits.producer_git` → `regimes.producer_commit`.
6. **The convention SHA is missing for old commits.** `mass_convention_authority` sits inside the run manifests, which are in blobs only. New commits capture it as `conventions`. For old commits, `mh_input_GeV` per row (125.13 vs 125.20) is the measured proxy.
7. **There are two leaf vocabularies.** The boundary writes `coverage_state` (`adaptive_m2_mesh.py:133`) and `decision_state` (`survivor_adaptive_campaign.py:191`) with different rules. Lake recomputes one `status` from the points, and the boundary's own labels remain in the `boundary_leaves` and `survivor_leaf_aggregate` tables.

## Proposals (user decision)

- **P1.** Make the next boundary run read coverage from `lake explored`, or from a Parquet export of the view, instead of local state files. Until then, do not `sync --yes` a campaign whose state a follow-up run needs. That needs a small hook in `dihiggs_boundary`. It is not written because no follow-up campaign exists yet.
- **P2.** Add tables for the lambda7 ≠ 0 campaigns (`dihiggs/campaigns/lambda7_*`, currently `keep` with no tables). They have no mesh columns, so they would appear in `commits` but not in `explored`. A lambda7 ≠ 0 boundary run (a config with `lambda7` ≠ 0, or lambda7 as a scan axis) is what would populate `explored`.
- **P3.** Choose a precision option from the table above, or keep float64. The saving is under 150 MB on Drive.
- **P4.** Retire superseded lambda7 = 0 data by authority label (`historical`), not by deletion. The blobs are the only copy of the 30 newer hep_cross files (forensics §1).
- **P5.** Add `site/src/content/docs/lake.md`. It is owned by the docs worker and does not yet mention `explored`, `regimes` or the safety rules.
