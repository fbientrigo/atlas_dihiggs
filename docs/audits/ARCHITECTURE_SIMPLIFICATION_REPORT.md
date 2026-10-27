# Architecture simplification report (branch `simplify/submodules`)

## Result
Overlays are committed upstream in each module; the root pins six modules as git submodules.
Bootstrap is `git clone --recursive <root>`; one module: `git clone <root> && git submodule update --init <name>`.

| module | pinned commit | remote location |
|---|---|---|
| dihiggs | 47fcfe8 (overlay on 087ba24) | new branch `feat/autoharness` (pushed; bundle no longer needed) |
| dihiggs_boundary | 8f032a7 | main (fast-forward from 32dd9df) |
| dihiggs_hep_cross | df95b4b | main (ff from f8893be) |
| dihiggs_llp_recast | 4d62c29 | main (ff from 72b8638) |
| dihiggs_ufo | 9a7ba38 | main (ff from 7dd02c1) |
| recast_viewer | b049d37 | main of atlas_recast_viewer (ff from 19c18ee) |

`git ls-remote` of each URL in `.gitmodules` lists the pinned commit (verified). No force push, no branch deleted, no `workspace-pin` branch needed (every base was the remote tip; `feat/autoharness` did not exist remotely).
Commit "Absorb atlas_dihiggs workspace overlay" contains exactly the paths of the old `overlay_files.json`; blob sha256 at HEAD equals the manifest for all 6 repos (0 mismatches). Convention YAMLs, CURRENT_CAMPAIGN.yaml and scripts unchanged byte-for-byte.

## Pre-existing local changes NOT committed (left in place)
These tracked modifications are outside the overlay (not mine, not discarded):
dihiggs 10 (2hdmc/*, orchestrator/cli.py, pilot csv/json...), dihiggs_boundary 5 (.gitignore, 2HDMC lib, data/runs/.gitkeep), dihiggs_hep_cross 379 (377 deleted tracked artifact/campaign files + 2 staged renames), dihiggs_ufo 1 (PACK_AA_PRESENTATION_EVIDENCE.zip deleted).
**Consequence: `check_workspace.py` reports "tracked modifications" in these 4 modules in the real workspace** (cleanliness is a required check); it passes in a fresh clone. Decision for the user: commit, stash, or `git checkout` those files. I did none of them.

## Safety proof (before -> after, `git status --porcelain | wc -l`; `du -s` KiB)
| repo | status before | after | tracked-mod before | after | du before | du after |
|---|---|---|---|---|---|---|
| dihiggs | 46 | 37 | 19 | 10 | 2017776 | 2017836 |
| dihiggs_boundary | 40 | 29 | 15 | 5 | 775092 | 775264 |
| dihiggs_hep_cross | 399 | 382 | 394 | 379 | 61616 | 61788 |
| dihiggs_llp_recast | 3 | 0 | 1 | 0 | 371420 | 371488 |
| dihiggs_ufo | 25 | 5 | 19 | 1 | 79080 | 79176 |
| recast_viewer | 1 | 0 | 1 | 0 | 674556 | 674600 |

Drops equal the overlay entries now committed; the du growth is the new commit objects. `.git` dirs stayed in place (`git submodule add` on existing repos; no absorbgitdirs), all branches/worktrees/untracked data untouched.

## Tests (overlay-touched, run before push)
boundary: 8 passed (test_conventions, test_external_tools). hep_cross: all passed, 1 skipped (5 files; needs `PYTHONSAFEPATH=1` because the repo's `py.py` shadows pytest's `py`). llp_recast: 1 passed. ufo: 1 passed. dihiggs, recast_viewer: overlay touches no tests.
`python lake/test_lake.py` -> `ok`.

## Fresh-clone proof
- `git clone --recursive /home/fabian/atlas_dihiggs` (branch simplify/submodules): 6 submodules at gitlinks, `scripts/check_workspace.py` -> `Workspace check: OK`.
- `git clone` + `git submodule update --init dihiggs_ufo`: only dihiggs_ufo populated (28 MB), other five `-` (uninitialised).

## Counts (root-tracked text files/lines; gitlinks excluded)
before: 38 files, 7410 lines (+1 binary bundle). after: 24 files + 6 gitlinks, 932 lines. check_workspace.py 178 -> 71 lines.

## Kept / removed
Kept: pin of 6 repos at exact commits (now gitlinks); per-module fetch; convention-source sha256 from the dihiggs gitlink with the SHA-256 constant; 4 caches + sidecars + external_tools.lock.yaml match; CURRENT_CAMPAIGN `madgraph.authoritative_results` null and physics_convention fields; sidecar/campaign `*_commit` must resolve in dihiggs and carry the pinned bytes; lake.py/sources.tsv/test_lake.py; tasks 003-012; alias symlinks, graphify-out, mission_runs, reports, experiments, results, env.sh, tests/, docs/audits.
Removed: patches/* (6 patches + base bundle), lake/overlay_files.json, lake/repos.tsv, lake/bootstrap.sh, scripts/bootstrap_workspace.py + its test (bootstrap = git), overlay-vs-patch/bundle/post-image verification, pytest/PyYAML runtime version asserts (requirements.txt pins them), tasks 001/002, root tracking of HANDOFF_T2_T4.md (file kept on disk). requirements-minimal.txt renamed requirements.txt. .gitignore 78 -> 18 lines allowlist.
Behaviour change: submodule HEAD must equal gitlink and be clean; the old "dirty must equal overlay" check is replaced by "no tracked modifications".

## Docs still referencing deleted files (not edited, other worker owns)
docs/WORKSPACE_MAP.md, docs/ONBOARDING.md (bootstrap / repos.tsv / patches / requirements-minimal).

## Proposals (not implemented)
1. Single source for the convention YAML: keep only dihiggs's copy; downstream repos read it via the dihiggs submodule path instead of 4 byte-identical caches + sidecars.
2. Move lake/ to its own repo.
3. Cache/sidecar `source_commit` still names 087ba24 (pre-overlay); fine (check resolves it), but could be repointed when the YAML is next versioned.
4. Cleanup of the 379-file hep_cross deletions and other local edits so the real-workspace check can pass.
