#!/usr/bin/env python3
"""Offline regression for pinned clone, bundle, overlay, and dirty-path safety."""

import hashlib
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("bootstrap_workspace.py")
SPEC = importlib.util.spec_from_file_location("bootstrap_workspace", SCRIPT)
bootstrap = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(bootstrap)


def git(*args: str, cwd: Path) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True)
    return result.stdout.strip()


class BootstrapWorkspaceTest(unittest.TestCase):
    def test_bundle_overlay_idempotence_and_dirty_checkout_protection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            git("init", "-q", cwd=source)
            git("config", "user.email", "test@example.invalid", cwd=source)
            git("config", "user.name", "Bootstrap test", cwd=source)
            (source / "value.txt").write_text("pinned\n")
            git("add", "value.txt", cwd=source)
            git("commit", "-qm", "baseline", cwd=source)
            commit = git("rev-parse", "HEAD", cwd=source)

            bare = root / "remote.git"
            subprocess.run(["git", "clone", "--bare", str(source), str(bare)], check=True, capture_output=True)
            (source / "bundle-only.txt").write_text("not on the published baseline\n")
            git("add", "bundle-only.txt", cwd=source)
            git("commit", "-qm", "bundled revision", cwd=source)
            commit = git("rev-parse", "HEAD", cwd=source)
            missing = subprocess.run(
                ["git", "cat-file", "-e", commit], cwd=bare,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            self.assertNotEqual(missing.returncode, 0)
            bundle = root / "base.bundle"
            git("bundle", "create", str(bundle), "--all", cwd=source)

            (source / "value.txt").write_text("workspace overlay\n")
            patch = root / "overlay.patch"
            diff = subprocess.run(["git", "diff", "--", "value.txt"], cwd=source, text=True, capture_output=True, check=True).stdout
            patch.write_text(diff)
            (source / "value.txt").write_text("pinned\n")
            patch_sha = hashlib.sha256(patch.read_bytes()).hexdigest()
            bundle_sha = hashlib.sha256(bundle.read_bytes()).hexdigest()
            expected_sha = hashlib.sha256(b"workspace overlay\n").hexdigest()

            bootstrap.ROOT = root
            bootstrap.EXPECTED_FILES = {"sample": {"value.txt": expected_sha}}
            result = bootstrap.install_one(
                "sample", str(bare), commit, "overlay.patch", patch_sha,
                "base.bundle", bundle_sha,
            )
            self.assertIn("cloned", result)
            target = root / "sample"
            self.assertEqual((target / "value.txt").read_text(), "workspace overlay\n")
            self.assertIn("already match", bootstrap.install_one(
                "sample", str(bare), commit, "overlay.patch", patch_sha,
                "base.bundle", bundle_sha,
            ))

            (target / "value.txt").write_text("developer change\n")
            with self.assertRaisesRegex(RuntimeError, "left untouched"):
                bootstrap.install_one(
                    "sample", str(bare), commit, "overlay.patch", patch_sha,
                    "base.bundle", bundle_sha,
                )
            self.assertEqual((target / "value.txt").read_text(), "developer change\n")

            nested = target / "conventions" / "new" / "local.yaml"
            nested.parent.mkdir(parents=True)
            nested.write_text("keep me\n")
            with self.assertRaisesRegex(RuntimeError, "left untouched"):
                bootstrap.install_one(
                    "sample", str(bare), commit, "overlay.patch", patch_sha,
                    "base.bundle", bundle_sha,
                )
            self.assertEqual(nested.read_text(), "keep me\n")


if __name__ == "__main__":
    unittest.main()
