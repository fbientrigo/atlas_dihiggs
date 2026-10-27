#!/usr/bin/env python3
"""Lightweight offline check of pins, overlays, YAML authority, and tooling."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FILES = json.loads((ROOT / "lake/overlay_files.json").read_text(encoding="utf-8"))
CONVENTION_COMMIT = "087ba246e9a9fa34b16249b52629a62703893b5c"
CONVENTION_PATH = "conventions/physics_conventions.yaml"
CONVENTION_SHA256 = "4f3a938ed54dbc779d25f691ce1dd06fe17af69751105dc3b69ccb6b7d92fff6"
CONVENTION_CACHES = ("dihiggs_boundary", "dihiggs_hep_cross", "dihiggs_ufo", "dihiggs_llp_recast")


def git(*args: str, cwd: Path) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        return ""
    return result.stdout.strip()


def status_paths(repo: Path) -> set[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain", "-z", "--untracked-files=all"], cwd=repo,
        text=True, capture_output=True, check=True,
    )
    return {
        row[3:].split(" -> ")[-1]
        for row in result.stdout.split("\0")
        if row
    }


def main() -> int:
    problems: list[str] = []
    if pytest.__version__ != "9.1.1" or yaml.__version__ != "6.0.3":
        problems.append(
            f"unexpected lightweight package versions: pytest={pytest.__version__}, "
            f"PyYAML={yaml.__version__}"
        )
    for raw in (ROOT / "lake/repos.tsv").read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.startswith("#"):
            continue
        name, _url, sha, patch_name, patch_sha, bundle_name, bundle_sha = raw.split("\t")
        repo, patch = ROOT / name, ROOT / patch_name
        if not patch.is_file() or hashlib.sha256(patch.read_bytes()).hexdigest() != patch_sha:
            problems.append(f"{name}: missing or checksum-mismatched overlay {patch_name}")
            continue
        if bundle_name != "-":
            bundle = ROOT / bundle_name
            if not bundle.is_file() or hashlib.sha256(bundle.read_bytes()).hexdigest() != bundle_sha:
                problems.append(f"{name}: missing or checksum-mismatched pinned commit bundle")
                continue
            bundle_heads = subprocess.run(
                ["git", "bundle", "list-heads", str(bundle)], cwd=repo,
                text=True, capture_output=True,
            )
            if bundle_heads.returncode or sha not in {
                row.split(maxsplit=1)[0] for row in bundle_heads.stdout.splitlines() if row
            }:
                problems.append(f"{name}: Git bundle does not contain pinned commit {sha}")
                continue
        if not (repo / ".git").exists():
            problems.append(f"{name}: repository missing (run bash lake/bootstrap.sh)")
            continue
        head = git("rev-parse", "HEAD", cwd=repo)
        if head != sha:
            problems.append(f"{name}: HEAD {head or 'unavailable'} differs from pin {sha}")
            continue
        expected_files = EXPECTED_FILES.get(name, {})
        patch_paths = {
            line[6:]
            for line in patch.read_text(encoding="utf-8").splitlines()
            if line.startswith("+++ b/") or line.startswith("--- a/")
        }
        if patch_paths != set(expected_files):
            problems.append(f"{name}: overlay post-image manifest differs from patch")
            continue
        applied = subprocess.run(
            ["git", "apply", "--reverse", "--check", str(patch)], cwd=repo,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ).returncode == 0
        actual_paths = status_paths(repo)
        postimage_ok = all(
            (not (repo / path).exists()) if digest is None else
            ((repo / path).is_symlink() and (repo / path).readlink().as_posix() == digest.removeprefix("symlink:")) if digest.startswith("symlink:") else
            (repo / path).is_file() and hashlib.sha256((repo / path).read_bytes()).hexdigest() == digest
            for path, digest in expected_files.items()
        )
        if (
            (not applied and expected_files)
            or actual_paths != set(expected_files)
            or not postimage_ok
        ):
            problems.append(f"{name}: workspace overlay is absent or differs")
    authority_repo = ROOT / "dihiggs"
    source = subprocess.run(
        ["git", "show", f"{CONVENTION_COMMIT}:{CONVENTION_PATH}"],
        cwd=authority_repo, capture_output=True, check=False,
    )
    if source.returncode:
        problems.append("canonical physics convention source commit is unavailable")
    elif hashlib.sha256(source.stdout).hexdigest() != CONVENTION_SHA256:
        problems.append("canonical physics convention source bytes do not match the pinned SHA-256")
    for name in CONVENTION_CACHES:
        repo = ROOT / name
        cache_path = repo / CONVENTION_PATH
        sidecar_path = repo / "conventions/physics_conventions.lock.yaml"
        lock_path = repo / "external_tools.lock.yaml"
        try:
            cache_bytes = cache_path.read_bytes()
            cache_hash = hashlib.sha256(cache_bytes).hexdigest()
            sidecar = yaml.safe_load(sidecar_path.read_text(encoding="utf-8"))
            cache_yaml = yaml.safe_load(cache_bytes)
            lock = yaml.safe_load(lock_path.read_text(encoding="utf-8")) if lock_path.is_file() else None
            expected_sidecar = {
                "source_repository": "fbientrigo/dihiggs",
                "source_commit": CONVENTION_COMMIT,
                "source_path": CONVENTION_PATH,
                "source_sha256": CONVENTION_SHA256,
                "schema_version": "physics_conventions_v3",
            }
            if cache_hash != CONVENTION_SHA256 or cache_bytes != source.stdout:
                problems.append(f"{name}: convention cache differs from pinned canonical source")
            if not isinstance(sidecar, dict) or any(sidecar.get(k) != v for k, v in expected_sidecar.items()):
                problems.append(f"{name}: convention provenance sidecar is missing or stale")
            if not isinstance(cache_yaml, dict) or cache_yaml.get("schema_version") != "physics_conventions_v3":
                problems.append(f"{name}: convention cache is not v3")
            if lock is not None:
                declared = lock.get("conventions", {})
                if declared.get("sha256") != CONVENTION_SHA256 or declared.get("schema_version") != "physics_conventions_v3":
                    problems.append(f"{name}: external-tools convention lock is stale")
        except (OSError, yaml.YAMLError) as exc:
            problems.append(f"{name}: convention cache or provenance could not be read: {exc}")
    try:
        campaign = yaml.safe_load(
            (ROOT / "dihiggs_hep_cross/state/CURRENT_CAMPAIGN.yaml").read_text()
        )
        authority = ROOT / "dihiggs_hep_cross/docs/CURRENT_DATA_AUTHORITY.md"
        print(f"Campaign status: {campaign.get('status', 'unspecified')}")
        print(f"Authoritative MadGraph results: {campaign.get('madgraph', {}).get('authoritative_results')}")
        if not authority.is_file():
            problems.append("current data-authority document is missing")
        madgraph = campaign.get("madgraph", {})
        if not isinstance(madgraph, dict) or "authoritative_results" not in madgraph:
            problems.append("campaign YAML has no madgraph.authoritative_results field")
        elif madgraph["authoritative_results"] is not None:
            problems.append("workspace setup must preserve null MadGraph result authority")
        physics = campaign.get("physics_convention", {})
        if not isinstance(physics, dict) or any(physics.get(key) != value for key, value in {
            "authority_commit": CONVENTION_COMMIT,
            "authority_sha256": CONVENTION_SHA256,
            "schema_version": "physics_conventions_v3",
            "m_h_GeV": "125.20",
        }.items()):
            problems.append("campaign physics convention reference does not match the pinned v3 authority")
    except (OSError, yaml.YAMLError, AttributeError) as exc:
        problems.append(f"campaign authority could not be read: {exc}")
    if problems:
        print("Workspace check: NEEDS ATTENTION", file=sys.stderr)
        print("\n".join(f"- {item}" for item in problems), file=sys.stderr)
        return 1
    print("Workspace check: pins, overlays, and lightweight environment are valid.")
    print("No physics build, simulation, remote data access, or scientific validation was run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
