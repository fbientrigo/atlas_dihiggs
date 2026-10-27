# Agent Guidance

Consult [README.md](README.md) for workspace architecture, submodules, and physics authority rules.

- **Submodule boundaries**: Nested repositories own their code, tests, and contracts; keep edits scoped.
- **Physics authority**: Never promote results, alter campaign state, or infer authority from file timestamps or presence.
- **Cross sections**: MadGraph cross sections require full provenance (H2 mass, `GHphiphi`, prescription, process, energy, UFO ID, seed, banner).
- **Environment**: Do not download remote data or modify nested checkouts during setup.
