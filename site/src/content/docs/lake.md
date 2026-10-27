---
title: "Data Lake (Optional)"
description: "Columnar Parquet storage, DuckDB SQL queries, and commit provenance archives."
---

<div class="wired-card">
  <div class="wired-card-header">
    <span>// DATA_LAKE_ARCHIVE: PARQUET TABLES & PROVENANCE TIERS</span>
    <span class="wired-pill">OPTIONAL STORAGE</span>
  </div>
  <p style="margin-bottom: 0;">
    The DiHiggs Data Lake is an optional cloud storage and metadata query client backed by Google Drive (<code>dihiggs_lake:store</code>). It manages large simulation datasets, analysis tables, and commit provenance archives. Consult the repository documentation at <a href="https://github.com/fbientrigo/atlas_dihiggs/blob/main/lake/README.md"><code>lake/README.md</code></a> for full specifications.
  </p>
</div>

## Storage Architecture

The remote Drive storage organizes data into three immutable object tiers:

<div class="wired-grid">
  <div class="wired-card" style="margin-bottom: 0;">
    <div class="wired-card-header">
      <span>IMMUTABLE BLOBS</span>
      <span class="wired-pill">TIER 1</span>
    </div>
    <p style="font-size: 0.85rem; margin-bottom: 0;">
      <code>blobs/&lt;sha256&gt;.tar.zst</code><br/>
      Full lossless archives of complete campaign commits. Downloaded only during full dataset restoration.
    </p>
  </div>

  <div class="wired-card" style="margin-bottom: 0;">
    <div class="wired-card-header">
      <span>QUERYABLE TABLES</span>
      <span class="wired-pill">TIER 2</span>
    </div>
    <p style="font-size: 0.85rem; margin-bottom: 0;">
      <code>tables/&lt;name&gt;/commit=&lt;cid&gt;/*.parquet</code><br/>
      Columnar Parquet datasets for tabular scan data (~180 MB). Queryable directly via DuckDB without downloading heavy blob archives.
    </p>
  </div>

  <div class="wired-card" style="margin-bottom: 0;">
    <div class="wired-card-header">
      <span>PROVENANCE MANIFESTS</span>
      <span class="wired-pill">TIER 3</span>
    </div>
    <p style="font-size: 0.85rem; margin-bottom: 0;">
      <code>commits/&lt;cid&gt;.json</code><br/>
      Provenance metadata capturing Git HEAD commit, working tree dirty status, authority labels, and timestamps.
    </p>
  </div>
</div>

---

## Setup & Configuration

The data lake is optional and not required for standard code builds, unit tests, or workspace validation.

### 1. Install DuckDB
```bash
pip install duckdb
```

### 2. Configure `rclone`
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
