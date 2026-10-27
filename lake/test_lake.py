"""Roundtrip: commit -> verify -> prune -> restore, plus safety guards and the explored view, with a local-dir remote
(no Drive needed). Run: python test_lake.py"""
import argparse, json, os, subprocess, sys, tempfile
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
    explored_and_old_records()
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
            "lambda7": None, "mh": None, "tan_beta": None, "mphi": None, "mbar": None, **kw}))
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


if __name__ == "__main__":
    main()
