# Data Lake (Optional)

The DiHiggs Data Lake is an optional cloud storage and metadata query client backed by Google Drive (`dihiggs_lake:store`). It manages large simulation datasets, analysis tables, and commit provenance archives.

Consult the local documentation at [`lake/README.md`](https://github.com/fbientrigo/atlas_dihiggs/blob/main/lake/README.md) for full script specifications.

---

## Storage Architecture

The remote Drive storage organizes data into three distinct immutable object tiers:

- **Immutable Blobs (`blobs/<sha256>.tar.zst`)**: Full lossless archives of complete campaign commits. Downloaded only during full dataset restoration.
- **Queryable Tables (`tables/<name>/commit=<cid>/*.parquet`)**: Columnar Parquet datasets for tabular scan data (totaling ~180 MB). These can be queried directly via DuckDB without downloading heavy blob archives.
- **Provenance Manifests (`commits/<cid>.json`)**: Complete provenance metadata records capturing Git HEAD commit, working tree dirty status, scientific authority labels, and generation timestamps.

---

## Setup & Configuration

The data lake is optional and not required for standard code builds, unit tests, or workspace validation.

1. **Install DuckDB**:
    ```bash
    pip install duckdb
    ```

2. **Configure `rclone`**:
    Configure a remote named `dihiggs_lake` with type `drive` and scope `drive`:
    ```bash
    rclone config
    ```
    *(Browser authentication is used for Google OAuth; credentials are not stored in the repository).*

    To use an alternative remote target, set the `LAKE_REMOTE` environment variable:
    ```bash
    export LAKE_REMOTE="my_remote:path"
    ```

---

## Daily Usage

The query and synchronization tool is executed via `lake/lake.py`:

### Querying Metadata with SQL
Run interactive SQL queries on table metadata mirrored locally to `~/.cache/lake`:

```bash
# Query boundary points with non-zero trilinear input
python3 lake/lake.py query "SELECT count(*) FROM boundary_points WHERE lambda7_input != 0"

# Inspect commit provenance and authority labels
python3 lake/lake.py query "SELECT cid, authority, message FROM commits"

# Join point data with commit provenance
python3 lake/lake.py query "SELECT p.*, c.authority FROM boundary_points p JOIN commits c ON p.commit = c.cid"
```

Use `--offline` to skip remote cache refresh during offline work.

### Inspecting Commits
List recorded campaign commits, authority tags, and status:

```bash
python3 lake/lake.py ls
```

### Synchronizing Local Data
Synchronize local files matching patterns declared in `lake/sources.tsv`:

```bash
# Dry run: check which files would be uploaded or cleaned
python3 lake/lake.py sync

# Execute upload and remove verified local files older than 2 days
python3 lake/lake.py sync --yes --older-than 2
```

### Restoring Campaign Datasets
Download and verify a complete campaign commit by its commit ID:

```bash
python3 lake/lake.py restore <cid> <destination-dir>
python3 lake/lake.py verify <cid>
```
