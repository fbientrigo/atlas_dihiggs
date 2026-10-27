# lake — DiHiggs data store on Google Drive (`dihiggs_lake:store`)

Drive holds immutable objects: `blobs/<sha256>.tar.zst` (full lossless copy of each commit), `tables/<name>/commit=<cid>/*.parquet` (queryable),
`commits/<cid>.json` (provenance: code HEAD + dirty, authority label, date). Tables are only ~180 MB; blobs are never needed to query.

## New machine
1. Follow the global [onboarding guide](../docs/ONBOARDING.md); run
   `python3 -P scripts/bootstrap_workspace.py` from the workspace root.
2. Install DuckDB in the workspace environment only if using this optional
   query client. Configure `rclone` separately for a remote named
   `dihiggs_lake`, type `drive`, scope `drive` (OAuth in the browser; tokens
   are not in the repo).
   Override the target with `LAKE_REMOTE=name:path` if needed.

## Daily use (`.venv/bin/python lake/lake.py ...`)
- `query "SQL"` — SQL on Drive metadata without downloading blobs (mirrors commits+tables to `~/.cache/lake`, incremental; `--offline` skips refresh).
  `query "select count(*) from boundary_points where lambda7_input != 0"` · `query "select cid, authority, message from commits"`
  Per-row provenance: `... from boundary_points join commits on boundary_points.commit = commits.cid`.
- `ls` — commits (authority, code HEAD, clean/dirty, source dir).
- `sync` — commit every local file not yet uploaded (rules in `sources.tsv`), dry-run of the cleanup; `sync --yes [--older-than 2]` deletes local
  files only after re-verifying the remote md5 and re-hashing the local file. Refuses if the code HEAD is not on its git remote.
- `restore <cid> <dir>` — download + sha256-check a full commit. `verify <cid>`.
- New campaign dir under an existing pattern in `sources.tsv` → picked up by `sync`; otherwise add one line.
- Adding a queryable table: `NAME=GLOB` in the 4th column of `sources.tsv`.
