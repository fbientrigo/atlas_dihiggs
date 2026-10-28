#!/usr/bin/env python3
"""lake: commit directories to a remote store (blob + Parquet tables + provenance), verify, prune, restore.

Remote layout (LAKE_REMOTE or --remote; "name:path" -> rclone, otherwise a plain local dir):
  blobs/<sha256>.tar.zst  tables/<name>/commit=<cid>/part-0.parquet  commits/<cid>.json  catalog.sql
Remote objects are immutable: lake only ever adds them. Local deletes (prune) need a verified remote copy and never touch git-tracked files.
"""
import fnmatch, glob as globmod, time, argparse, datetime as dt, gzip, hashlib, json, os, secrets, shutil, socket, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import duckdb

EXCLUDE = {".git", "__pycache__", "graphify-out"}
AUTHORITY = ("current", "candidate", "historical", "forbidden_as_current")
MANIFESTS = ("manifest.json", "run_manifest.json")
DEFAULT_REMOTE = "dihiggs_lake:store"  # rclone remote; recreate it on a new machine (see README.md)
WORKSPACE = Path(__file__).resolve().parent.parent
CACHE = Path(os.environ.get("LAKE_CACHE", Path.home() / ".cache" / "lake"))


# ---- remote: rclone ("name:path") or local dir -------------------------------------------
class Remote:
    def __init__(self, spec):
        self.spec = spec.rstrip("/")
        self.rclone = ":" in spec and not spec.startswith(("/", "."))

    def _r(self, *a):
        return subprocess.run(["rclone", *a], check=True, capture_output=True, text=True).stdout

    def put(self, local, rel):
        if self.rclone:
            self._r("copyto", str(local), f"{self.spec}/{rel}")
        else:
            dst = Path(self.spec, rel); dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(local, dst)

    def get(self, rel, local):
        if self.rclone:
            self._r("copyto", f"{self.spec}/{rel}", str(local))
        else:
            shutil.copyfile(Path(self.spec, rel), local)

    def md5(self, rel):
        """Remote md5 of one object, or None if missing."""
        for attempt in range(3):  # transient rclone/Drive errors (rate limits) must not look like "missing"
            try:
                if self.rclone:
                    return self._r("md5sum", f"{self.spec}/{rel}").split()[0]
                return _hash(Path(self.spec, rel), "md5")
            except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
                time.sleep(5 * attempt)
        return None

    def ls(self, rel, dirs=False):
        if self.rclone:
            try:
                out = self._r("lsf", *(["--dirs-only"] if dirs else ["--files-only"]), f"{self.spec}/{rel}")
            except subprocess.CalledProcessError:
                return []
            return [x.rstrip("/") for x in out.split("\n") if x]
        p = Path(self.spec, rel)
        return sorted(x.name for x in p.iterdir() if x.is_dir() == dirs) if p.is_dir() else []


def _hash(path, algo):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _remote(args):
    return Remote(args.remote or os.environ.get("LAKE_REMOTE") or DEFAULT_REMOTE)


# ---- provenance --------------------------------------------------------------------------
def git_state(path):
    def g(*a):
        r = subprocess.run(["git", "-C", str(path), *a], capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else None
    head = g("rev-parse", "HEAD")
    if head is None:
        return {"repo": None, "head": None, "branch": None, "dirty": None, "head_on_remote": None}
    return {"repo": g("rev-parse", "--show-toplevel"), "head": head, "branch": g("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": bool(g("status", "--porcelain")),
            "head_on_remote": bool(g("branch", "-r", "--contains", head)) if g("remote") else None}  # None: repo has no remote


def on_remote(repo, head):
    """Live check (the commit record is a snapshot): is head now contained in a remote-tracking branch?"""
    r = subprocess.run(["git", "-C", str(repo), "branch", "-r", "--contains", head], capture_output=True, text=True)
    return r.returncode == 0 and bool(r.stdout.strip())


def manifest_records(root, extra=(), key="commit"):
    """Records found in the run manifest: key="commit" -> git records (any dict with 'commit'),
    key="convention_id" -> mass-convention blocks (dihiggs convention_provenance). [] means unknown. Not invented."""
    found = []
    def walk(o, p):
        if isinstance(o, dict):
            if key == "commit" and isinstance(o.get("commit"), str):
                found.append({"path": p, "commit": o["commit"], "dirty": o.get("dirty", o.get("is_dirty"))})
            elif key == "convention_id" and isinstance(o.get("convention_id"), str):
                found.append({"path": p, "convention_id": o["convention_id"], "source_sha256": o.get("source_sha256")})
            for k, v in o.items():
                walk(v, f"{p}.{k}" if p else k)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{p}[{i}]")
    for f in [Path(root, n) for n in MANIFESTS] + [Path(x) for x in extra]:
        if f.is_file():
            try:
                walk(json.loads(f.read_text()), f.name)
            except Exception:
                pass
    return found


# ---- commit ------------------------------------------------------------------------------
def scan(root, excludes, only=None):
    rels = list(only or [])
    for d, dirs, files in os.walk(root) if only is None else ():
        dirs[:] = [x for x in dirs if x not in EXCLUDE and not x.startswith(".venv") and x not in excludes]
        rels += [os.path.relpath(os.path.join(d, f), root) for f in files if f not in excludes and os.path.isfile(os.path.join(d, f))]
    def one(rel):
        p = Path(root, rel)
        return {"path": rel, "size": p.stat().st_size, "sha256": _hash(p, "sha256")}
    with ThreadPoolExecutor(4) as ex:
        return sorted(ex.map(one, rels), key=lambda x: x["path"])


def to_parquet(root, glob, out, only=None):
    """Table from files matching glob under root; with `only` (delta commit) just those among them. None if no match."""
    if only is None:
        g = "'" + str(Path(root, glob)).replace("'", "''") + "'"
    else:
        hit = sorted(set(globmod.glob(str(Path(root, glob)), recursive=True)) & {str(Path(root, o)) for o in only})
        if not hit:
            return None
        g = "[" + ",".join("'" + h.replace("'", "''") + "'" for h in hit) + "]"
    ext = glob.rsplit(".", 1)[-1]
    con = duckdb.connect()
    con.execute(f"SET memory_limit='1500MB'; SET threads=2; SET temp_directory='{tempfile.gettempdir()}'")
    if ext in ("csv", "tsv", "gz"):  # type inference on a sample first, then full scan, then all strings
        srcs = [f"read_csv({g}, union_by_name=true, filename=true, sample_size={n}{x})"
                for n, x in ((20480, ""), (-1, ""), (-1, ", all_varchar=true"))]
    elif ext in ("json", "jsonl", "ndjson"):
        srcs = [f"read_json({g}, union_by_name=true, filename=true)",  # fallback: one raw JSON column per line
                f"read_ndjson_objects({g}, filename=true)"]
    elif ext == "parquet":
        srcs = [f"read_parquet({g}, union_by_name=true, filename=true)"]
    else:
        sys.exit(f"unsupported table glob extension: {glob}")
    for src in srcs:
        try:
            con.execute(f"COPY (SELECT * REPLACE (replace(filename, ?, '') AS filename) FROM {src}) "
                        f"TO '{out}' (FORMAT parquet, COMPRESSION zstd)", [str(root).rstrip("/") + "/"])
            break
        except duckdb.Error as e:
            print(f"table {glob}: retrying with looser typing ({str(e)[:120]})", file=sys.stderr)
    else:
        sys.exit(f"could not convert {glob}")
    return con.execute(f"SELECT count(*) FROM read_parquet('{out}')").fetchone()[0]


# Columns a compact table keeps for theory-invalid rows: the exact inputs and ids that say "this point was already run"
# (tan_beta, masses, lambda6/X, Delta, lambda7, mh, seeds, point/leaf ids, mesh bounds) and why it was rejected.
# Allowlist on purpose: every other column (outputs, diagnostics) of an invalid row lives only in the lossless blob.
COMPACT_KEEP = ("campaign_id", "run_id", "point_id", "yukawa_type", "*_input*", "m_phi_GeV", "M_plot_GeV", "X_lambda6_times_tan_beta",
                "lambda6_from_X", "Delta_heavy_GeV", "profile_index", "profile_replicate", "profile_seed", "outer_cell_id",
                "outer_*_index", "mesh_*", "*_min_GeV", "*_max_GeV", "theory_ok_v1", "rejection_stage", "rejection_reason")


def compact(src, valid, invalid):
    """Split a point table: valid rows (theory_ok_v1 = 1) unchanged; invalid rows keep only the COMPACT_KEEP columns, unchanged.
    The valid part is written even when empty so its schema (the output columns) stays in the table. Returns [(path, rows)]."""
    con, src = duckdb.connect(), "read_parquet('" + str(src).replace("'", "''") + "')"
    keep = ", ".join(f'"{c}"' for c, *_ in con.execute(f"DESCRIBE SELECT * FROM {src}").fetchall()
                     if any(fnmatch.fnmatchcase(c, g) for g in COMPACT_KEEP))
    bad, parts = "coalesce(TRY_CAST(theory_ok_v1 AS DOUBLE), 0) != 1", []
    for dst, q in ((valid, f"SELECT * FROM {src} WHERE NOT ({bad})"), (invalid, f"SELECT {keep} FROM {src} WHERE {bad}")):
        con.execute(f"COPY ({q}) TO '{dst}' (FORMAT parquet, COMPRESSION zstd)")
        n = con.execute(f"SELECT count(*) FROM read_parquet('{dst}')").fetchone()[0]
        if n or dst == valid:
            parts.append((dst, n))
    return parts


def cmd_commit(a):
    rem, root = _remote(a), Path(a.dir).resolve()
    cid = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + secrets.token_hex(3)
    files = scan(root, set(a.exclude), getattr(a, "only", None))
    with tempfile.TemporaryDirectory() as tmp:
        blob = Path(tmp, "blob.tar.zst")
        lst = Path(tmp, "files")
        lst.write_bytes(b"\0".join(f["path"].encode() for f in files))
        subprocess.run(["tar", "--zstd", "-cf", str(blob), "-C", str(root), "--null", "-T", str(lst)], check=True)
        bsha = _hash(blob, "sha256")
        rem.put(blob, f"blobs/{bsha}.tar.zst")
        rec = {"cid": cid, "message": a.message, "authority": a.authority, "source_path": str(root),
               "host": socket.gethostname(), "created_utc": cid.split("-")[0],
               "blob": {"sha256": bsha, "md5": _hash(blob, "md5"), "size": blob.stat().st_size, "n_files": len(files)},
               "tables": [], "producer_git": manifest_records(root, a.producer_manifest), "committer_git": git_state(root),
               "conventions": manifest_records(root, a.producer_manifest, "convention_id")}
        mj = Path(tmp, "m.json.gz")  # per-file hashes live in their own object so the commits/ view stays small
        with gzip.open(mj, "wt") as f:
            json.dump(files, f)
        rec["source_manifest"] = {"path": f"manifests/{cid}.json.gz", "md5": _hash(mj, "md5")}
        rem.put(mj, rec["source_manifest"]["path"])
        for spec in a.table:
            name, glob = spec.split("=", 1); glob, _, mode = glob.partition("@")  # NAME=GLOB@compact: see compact()
            pq = Path(tmp, f"{name}.parquet")
            rows = to_parquet(root, glob, pq, getattr(a, "only", None))
            if rows is None:
                continue
            parts = compact(pq, Path(tmp, f"{name}.valid.parquet"), Path(tmp, f"{name}.invalid.parquet")) if mode == "compact" else [(pq, rows)]
            for i, (part, n) in enumerate(parts):
                rel = f"tables/{name}/commit={cid}/part-{i}.parquet"
                rem.put(part, rel)
                rec["tables"].append({"name": name, "glob": glob, "rows": n, "path": rel, "md5": _hash(part, "md5"),
                                      **({"compact": "invalid_inputs_only"} if part.name.endswith(".invalid.parquet") else {})})
        verify(rem, cid, rec)  # before the record: a commit record must never point at a missing/partial object
        cj = Path(tmp, "c.json"); cj.write_text(json.dumps(rec, indent=1))
        rem.put(cj, f"commits/{cid}.json")
    print(f"committed {cid}: {len(files)} files, {len(rec['tables'])} tables, blob {rec['blob']['size']} B")
    return cid


def catalog_sql(tables):
    sql = ["CREATE OR REPLACE VIEW commits AS SELECT * FROM read_json_auto('commits/*.json', union_by_name=true);"]
    for t in tables:
        sql.append(f"CREATE OR REPLACE VIEW {t} AS SELECT * FROM read_parquet('tables/{t}/*/*.parquet', "
                   "hive_partitioning=true, union_by_name=true);")
    return "\n".join(sql) + "\n"


def write_catalog(rem, tmp):
    """catalog.sql on the remote, for readers without lake.py (query/explored build their views from the mirror)."""
    p = Path(tmp, "catalog.sql"); p.write_text(catalog_sql(rem.ls("tables", dirs=True)))
    rem.put(p, "catalog.sql")


# ---- verify / prune / restore / ls -------------------------------------------------------
def load(rem, cid):
    with tempfile.TemporaryDirectory() as tmp:
        rem.get(f"commits/{cid}.json", Path(tmp, "c.json"))
        return json.loads(Path(tmp, "c.json").read_text())


def load_files(rem, rec):
    p = CACHE / "manifests" / f"{rec['cid']}.json.gz"  # manifests are immutable: cache per cid
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        rem.get(rec["source_manifest"]["path"], str(p) + ".tmp"); os.replace(str(p) + ".tmp", p)
    with gzip.open(p, "rt") as f:
        return json.load(f)


def verify(rem, cid, rec=None):
    rec = rec or load(rem, cid)
    objs = [(f"blobs/{rec['blob']['sha256']}.tar.zst", rec["blob"]["md5"])] + [(t["path"], t["md5"]) for t in rec["tables"]] + [(rec["source_manifest"]["path"], rec["source_manifest"]["md5"])]
    with ThreadPoolExecutor(len(objs)) as ex:  # Drive calls take 7-25 s each: one per object, in parallel
        got = dict(zip([p for p, _ in objs], ex.map(rem.md5, [p for p, _ in objs])))
    bad = [(p, m, got[p]) for p, m in objs if got[p] != m]
    if bad:
        sys.exit(f"VERIFY FAILED for {cid}: {bad}")
    return rec


def cmd_verify(a):
    verify(_remote(a), a.cid); print("ok")


def tracked(root):
    """Absolute paths of git-tracked files under root (incl. submodules); empty if root is in no repo."""
    r = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--recurse-submodules"], capture_output=True)
    if r.returncode != 0:
        if b"not a git repository" in r.stderr:
            return set()
        sys.exit(f"refusing: cannot list git-tracked files under {root}: {r.stderr.decode()[:200]}")
    return {str(Path(root, x)) for x in r.stdout.decode().split("\0") if x}


def cmd_prune(a):
    rem = _remote(a)
    rec = verify(rem, a.cid)  # always re-checked remotely, never cached
    g = rec["committer_git"]
    if g["head"] and g["head_on_remote"] is False and not a.allow_unpushed and not on_remote(g["repo"], g["head"]):
        sys.exit(f"refusing: code HEAD {g['head'][:7]} is not on its remote (push it, or --allow-unpushed)")
    cutoff = time.time() - a.older_than * 86400
    root, delete, keep = Path(rec["source_path"]), [], []
    git = tracked(root) if root.is_dir() else set()
    never = [g for *_, globs in rules(root) for g in globs]  # sources.tsv "yes -GLOB": e.g. run state a later run resumes from
    for f in load_files(rem, rec):
        p = root / f["path"]
        ok = not any(fnmatch.fnmatchcase(p.name, g) for g in never) and str(p) not in git and p.is_file() and p.stat().st_mtime < cutoff and p.stat().st_size == f["size"] and _hash(p, "sha256") == f["sha256"]
        (delete if ok else keep).append(p)
    print(f"{len(delete)} files safe to delete, {len(keep)} kept (sources.tsv keep glob, git-tracked, missing, or changed since commit)")
    if not a.yes:
        print("dry run; pass --yes to delete"); return
    locked = []
    for p in delete:
        try:
            p.unlink()
        except PermissionError:  # read-only dirs are deliberate protection: leave the file, never chmod
            locked.append(p)
    if locked:
        print(f"{len(locked)} files left in place (permission denied), e.g. {locked[0]}")
    # only dirs we emptied, deepest first, never root itself (a full os.walk would also rmdir empty dirs inside .git)
    for d in sorted({q for p in delete for q in p.parents if root in q.parents}, key=lambda q: -len(q.parts)):
        try: d.rmdir()  # only succeeds if empty
        except OSError: pass


def cmd_restore(a):
    rem = _remote(a); rec = verify(rem, a.cid)
    dest = Path(a.dest); dest.mkdir(parents=True, exist_ok=True); files = load_files(rem, rec)
    clash = [f["path"] for f in files if (dest / f["path"]).exists() and _hash(dest / f["path"], "sha256") != f["sha256"]]
    if clash:
        sys.exit(f"refusing: {len(clash)} files in {dest} differ from the commit (would be overwritten), e.g. {clash[:3]}")
    with tempfile.TemporaryDirectory() as tmp:
        blob = Path(tmp, "b.tar.zst")
        rem.get(f"blobs/{rec['blob']['sha256']}.tar.zst", blob)
        if _hash(blob, "sha256") != rec["blob"]["sha256"]:
            sys.exit("blob sha256 mismatch")
        subprocess.run(["tar", "--zstd", "-xf", str(blob), "-C", str(dest), "--skip-old-files"], check=True)  # existing = identical
    bad = [f["path"] for f in files if _hash(dest / f["path"], "sha256") != f["sha256"]]
    if bad:
        sys.exit(f"restore mismatch: {bad[:5]}")
    print(f"restored {len(files)} files to {dest}")


def cmd_catalog(a):
    with tempfile.TemporaryDirectory() as tmp:
        write_catalog(_remote(a), tmp)


def refresh(rem, offline=False):
    """Local mirror of commits/, tables/ and catalog.sql (small: metadata only, never blobs). Returns its path."""
    if not rem.rclone:
        return Path(rem.spec)
    store = CACHE / "store"
    if not offline:
        subprocess.run(["rclone", "copy", rem.spec, str(store), "--include", "commits/**", "--include", "tables/**",
                        "--include", "catalog.sql"], check=True)
    return store


def records(rem, offline=False):
    return [json.loads(p.read_text()) for p in sorted((refresh(rem, offline) / "commits").glob("*.json"))]


def cmd_ls(a):
    for r in records(_remote(a), a.offline):
        g = r["committer_git"]
        print(r["cid"], r["authority"], f"{r['blob']['n_files']}f", (g["head"] or "nogit")[:7],
              "dirty" if g["dirty"] else "clean", r["source_path"].replace(str(WORKSPACE) + "/", ""), r["message"], sep="\t")


# ---- explored: coverage of the parameter space, derived from the point tables --------------
# A point table is any table with these columns (dihiggs.point.v2 rows + boundary mesh columns).
POINT_COLUMNS = {"point_id", "campaign_id", "lambda7_input", "mh_input_GeV", "tan_beta_input", "theory_ok_v1", "g_physical_hphiphi_GeV",
                 "mesh_leaf_id", "mphi_min_GeV", "mphi_max_GeV", "Mbar_min_GeV", "Mbar_max_GeV"}
EXCLUDED_MIN_POINTS = 64  # = boundary survivor campaign zero_success_max_attempts (its "tested_empty_95"): upper95 < 4.6%
EXPLORED = """CREATE OR REPLACE VIEW explored AS
SELECT e.*, r.* EXCLUDE (cid),
       CASE WHEN n_valid > 0 THEN 'valid' WHEN n_points >= {min_n} THEN 'excluded' ELSE 'unknown' END AS status,
       CASE WHEN n_valid = 0 THEN 1 - 0.05 ** (1.0 / n_points) END AS upper95_valid_fraction
FROM (SELECT lambda7_input AS lambda7, mh_input_GeV AS mh_GeV, tan_beta_input AS tan_beta,
             mphi_min_GeV, mphi_max_GeV, Mbar_min_GeV, Mbar_max_GeV, mesh_leaf_id AS leaf_id, campaign_id, commit,
             count(*) AS n_points, count(*) FILTER (WHERE theory_ok_v1 = 1) AS n_valid,
             arg_max(point_id, abs(g_physical_hphiphi_GeV)) FILTER (WHERE theory_ok_v1 = 1) AS best_point_id
      FROM ({points}) WHERE mesh_leaf_id IS NOT NULL GROUP BY ALL) e
LEFT JOIN regimes r ON r.cid = e.commit"""


def regime(r):
    """Per-commit regime label: producer (dihiggs evaluator) git + mass convention. Old records lack 'conventions' -> NULL."""
    pg = [g for g in r.get("producer_git", []) if g["path"].endswith("dihiggs_git")] or r.get("producer_git", []) or [{}]
    cv = r.get("conventions") or [{}]
    return (r["cid"], r["authority"], pg[0].get("commit"), pg[0].get("dirty"), cv[0].get("convention_id"), cv[0].get("source_sha256"))


def connect(a):
    """DuckDB on the metadata mirror: commits, one view per table, regimes (per commit) and explored (per leaf)."""
    rem = _remote(a); recs = records(rem, a.offline)
    os.chdir(refresh(rem, offline=True))
    tables = sorted(p.name for p in Path("tables").iterdir() if p.is_dir()) if Path("tables").is_dir() else []
    con = duckdb.connect()
    con.execute(catalog_sql(tables))
    con.execute("CREATE TABLE regimes (cid VARCHAR, authority VARCHAR, producer_commit VARCHAR, producer_dirty BOOLEAN, "
                "convention_id VARCHAR, convention_sha256 VARCHAR)")
    if recs:
        con.executemany("INSERT INTO regimes VALUES (?, ?, ?, ?, ?, ?)", [regime(r) for r in recs])
    pts = [t for t in tables if POINT_COLUMNS <= {c[0] for c in con.execute(f"DESCRIBE {t}").fetchall()}]
    if pts:
        cols = ", ".join(sorted(POINT_COLUMNS)) + ", commit"
        con.execute(EXPLORED.format(min_n=EXCLUDED_MIN_POINTS, points=" UNION ALL BY NAME ".join(f"SELECT {cols} FROM {t}" for t in pts)))
    return con


def cmd_query(a):
    """SQL over the views (commits, regimes, explored, one per table) without downloading any blob."""
    connect(a).sql(a.sql).show(max_rows=a.rows, max_width=200)


def cmd_explored(a):
    """Without --mphi/--mbar: coverage summary per regime. With them: the leaves containing that point (exit 1 if none)."""
    w, args = [], []
    if a.lambda7 == "nonzero":
        w.append("lambda7 != 0")
    elif a.lambda7 is not None:
        w.append("lambda7 = ?"); args.append(float(a.lambda7))
    for col, v in (("mh_GeV", a.mh), ("tan_beta", a.tan_beta)):
        if v is not None:
            w.append(f"abs({col} / ? - 1) < 1e-9"); args.append(v)
    for col, v in (("mphi", a.mphi), ("Mbar", a.mbar)):
        if v is not None:
            w.append(f"? BETWEEN {col}_min_GeV AND {col}_max_GeV"); args.append(v)
    con, where = connect(a), (" WHERE " + " AND ".join(w)) if w else ""
    if not con.execute("SELECT count(*) FROM duckdb_views() WHERE view_name = 'explored'").fetchone()[0]:
        sys.exit("no point tables in the lake (need columns: " + ", ".join(sorted(POINT_COLUMNS)) + ")")
    if a.export:  # the file a boundary run takes as --explored: it never needs lake.py, rclone or DuckDB
        rel = con.sql(f"SELECT * FROM explored{where} ORDER BY leaf_id, commit", params=args)
        rel.write_csv(a.export); print(f"exported {len(rel)} explored leaves to {a.export}"); return
    if a.mphi is None and a.mbar is None:
        sql = f"SELECT lambda7, mh_GeV, tan_beta, convention_id, status, count(*) AS leaves, sum(n_points) AS points FROM explored{where} GROUP BY ALL ORDER BY ALL"
    else:
        sql = (f"SELECT status, n_valid, n_points, upper95_valid_fraction, best_point_id, leaf_id, campaign_id, commit, producer_commit "
               f"FROM explored{where} ORDER BY status = 'valid' DESC, n_points DESC")
    rel = con.sql(sql, params=args)
    if not rel.fetchall():
        print("not explored"); sys.exit(1)
    rel.show(max_rows=a.rows, max_width=200)


def sources():
    """sources.tsv rows -> (dir, authority, prune?, [NAME=GLOB], [never-prune basename globs]); first matching row owns a file."""
    for ln in Path(__file__).with_name("sources.tsv").read_text().splitlines():
        if ln.strip() and not ln.startswith("#"):
            pat, auth, prune, *t = ln.split("\t") + [""]
            prune, *never = prune.split()
            for d in sorted(globmod.glob(str(WORKSPACE / pat))):
                if Path(d).is_dir():
                    yield Path(d), auth, prune == "yes", [x for x in (t[0].split() if t else []) if x], [g.lstrip("-") for g in never]


def rules(root):
    """sources.tsv rows at, above or below root (a nested row counts too: a "keep" block inside a prunable dir)."""
    return [(d, p, never) for d, _, p, _, never in sources() if d == root or d in root.parents or root in d.parents]


def cmd_sync(a):
    """Commit whatever local files no commit covers yet; then (with --yes) prune committed files older than --older-than."""
    rem = _remote(a); recs = records(rem)
    plan, claimed = [], {}
    for d, auth, prune, tables, _ in sources():
        mine, git = {}, tracked(d)  # git owns tracked files; the lake only takes what git does not hold
        for f in scan(d, set()):
            k = str(d / f["path"])
            if k not in claimed and k not in git:
                claimed[k] = f["sha256"]; mine[k] = f
        if mine:
            plan.append((d, auth, tables, mine))
    with ThreadPoolExecutor(8) as ex:  # mark covered files (same path and sha256) so only new/changed ones are committed
        for rec, files in zip(recs, ex.map(lambda r: load_files(rem, r), recs)):
            for f in files:
                k = os.path.join(rec["source_path"], f["path"])
                if claimed.get(k) == f["sha256"]:
                    del claimed[k]
    new = 0
    for d, auth, tables, mine in plan:
        only = [os.path.relpath(k, d) for k in mine if k in claimed]
        if only:
            cmd_commit(argparse.Namespace(remote=a.remote, dir=str(d), message=f"sync {dt.date.today()}", authority=auth, exclude=[],
                                          producer_manifest=[], table=tables, only=only)); new += 1
    if new:
        cmd_catalog(a)
    print(f"{new} new commits")
    for rec in records(rem):  # records() re-reads the mirror, which now includes the commits just made
        root = Path(rec["source_path"])
        rows = rules(root)
        if not rows or not all(p for _, p, _ in rows) or not any((root / f["path"]).is_file() for f in load_files(rem, rec)):
            continue
        try:
            cmd_prune(argparse.Namespace(remote=a.remote, cid=rec["cid"], yes=a.yes, allow_unpushed=False, older_than=a.older_than))
        except SystemExit as e:
            print(f"SKIPPED {rec['cid']}: {e}")


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument("--remote")
    s = p.add_subparsers(dest="cmd", required=True)
    c = s.add_parser("commit"); c.add_argument("dir"); c.add_argument("-m", "--message", required=True)
    c.add_argument("--authority", choices=AUTHORITY, required=True)
    c.add_argument("--table", action="append", default=[], metavar="NAME=GLOB")
    c.add_argument("--exclude", action="append", default=[], metavar="NAME")
    c.add_argument("--producer-manifest", action="append", default=[], metavar="PATH"); c.set_defaults(f=cmd_commit)
    for n, f in (("verify", cmd_verify), ("prune", cmd_prune), ("restore", cmd_restore)):
        x = s.add_parser(n); x.add_argument("cid")
        if n == "prune":
            x.add_argument("--yes", action="store_true"); x.add_argument("--older-than", type=float, default=0, metavar="DAYS"); x.add_argument("--allow-unpushed", action="store_true")
        if n == "restore":
            x.add_argument("dest")
        x.set_defaults(f=f)
    x = s.add_parser("ls", help="list commits (from the local metadata mirror)"); x.add_argument("--offline", action="store_true"); x.set_defaults(f=cmd_ls)
    x = s.add_parser("query", help="SQL on catalog views, e.g. 'select count(*) from boundary_points where lambda7_input != 0'")
    x.add_argument("sql"); x.add_argument("--offline", action="store_true"); x.add_argument("--rows", type=int, default=40); x.set_defaults(f=cmd_query)
    x = s.add_parser("sync", help="commit what is new per sources.tsv; with --yes delete local files already safe in the remote")
    x.add_argument("--yes", action="store_true"); x.add_argument("--older-than", type=float, default=2, metavar="DAYS"); x.set_defaults(f=cmd_sync)
    x = s.add_parser("explored", help="is this region/point already explored for a regime? (coverage from point tables)")
    x.add_argument("--lambda7", metavar="VALUE|nonzero"); x.add_argument("--mh", type=float, metavar="GeV")
    x.add_argument("--tan-beta", type=float); x.add_argument("--mphi", type=float, metavar="GeV"); x.add_argument("--mbar", type=float, metavar="GeV")
    x.add_argument("--offline", action="store_true"); x.add_argument("--rows", type=int, default=40)
    x.add_argument("--export", metavar="FILE.csv", help="write the matching explored rows (one per leaf x commit) for a boundary run's --explored")
    x.set_defaults(f=cmd_explored)
    s.add_parser("catalog", help="regenerate catalog.sql (not done per commit)").set_defaults(f=cmd_catalog)
    a = p.parse_args(); a.f(a)


if __name__ == "__main__":
    main()
