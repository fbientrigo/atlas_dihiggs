#!/usr/bin/env python3
"""Clone pinned nested repositories and apply their reviewed root overlays."""

from __future__ import annotations

import os
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOS_FILE = Path(os.environ.get("ATLAS_REPOS_FILE", ROOT / "lake/repos.tsv"))
EXPECTED_FILES = json.loads((ROOT / "lake/overlay_files.json").read_text(encoding="utf-8"))
ENV_PATH = Path(os.environ.get("ATLAS_VENV_PATH", ROOT / ".venv"))
if not ENV_PATH.is_absolute():
    ENV_PATH = ROOT / ENV_PATH


def run(args: list[str], cwd: Path | None = None, *, check: bool = True) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if check and result.returncode:
        raise RuntimeError(f"{' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def patch_paths(patch: Path) -> set[str]:
    paths: set[str] = set()
    for line in patch.read_text(encoding="utf-8").splitlines():
        if line.startswith("+++ b/"):
            paths.add(line[6:])
        elif line.startswith("--- a/"):
            paths.add(line[6:])
    return paths


def dirty_paths(repo: Path) -> set[str]:
    output = subprocess.run(
        ["git", "status", "--porcelain", "-z", "--untracked-files=all"], cwd=repo,
        text=True, capture_output=True, check=True,
    ).stdout
    return {
        row[3:].split(" -> ")[-1]
        for row in output.split("\0")
        if row
    }


def patch_applied(repo: Path, patch: Path) -> bool:
    return subprocess.run(
        ["git", "apply", "--reverse", "--check", str(patch)], cwd=repo,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


def postimage_matches(repo: Path, expected: dict[str, str | None]) -> bool:
    for relpath, digest in expected.items():
        path = repo / relpath
        if digest is None:
            if path.exists():
                return False
        elif digest.startswith("symlink:"):
            if not path.is_symlink() or os.readlink(path) != digest.removeprefix("symlink:"):
                return False
        elif not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            return False
    return True


def install_one(
    name: str, url: str, sha: str, patch_name: str, patch_sha: str,
    bundle_name: str, bundle_sha: str,
) -> str:
    target = ROOT / name
    patch = ROOT / patch_name
    if not patch.is_file():
        raise RuntimeError(f"{name}: missing declared overlay {patch_name}")
    actual_patch_sha = hashlib.sha256(patch.read_bytes()).hexdigest()
    if actual_patch_sha != patch_sha:
        raise RuntimeError(f"{name}: overlay SHA-256 mismatch for {patch_name}")
    bundle = ROOT / bundle_name if bundle_name != "-" else None
    if (bundle is None) != (bundle_sha == "-"):
        raise RuntimeError(f"{name}: bundle path/checksum must both be present or both be '-'")
    if bundle is not None and (
        not bundle.is_file() or hashlib.sha256(bundle.read_bytes()).hexdigest() != bundle_sha
    ):
        raise RuntimeError(f"{name}: missing or checksum-mismatched Git bundle {bundle_name}")
    expected_paths = patch_paths(patch)
    expected_files = EXPECTED_FILES.get(name, {})
    if set(expected_files) != expected_paths:
        raise RuntimeError(f"{name}: expected-file manifest differs from patch paths")
    if target.exists():
        if not (target / ".git").exists():
            raise RuntimeError(f"{name}: path exists without .git; left untouched")
        head = run(["git", "rev-parse", "HEAD"], target)
        actual_paths = dirty_paths(target)
        if head != sha:
            raise RuntimeError(f"{name}: HEAD {head} != pinned {sha}; left untouched")
        if (
            actual_paths == expected_paths
            and (not expected_paths or patch_applied(target, patch))
            and postimage_matches(target, expected_files)
        ):
            return f"{name}: pinned checkout and overlay already match"
        if not actual_paths:
            if expected_paths:
                run(["git", "apply", str(patch)], target)
            if not postimage_matches(target, expected_files):
                raise RuntimeError(f"{name}: overlay post-image verification failed")
            return f"{name}: applied overlay to pinned clean checkout"
        extra = sorted(actual_paths - expected_paths)
        missing = sorted(expected_paths - actual_paths)
        raise RuntimeError(
            f"{name}: dirty checkout does not match overlay; left untouched "
            f"(unexpected paths={extra}, missing overlay paths={missing}). "
            "Preserve it and bootstrap into a fresh workspace directory."
        )

    parent = ROOT / ".bootstrap-tmp"
    parent.mkdir(exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f"{name}-", dir=parent)) / name
    try:
        run(["git", "clone", "--filter=blob:none", "--no-checkout", url, str(temp)])
        if bundle is not None:
            run(["git", "bundle", "verify", str(bundle)], temp)
            heads = run(["git", "bundle", "list-heads", str(bundle)]).splitlines()
            refs = [line.split(maxsplit=1)[1] for line in heads if line.split(maxsplit=1)[0] == sha]
            if not refs:
                raise RuntimeError(f"{name}: bundle does not contain pinned commit {sha}")
            run(["git", "fetch", str(bundle), f"{refs[0]}:refs/remotes/workspace/pinned-base"], temp)
        run(["git", "checkout", "--detach", sha], temp)
        if expected_paths:
            run(["git", "apply", str(patch)], temp)
        if (
            dirty_paths(temp) != expected_paths
            or (expected_paths and not patch_applied(temp, patch))
            or not postimage_matches(temp, expected_files)
        ):
            raise RuntimeError(f"{name}: overlay verification failed")
        temp.rename(target)
    finally:
        shutil.rmtree(temp.parent, ignore_errors=True)
    return f"{name}: cloned {sha[:12]} and applied overlay"


def main() -> int:
    errors: list[str] = []
    messages: list[str] = []
    for raw in REPOS_FILE.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.startswith("#"):
            continue
        fields = raw.split("\t")
        if len(fields) != 7:
            errors.append(f"invalid lock row: {raw}")
            continue
        try:
            messages.append(install_one(*fields))
        except (OSError, RuntimeError) as exc:
            errors.append(str(exc))
    print("\n".join(messages))
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors), file=sys.stderr)
        return 1
    env_python = ENV_PATH / "bin/python"
    if ENV_PATH.exists():
        if not env_python.exists():
            print(f"ERROR: {ENV_PATH} exists but is not a supported venv; left untouched", file=sys.stderr)
            return 1
        imports_ok = subprocess.run(
            [
                str(env_python), "-P", "-c",
                "import pytest, yaml; assert pytest.__version__ == '9.1.1'; "
                "assert yaml.__version__ == '6.0.3'",
            ],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ).returncode == 0
        if not imports_ok:
            print(
                f"ERROR: {ENV_PATH} lacks the pinned pytest/PyYAML versions; left untouched. "
                "Set ATLAS_VENV_PATH to a new directory.",
                file=sys.stderr,
            )
            return 1
        print(f"Python environment: reusing {ENV_PATH}")
    else:
        ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
        run([sys.executable, "-m", "venv", str(ENV_PATH)])
        requirements = ROOT / "requirements-minimal.txt"
        run([str(env_python), "-m", "pip", "install", "-r", str(requirements)])
        print(f"Python environment: created {ENV_PATH}")
    print(f"Next: {env_python} -P scripts/check_workspace.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
