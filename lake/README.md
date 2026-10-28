# lake: DiHiggs data store on Google Drive (`dihiggs_lake:store`)

Drive holds immutable, add-only objects:
- `blobs/<sha256>.tar.zst` is a lossless copy of every file in a commit;
- `tables/<name>/commit=<cid>/*.parquet` is the queryable index;
- `manifests/<cid>.json.gz` holds per-file sha256;
- `commits/<cid>.json` holds provenance: authority, committer git, producer git and mass convention.

Queries use only commits and tables, about 180 MB, and never download blobs. The end-to-end pipeline, the safety rules, the gaps and the open proposals are in [ARCHITECTURE.md](ARCHITECTURE.md).

## Setup
1. Workspace: see the root [README.md](../README.md). `pip install duckdb`; the workspace `.venv` has it.
2. Configure `rclone` with a remote named `dihiggs_lake`: type `drive`, scope `drive`. OAuth runs in the browser, and the tokens are not stored in the repo. Set `LAKE_REMOTE=name:path` to use another remote. A plain directory path works as a remote too, which is how `test_lake.py` runs.

## Use (`python lake/lake.py ...`; add `--offline` to skip the mirror refresh)
- `explored [--lambda7 V|nonzero] [--mh GeV] [--tan-beta T] [--mphi GeV --mbar GeV]`
  - With no point given, it prints coverage per regime and status (`valid` / `excluded` / `unknown`).
  - With a point given, it prints the leaves that contain it. If none do, it prints `not explored` and exits 1.
  - With `--export FILE.csv`, it writes the matching rows. A boundary survivor v2 run takes that file as `--explored` and skips leaves already explored for its exact regime (see ARCHITECTURE.md, P1).
- `query "SQL"` runs SQL over these views:
  - `commits`;
  - one view per table;
  - `regimes`: per commit, the producer commit and the convention;
  - `explored`: per campaign × leaf, with `n_points`, `n_valid`, `status`, `best_point_id` and the regime.

  Examples:
  - `query "select status, count(*) from explored where lambda7 != 0 group by 1"`
  - `query "select b.point_id, r.producer_commit, r.convention_id from boundary_points b join regimes r on b.commit = r.cid limit 5"` (rows also carry their own `producer_commit`, which is "unknown" in all current data)
- `ls` lists commits: authority, code HEAD, clean or dirty, and source dir.
- `sync` commits every local file that no commit covers yet and git does not track (git owns tracked files), following the rules in `sources.tsv`, then dry-runs the cleanup. `sync --yes [--older-than 2]` deletes local files, but only if all of these hold:
  - the remote md5 is re-verified;
  - the local sha256 still matches;
  - the file is **not git-tracked**;
  - its name matches no `-GLOB` of its `sources.tsv` row (`yes -*_state.json -*.yaml` keeps run state and configs).

  It refuses to run if the code HEAD is not on its git remote.
- `prune <cid> [--yes]` runs the same per-commit delete step, with the same guards.
- `restore <cid> <dir>` downloads a commit and checks its sha256. It refuses to overwrite local files that differ.
- `verify <cid>` checks one commit. `catalog` regenerates `catalog.sql` on the remote, for readers without lake.py.

## Adding data
- A new campaign dir that matches a pattern in `sources.tsv` is picked up by `sync`. Otherwise, add one line.
- To make files queryable, add `NAME=GLOB` in column 4. `NAME=GLOB@compact` keeps only the inputs, ids and rejection reason of theory-invalid rows (`lake.COMPACT_KEEP`), exact; valid rows are unchanged, and the blob keeps the full rows. A table with the point columns (`lake.POINT_COLUMNS`: dihiggs.point.v2 plus boundary `mesh_*` bounds) feeds `explored` automatically.

Run the tests with `python lake/test_lake.py`. They need no Drive access.
