#!/usr/bin/env python3
"""Offline check: submodules at their pins and clean, convention authority and caches intact."""
import hashlib, subprocess, sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONV = "conventions/physics_conventions.yaml"
SIDECAR = "conventions/physics_conventions.lock.yaml"
SHA = "4f3a938ed54dbc779d25f691ce1dd06fe17af69751105dc3b69ccb6b7d92fff6"
V3 = "physics_conventions_v3"
CACHES = ("dihiggs_boundary", "dihiggs_hep_cross", "dihiggs_ufo", "dihiggs_llp_recast")


def git(repo, *args):
    p = subprocess.run(["git", "-C", str(ROOT / repo), *args], capture_output=True)
    return p.stdout if p.returncode == 0 else b""


def canonical(commit):  # convention bytes at a dihiggs commit, if it carries the pinned sha
    data = git("dihiggs", "show", f"{commit}:{CONV}")
    return data if hashlib.sha256(data).hexdigest() == SHA else None


def main():
    bad = []
    pins = {}
    for line in git(".", "ls-tree", "HEAD", "dihiggs", "recast_viewer", *CACHES).decode().splitlines():
        meta, name = line.split("\t")
        pins[name] = meta.split()[2]
    for name, pin in pins.items():
        if git(name, "rev-parse", "HEAD").decode().strip() != pin:
            bad.append(f"{name}: HEAD differs from gitlink {pin[:12]} (git submodule update --init {name})")
        elif git(name, "status", "--porcelain", "-uno"):
            bad.append(f"{name}: tracked modifications")
    source = canonical(pins["dihiggs"])
    if source is None:
        bad.append("dihiggs gitlink does not carry the pinned convention bytes")
    for name in CACHES:
        repo = ROOT / name
        try:
            side = yaml.safe_load((repo / SIDECAR).read_text())
            lock = repo / "external_tools.lock.yaml"
            lock = yaml.safe_load(lock.read_text()) if lock.is_file() else None
            cache = (repo / CONV).read_bytes()
            if cache != source:
                bad.append(f"{name}: convention cache differs from canonical source")
            if (side.get("source_sha256"), side.get("schema_version"), side.get("source_path")) != (SHA, V3, CONV) \
                    or side.get("source_repository") != "fbientrigo/dihiggs" or canonical(side.get("source_commit", "")) is None:
                bad.append(f"{name}: provenance sidecar missing or stale")
            if lock and (lock["conventions"].get("sha256"), lock["conventions"].get("schema_version")) != (SHA, V3):
                bad.append(f"{name}: external_tools.lock.yaml convention lock is stale")
        except (OSError, yaml.YAMLError, AttributeError, KeyError) as exc:
            bad.append(f"{name}: convention files unreadable: {exc}")
    try:
        c = yaml.safe_load((ROOT / "dihiggs_hep_cross/state/CURRENT_CAMPAIGN.yaml").read_text())
        if c["madgraph"]["authoritative_results"] is not None:
            bad.append("madgraph.authoritative_results must stay null")
        p = c["physics_convention"]
        if (p.get("authority_sha256"), p.get("schema_version"), p.get("m_h_GeV")) != (SHA, V3, "125.20") \
                or canonical(p.get("authority_commit", "")) is None:
            bad.append("CURRENT_CAMPAIGN physics_convention does not match the v3 authority")
    except (OSError, yaml.YAMLError, AttributeError, KeyError, TypeError) as exc:
        bad.append(f"CURRENT_CAMPAIGN.yaml unreadable: {exc}")
    print("\n".join(["Workspace check: NEEDS ATTENTION", *("- " + b for b in bad)]) if bad else "Workspace check: OK")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
