---
title: "Data Lake"
description: "Lossless storage of campaign output, a queryable index, and the explored-coverage loop that keeps runs from repeating work."
---

The lake (`lake/lake.py`) keeps every campaign file on a remote store (`dihiggs_lake:store` on Google Drive, or any local directory) and a small Parquet index of the point tables. It is optional: builds and tests do not need it. Design and measured numbers: [`lake/ARCHITECTURE.md`](https://github.com/fbientrigo/atlas_dihiggs/blob/main/lake/ARCHITECTURE.md).

## What the remote holds

Objects are only ever added, never rewritten or deleted.

| Path | Content |
|---|---|
| `blobs/<sha256>.tar.zst` | every file of a commit, byte for byte. Physics claims come from here. |
| `manifests/<cid>.json.gz` | sha256 and size of each file |
| `tables/<name>/commit=<cid>/*.parquet` | the queryable index of point and leaf files |
| `commits/<cid>.json` | authority, committer git, producer git, mass convention |

Queries read only `commits/` and `tables/` (a local mirror in `~/.cache/lake`), never blobs.

## Setup

```bash
pip install duckdb            # the workspace .venv already has it
rclone config                 # remote "dihiggs_lake", type drive, scope drive
export LAKE_REMOTE=name:path  # optional: another rclone remote, or a plain directory
```

## Commands

```bash
python lake/lake.py ls                       # commits: authority, code HEAD, source dir
python lake/lake.py query "SQL"              # views: commits, regimes, explored, one per table
python lake/lake.py explored                 # coverage per regime and status
python lake/lake.py explored --lambda7 nonzero --mh 125.2 --tan-beta 1e5 --mphi 150 --mbar 160
python lake/lake.py explored --lambda7 0 --mh 125.2 --export explored.csv
python lake/lake.py sync                     # commit new files per sources.tsv, then a dry-run cleanup
python lake/lake.py restore <cid> <dir>      # download and sha256-check one commit
python lake/lake.py verify <cid>
```

Add `--offline` to skip the mirror refresh.

## Regimes and the explored view

A **regime** is `lambda7`, `mh` (per row) plus the producer commit and `convention_id` (per commit; commits before 2026-10-27 have no convention, so `mh` is the proxy there).

`explored` has one row per regime × campaign × commit × leaf, built from every table with the point columns. Its `status` is:

- `valid`: at least one `theory_ok_v1 = 1` point;
- `excluded`: 0 valid out of at least 64 points (95% upper bound on the valid fraction below 4.6%);
- `unknown`: anything else. `upper95_valid_fraction` is always given.

Coverage of one regime never answers for another: a `lambda7 = 0` leaf is "not explored" for `lambda7 != 0`.

## The next run reads the lake

The boundary survivor campaign (v2) takes the export as input, so it needs neither lake.py nor rclone:

```bash
python lake/lake.py explored --lambda7 0 --mh 125.2 --export explored.csv
cd dihiggs_boundary && PYTHONPATH=python python -m dhb.survivor_adaptive_campaign \
    --config <campaign.yaml> --output-dir <dir> --explored ../explored.csv
```

Each leaf the run creates starts from the recorded `n_points` and `n_valid` of the same leaf (id and rectangle) in the same regime. Explored leaves cost no new evaluations, excluded leaves are not re-sampled, and partial leaves continue with the next replicate seed. The manifest records the export's sha256 under `explored_seed`. Without `--explored` the run resumes from its local `campaign_state.json` as before.

## Safety rules

- `sync --yes` and `prune --yes` delete a local file only when the remote md5 re-verifies, size, sha256 and the mtime cutoff all match, and the file is not git-tracked. If git cannot answer, nothing is deleted.
- Prune removes only directories it emptied, never the root.
- A `keep` row anywhere under a commit's root blocks pruning that commit.
- A `yes -GLOB` row keeps files whose name matches `GLOB`. The boundary rows keep `*_state.json` and `*.yaml`, so a later run can always resume.
- A commit record is written only after its objects verify.
- `restore` refuses to overwrite a local file whose content differs.

## Compact tables

`NAME=GLOB@compact` in `sources.tsv` keeps, for theory-invalid rows (`theory_ok_v1 != 1`) of that table, only the columns that say which point was already run, unchanged: tan β, masses, λ6/X, Δ, λ7, mh, seeds, ids, mesh bounds, plus the rejection reason (`rejection_stage`, `rejection_reason`). Their outputs (widths, BRs, couplings) are not in the table; `lake restore` gets the full rows from the blob, which is lossless. Valid rows are unchanged. `explored` and `--export` give the same answer as on a full table. This applies to new commits only. On the measured `boundary_points` (1.23M rows, 3.4% valid) the table goes from 163 MB to 23 MB.

## Adding data

Add one line to `lake/sources.tsv`: directory glob, authority, prune rule, and `NAME=GLOB` for files that should become tables. Tests: `python lake/test_lake.py` (local-directory remote, no Drive).
