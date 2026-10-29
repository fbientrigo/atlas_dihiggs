#!/usr/bin/env python3
"""Offline check: submodules at their pins and clean, one convention YAML (dihiggs) with the pinned sha."""
import hashlib, subprocess, sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONV = "conventions/physics_conventions.yaml"
SHA = "4f3a938ed54dbc779d25f691ce1dd06fe17af69751105dc3b69ccb6b7d92fff6"
V3 = "physics_conventions_v3"
LOCKS = ("dihiggs_boundary", "dihiggs_hep_cross")  # external_tools.lock.yaml carries the sha pin


def git(repo, *args):
    p = subprocess.run(["git", "-C", str(ROOT / repo), *args], capture_output=True)
    return p.stdout if p.returncode == 0 else b""


def canonical(commit):  # convention bytes at a dihiggs commit, if it carries the pinned sha
    data = git("dihiggs", "show", f"{commit}:{CONV}")
    return data if hashlib.sha256(data).hexdigest() == SHA else None


def main():
    bad = []
    pins = {}
    for line in git(".", "ls-tree", "HEAD", "dihiggs", "dihiggs_boundary", "dihiggs_hep_cross", "dihiggs_ufo").decode().splitlines():
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
    for name in LOCKS:
        try:
            lock = yaml.safe_load((ROOT / name / "external_tools.lock.yaml").read_text())["conventions"]
            if (lock.get("sha256"), lock.get("schema_version")) != (SHA, V3):
                bad.append(f"{name}: external_tools.lock.yaml convention lock is stale")
        except (OSError, yaml.YAMLError, AttributeError, KeyError, TypeError) as exc:
            bad.append(f"{name}: external_tools.lock.yaml unreadable: {exc}")
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
