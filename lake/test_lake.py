"""Roundtrip: commit -> verify -> prune -> restore, with a local-dir remote (no Drive needed). Run: python test_lake.py"""
import argparse, json, subprocess, sys, tempfile
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
    print("ok")


if __name__ == "__main__":
    main()
