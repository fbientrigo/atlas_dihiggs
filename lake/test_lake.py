"""Roundtrip: commit -> verify -> prune -> restore, plus safety guards and the explored view, with a local-dir remote
(no Drive needed). Run: python test_lake.py"""
import argparse, csv, json, os, subprocess, sys, tempfile
from pathlib import Path

import duckdb
import lake


def main():
    with tempfile.TemporaryDirectory() as t:
        t = Path(t); src, remote, out = t / "src", t / "remote", t / "out"
        (src / "sub").mkdir(parents=True)
        (src / "a.csv").write_text("x,y\n1,2\n3,4\n")
        (src / "sub" / "b.csv").write_text("x,y\n5,6\n")
        (src / "keep.lhe").write_text("event data")
        (src / "manifest.json").write_text(json.dumps({"git": {"commit": "abc123", "dirty": True}}))
        r = lake.Remote(str(remote))
        cid = lake.cmd_commit(argparse.Namespace(dir=str(src), message="t", authority="candidate", exclude=[], producer_manifest=[],
                                                 table=["pts=**/*.csv"], remote=str(remote)))
        rec = lake.verify(r, cid)
        assert rec["producer_git"] == [{"path": "manifest.json.git", "commit": "abc123", "dirty": True}]
        assert rec["tables"][0]["rows"] == 3, rec["tables"]

        con = duckdb.connect()  # the catalog works from the lake root, and provenance joins by commit
        n = con.execute(f"SELECT count(*) FROM read_parquet('{remote}/tables/pts/*/*.parquet', hive_partitioning=true) "
                        f"WHERE commit='{cid}'").fetchone()[0]
        assert n == 3

        (src / "a.csv").write_text("x,y\n9,9\n")  # modified after commit -> prune must keep it
        lake.cmd_prune(argparse.Namespace(remote=str(remote), cid=cid, yes=True, allow_unpushed=True, older_than=0))
        assert (src / "a.csv").exists() and not (src / "sub" / "b.csv").exists() and not (src / "keep.lhe").exists()

        lake.cmd_restore(argparse.Namespace(remote=str(remote), cid=cid, dest=str(out)))
        assert (out / "a.csv").read_text() == "x,y\n1,2\n3,4\n"  # original content, not the modified one
        (remote / "tables" / "pts" / f"commit={cid}" / "part-0.parquet").write_bytes(b"corrupt")
        try:
            lake.verify(r, cid); raise AssertionError("corruption not detected")
        except SystemExit:
            pass
    git_guard()
    sync_skips_tracked()
    explored_and_old_records()
    compact_keep_and_export()
    print("ok")


def ns(remote, **kw):
    return argparse.Namespace(**{"remote": str(remote), "exclude": [], "producer_manifest": [], "table": [], "authority": "candidate", "message": "t", **kw})


def git_guard():
    """prune never deletes git-tracked files nor empty dirs it did not empty (e.g. inside .git); restore never overwrites."""
    with tempfile.TemporaryDirectory() as t:
        t = Path(t); src, remote = t / "repo", t / "remote"
        (src / "data").mkdir(parents=True); (src / "empty").mkdir()
        (src / "tracked.csv").write_text("x\n1\n"); (src / "data" / "untracked.csv").write_text("x\n2\n")
        g = ["git", "-C", str(src), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(g + ["init", "-q"], check=True); subprocess.run(g + ["add", "tracked.csv"], check=True)
        subprocess.run(g + ["commit", "-qm", "t"], check=True)
        cid = lake.cmd_commit(ns(remote, dir=str(src)))
        lake.cmd_prune(argparse.Namespace(remote=str(remote), cid=cid, yes=True, allow_unpushed=True, older_than=0))
        assert (src / "tracked.csv").exists(), "git-tracked file was pruned"
        assert not (src / "data").exists() and (src / "empty").is_dir(), "rmdir must be limited to dirs prune emptied"
        assert subprocess.run(g + ["status", "--porcelain"], capture_output=True, text=True, check=True).stdout == ""
        (src / "data").mkdir(); (src / "data" / "untracked.csv").write_text("newer local edit\n")
        try:
            lake.cmd_restore(argparse.Namespace(remote=str(remote), cid=cid, dest=str(src))); raise AssertionError("restore overwrote")
        except SystemExit:
            assert (src / "data" / "untracked.csv").read_text() == "newer local edit\n"
        real = lake.Remote.md5  # a commit whose upload does not verify must not leave a commit record behind
        lake.Remote.md5 = lambda self, rel: None
        try:
            lake.cmd_commit(ns(remote, dir=str(src / "data"))); raise AssertionError("unverified commit accepted")
        except SystemExit:
            assert len(list((remote / "commits").glob("*.json"))) == 1
        finally:
            lake.Remote.md5 = real


def sync_skips_tracked():
    """sync commits only what git does not hold: one owner per file."""
    with tempfile.TemporaryDirectory() as t:
        t = Path(t); src, remote = t / "repo", t / "remote"
        src.mkdir(); (src / "code.py").write_text("x = 1\n"); (src / "data.csv").write_text("x\n1\n")
        g = ["git", "-C", str(src), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(g + ["init", "-q"], check=True); subprocess.run(g + ["add", "code.py"], check=True)
        subprocess.run(g + ["commit", "-qm", "t"], check=True)
        real = lake.sources
        lake.sources = lambda: iter([(src, "candidate", False, [], [])])
        try:
            lake.cmd_sync(argparse.Namespace(remote=str(remote), yes=False, older_than=0))
        finally:
            lake.sources = real
        (rec,) = lake.records(lake.Remote(str(remote)))
        assert [f["path"] for f in lake.load_files(lake.Remote(str(remote)), rec)] == ["data.csv"]


def explored_and_old_records():
    """explored answers 'already explored for regime R?' and old-format commit records (no 'conventions') still read."""
    cols = sorted(lake.POINT_COLUMNS - {"campaign_id"})
    rows = [  # leaf A: 1 valid of 2; leaf B: 0 valid of 2 (unknown, < EXCLUDED_MIN_POINTS)
        dict(point_id="p1", theory_ok_v1=1, g_physical_hphiphi_GeV=-5, mesh_leaf_id="A", mphi_min_GeV=130, mphi_max_GeV=140),
        dict(point_id="p2", theory_ok_v1=0, g_physical_hphiphi_GeV=9, mesh_leaf_id="A", mphi_min_GeV=130, mphi_max_GeV=140),
        dict(point_id="p3", theory_ok_v1=0, g_physical_hphiphi_GeV=1, mesh_leaf_id="B", mphi_min_GeV=140, mphi_max_GeV=150),
        dict(point_id="p4", theory_ok_v1=0, g_physical_hphiphi_GeV=1, mesh_leaf_id="B", mphi_min_GeV=140, mphi_max_GeV=150)]
    with tempfile.TemporaryDirectory() as t:
        t = Path(t); src, remote = t / "run", t / "remote"; src.mkdir()
        with open(src / "points.csv", "w") as f:
            f.write("campaign_id," + ",".join(cols) + "\n")
            for r in rows:
                r = {"lambda7_input": 0.1, "mh_input_GeV": 125.2, "tan_beta_input": 1e5, "Mbar_min_GeV": 130, "Mbar_max_GeV": 140, **r}
                f.write("c," + ",".join(str(r[c]) for c in cols) + "\n")
        (src / "manifest.json").write_text(json.dumps({"canonical_engine": {"dihiggs_git": {"commit": "d1", "dirty": False}},
                                                       "mass_convention_authority": {"convention_id": "mh_125p20", "source_sha256": "s1"}}))
        cid = lake.cmd_commit(ns(remote, dir=str(src), table=["pts=points.csv"]))
        old = json.loads((remote / "commits" / f"{cid}.json").read_text())
        assert old["conventions"] == [{"path": "manifest.json.mass_convention_authority", "convention_id": "mh_125p20", "source_sha256": "s1"}]
        del old["conventions"]; old["cid"] = "20261001T000000Z-000000"  # pre-2026-10-27 record format
        (remote / "commits" / f"{old['cid']}.json").write_text(json.dumps(old)); lake.verify(lake.Remote(str(remote)), old["cid"])
        q = lambda **kw: lake.cmd_explored(argparse.Namespace(remote=str(remote), offline=True, rows=10, **{
            "lambda7": None, "mh": None, "tan_beta": None, "mphi": None, "mbar": None, "export": None, **kw}))
        q()  # summary
        q(lambda7="nonzero", mh=125.2, tan_beta=1e5, mphi=135, mbar=135)  # inside leaf A -> found
        for miss in (dict(lambda7="0", mphi=135, mbar=135), dict(mphi=200, mbar=135)):  # other regime / outside the mesh
            try:
                q(**miss); raise AssertionError(f"explored claimed {miss}")
            except SystemExit as e:
                assert e.code == 1
        con = lake.connect(argparse.Namespace(remote=str(remote), offline=True))
        got = con.execute("SELECT leaf_id, status, n_points, n_valid, best_point_id, producer_commit, convention_id FROM explored "
                          "WHERE commit = ? ORDER BY 1", [cid]).fetchall()
        assert got == [("A", "valid", 2, 1, "p1", "d1", "mh_125p20"), ("B", "unknown", 2, 0, None, "d1", "mh_125p20")], got
        assert con.execute("SELECT convention_id FROM regimes WHERE cid = ?", [old["cid"]]).fetchone() == (None,)


def compact_keep_and_export():
    """@compact: valid rows bit-identical; invalid rows keep exactly their inputs/ids and rejection reason, outputs dropped;
    explored is the same on compact and full commits (also with no valid row); sources.tsv -GLOB is never pruned;
    explored --export round-trips tan_beta ~ 1e7 exactly."""
    cols = sorted(lake.POINT_COLUMNS - {"campaign_id"}) + ["X_lambda6_times_tan_beta", "width_bb_GeV", "lambda1_reconstructed", "rejection_reason"]
    with tempfile.TemporaryDirectory() as t:
        t = Path(t); src, remote = t / "run", t / "remote"; src.mkdir()
        with open(src / "points.csv", "w") as f:
            f.write("campaign_id," + ",".join(cols) + "\n")
            for i in range(6):  # tan_beta 1e7 + 0.1234...: float32 would round it to 1e7
                r = dict(point_id=f"p{i}", theory_ok_v1=int(i == 0), g_physical_hphiphi_GeV=1.0000001 + i, mesh_leaf_id="A",
                         mphi_min_GeV=130, mphi_max_GeV=140, Mbar_min_GeV=130, Mbar_max_GeV=140, lambda7_input=0.0,
                         mh_input_GeV=125.2, tan_beta_input=1e7 + 0.123456789 * i, X_lambda6_times_tan_beta=0.1 + 1e-12 * i,
                         width_bb_GeV=1.234567890123e-9 * (i + 1), lambda1_reconstructed=0.25 + 1e-13 * i,
                         rejection_reason="none" if i == 0 else "check_unitarity_false")
                f.write("c," + ",".join(repr(r[c]) if isinstance(r[c], float) else str(r[c]) for c in cols) + "\n")
        (src / "mesh_state.json").write_text("{}")
        plain = lake.cmd_commit(ns(remote, dir=str(src), table=["pts=points.csv"]))
        small = lake.cmd_commit(ns(remote, dir=str(src), table=["pts=points.csv@compact"]))
        rec = json.loads((remote / "commits" / f"{small}.json").read_text())
        assert [(x["rows"], x.get("compact")) for x in rec["tables"]] == [(1, None), (5, "invalid_inputs_only")], rec["tables"]
        con = duckdb.connect()
        inv = str(remote / "tables" / "pts" / f"commit={small}" / "part-1.parquet")
        kept = [c[0] for c in con.execute(f"DESCRIBE SELECT * FROM '{inv}'").fetchall()]
        assert set(kept) == set(lake.POINT_COLUMNS) - {"g_physical_hphiphi_GeV"} | {"X_lambda6_times_tan_beta", "rejection_reason", "commit"}, kept
        get = lambda cid: {r[0]: r for r in con.execute(f"SELECT point_id, * EXCLUDE (point_id, commit) FROM read_parquet("
                           f"'{remote}/tables/pts/*/*.parquet', hive_partitioning=true, union_by_name=true) WHERE commit = ?", [cid]).fetchall()}
        a, b = get(plain), get(small)
        names = [d[0] for d in con.execute(f"SELECT point_id, * EXCLUDE (point_id, commit) FROM read_parquet('{remote}/tables/pts/*/*.parquet', "
                                           "hive_partitioning=true, union_by_name=true) LIMIT 0").description]
        for pid in a:
            for n, x, y in zip(names, a[pid], b[pid]):
                assert y == (x if pid == "p0" or n in kept else None), (pid, n, x, y)
        assert b["p5"][names.index("tan_beta_input")] == 1e7 + 0.123456789 * 5
        assert b["p3"][names.index("rejection_reason")] == "check_unitarity_false"
        key = "tan_beta_input, X_lambda6_times_tan_beta, lambda7_input, mh_input_GeV, point_id"  # dedupe by inputs stays exact
        q = f"SELECT {key} FROM read_parquet('{remote}/tables/pts/*/*.parquet', hive_partitioning=true, union_by_name=true) WHERE commit = ?"
        assert con.execute(f"SELECT count(*) FROM ({q}) JOIN ({q}) USING ({key})", [plain, small]).fetchone()[0] == 6
        ex = lake.connect(argparse.Namespace(remote=str(remote), offline=True))
        view = lambda cid: ex.execute("SELECT * EXCLUDE (commit) FROM explored WHERE commit = ? ORDER BY ALL", [cid]).fetchall()
        assert view(plain) == view(small) and len(view(small)) == 6, (view(plain), view(small))

        none_valid = lake.compact(next((remote / "tables" / "pts" / f"commit={small}").glob("part-1*")), t / "v.parquet", t / "i.parquet")
        assert [n for _, n in none_valid] == [0, 5]  # empty valid part still carries the output columns explored needs

        real = lake.sources  # a "yes -*_state.json" row: the state file stays, the rest is pruned
        lake.sources = lambda: iter([(src, "candidate", True, [], ["*_state.json"])])
        try:
            lake.cmd_prune(argparse.Namespace(remote=str(remote), cid=small, yes=True, allow_unpushed=True, older_than=0))
        finally:
            lake.sources = real
        assert (src / "mesh_state.json").exists() and not (src / "points.csv").exists()

        out = t / "explored.csv"
        lake.cmd_explored(argparse.Namespace(remote=str(remote), offline=True, rows=10, lambda7="0", mh=None, tan_beta=None,
                                             mphi=None, mbar=None, export=str(out)))
        got = sorted(float(r["tan_beta"]) for r in csv.DictReader(open(out)))
        assert got == sorted(2 * [1e7 + 0.123456789 * i for i in range(6)]), got  # one row per leaf x commit, exact


if __name__ == "__main__":
    main()
