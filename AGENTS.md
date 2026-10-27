# Workspace guidance

Read `README.md` and `docs/ONBOARDING.md` before working across repositories.
This root repository owns the workspace pins, overlays, bootstrap, and
lightweight checks; the six nested repositories own their code and contracts.

Before using a physics number, consult both
`dihiggs_hep_cross/docs/CURRENT_DATA_AUTHORITY.md` and
`dihiggs_hep_cross/state/CURRENT_CAMPAIGN.yaml`. Consult the theory convention
authority in `dihiggs/docs/PROJECT_PHYSICS_AUTHORITY.md` and
`dihiggs/conventions/physics_conventions.yaml` before interpreting points.
Never infer current authority from timestamps or local presence.

A MadGraph cross section needs its H2 mass, `GHphiphi`, coupling prescription,
process, collision energy, UFO identity, seed, and banner/source artifact.
The current-results registry is separate from the theory-convention authority;
do not promote results as part of environment setup.

Do not let bootstrap overwrite an existing nested checkout. Keep overlays
limited to deliberate workspace changes; preserve pre-existing local changes.
Do not download or synchronize remote data as part of setup.
