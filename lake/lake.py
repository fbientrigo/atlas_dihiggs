#!/usr/bin/env python3
"""lake: commit directories to a remote store (blob + Parquet tables + provenance), verify, prune, restore.

Remote layout (LAKE_REMOTE or --remote; "name:path" -> rclone, otherwise a plain local dir):
  blobs/<sha256>.tar.zst  tables/<name>/commit=<cid>/part-0.parquet  commits/<cid>.json  catalog.sql
"""
import glob as globmod, time, argparse, datetime as dt, gzip, hashlib, json, os, secrets, shutil, socket, subprocess, sys, tempfile
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


def producer_git(root, extra=()):
    """Git records found in the run manifest (any dict with 'commit'); [] means unknown. Not invented."""
    found = []
    def walk(o, p):
        if isinstance(o, dict):
            if isinstance(o.get("commit"), str):
                found.append({"path": p, "commit": o["commit"], "dirty": o.get("dirty", o.get("is_dirty"))})
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
               "tables": [], "producer_git": producer_git(root, a.producer_manifest), "committer_git": git_state(root)}
        mj = Path(tmp, "m.json.gz")  # per-file hashes live in their own object so the commits/ view stays small
        with gzip.open(mj, "wt") as f:
            json.dump(files, f)
        rec["source_manifest"] = {"path": f"manifests/{cid}.json.gz", "md5": _hash(mj, "md5")}
        rem.put(mj, rec["source_manifest"]["path"])
        for spec in a.table:
            name, glob = spec.split("=", 1)
            pq = Path(tmp, f"{name}.parquet")
            rows = to_parquet(root, glob, pq, getattr(a, "only", None))
            if rows is None:
                continue
            rel = f"tables/{name}/commit={cid}/part-0.parquet"
            rem.put(pq, rel)
            rec["tables"].append({"name": name, "glob": glob, "rows": rows, "path": rel, "md5": _hash(pq, "md5")})
        cj = Path(tmp, "c.json"); cj.write_text(json.dumps(rec, indent=1))
        rem.put(cj, f"commits/{cid}.json")  # written last: a commit record implies everything else was uploaded
    verify(rem, cid, rec)
    print(f"committed {cid}: {len(files)} files, {len(rec['tables'])} tables, blob {rec['blob']['size']} B")
    return cid


def write_catalog(rem, tmp):
    sql = ["CREATE OR REPLACE VIEW commits AS SELECT * FROM read_json_auto('commits/*.json');"]
    for t in rem.ls("tables", dirs=True):
        sql.append(f"CREATE OR REPLACE VIEW {t} AS SELECT * FROM read_parquet('tables/{t}/*/*.parquet', "
                   "hive_partitioning=true, union_by_name=true);")
    p = Path(tmp, "catalog.sql"); p.write_text("\n".join(sql) + "\n")
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


def cmd_prune(a):
    rem = _remote(a)
    rec = verify(rem, a.cid)  # always re-checked remotely, never cached
    g = rec["committer_git"]
    if g["head"] and g["head_on_remote"] is False and not a.allow_unpushed and not on_remote(g["repo"], g["head"]):
        sys.exit(f"refusing: code HEAD {g['head'][:7]} is not on its remote (push it, or --allow-unpushed)")
    cutoff = time.time() - a.older_than * 86400
    root, delete, keep = Path(rec["source_path"]), [], []
    for f in load_files(rem, rec):
        p = root / f["path"]
        ok = p.is_file() and p.stat().st_mtime < cutoff and p.stat().st_size == f["size"] and _hash(p, "sha256") == f["sha256"]
        (delete if ok else keep).append(p)
    print(f"{len(delete)} files safe to delete, {len(keep)} kept (missing or changed since commit)")
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
    for d, _, _ in os.walk(root, topdown=False):
        try: os.rmdir(d)  # only succeeds if empty
        except OSError: pass


def cmd_restore(a):
    rem = _remote(a); rec = verify(rem, a.cid)
    dest = Path(a.dest); dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        blob = Path(tmp, "b.tar.zst")
        rem.get(f"blobs/{rec['blob']['sha256']}.tar.zst", blob)
        if _hash(blob, "sha256") != rec["blob"]["sha256"]:
            sys.exit("blob sha256 mismatch")
        subprocess.run(["tar", "--zstd", "-xf", str(blob), "-C", str(dest)], check=True)
    files = load_files(rem, rec)
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


def cmd_query(a):
    """SQL over the catalog views (commits + one view per table) without downloading any blob."""
    os.chdir(refresh(_remote(a), a.offline))
    con = duckdb.connect()
    con.execute(Path("catalog.sql").read_text())
    con.sql(a.sql).show(max_rows=a.rows, max_width=200)


def sources():
    """sources.tsv rows -> (dir, authority, prune?, {table: glob}); globs expand; first matching row owns a file."""
    for ln in Path(__file__).with_name("sources.tsv").read_text().splitlines():
        if ln.strip() and not ln.startswith("#"):
            pat, auth, prune, *t = ln.split("\t") + [""]
            for d in sorted(globmod.glob(str(WORKSPACE / pat))):
                if Path(d).is_dir():
                    yield Path(d), auth, prune == "yes", [x for x in (t[0].split() if t else []) if x]


def cmd_sync(a):
    """Commit whatever local files no commit covers yet; then (with --yes) prune committed files older than --older-than."""
    rem = _remote(a); recs = records(rem)
    plan, claimed = [], {}
    for d, auth, prune, tables in sources():
        mine = {}
        for f in scan(d, set()):
            k = str(d / f["path"])
            if k not in claimed:
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
        rows = [(d, p) for d, _, p, _ in sources() if d == root or d in root.parents]
        if not rows or not all(p for _, p in rows) or not any((root / f["path"]).is_file() for f in load_files(rem, rec)):
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
    s.add_parser("catalog", help="regenerate catalog.sql (not done per commit)").set_defaults(f=cmd_catalog)
    a = p.parse_args(); a.f(a)


if __name__ == "__main__":
    main()
