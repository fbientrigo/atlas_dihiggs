# DiHiggs workspace

This workspace combines six independently versioned repositories for the
2HDM Type-I theory evaluation, production, LLP recast, and visualization
workflow. Start with the [new-machine guide](docs/ONBOARDING.md), then use the
[workspace map](docs/WORKSPACE_MAP.md) to find the owner of each contract.

Before citing any physics number, read the [data-authority contract](dihiggs_hep_cross/docs/CURRENT_DATA_AUTHORITY.md)
and [campaign registry](dihiggs_hep_cross/state/CURRENT_CAMPAIGN.yaml). A
timestamp or a result file alone does not establish that a result is current.

The root repository versions workspace-level documentation, bootstrap
configuration, and lightweight validation. Each nested directory is an
independent Git repository; its commit and the root overlay are pinned in
[`lake/repos.tsv`](lake/repos.tsv) and [`patches/`](patches/).
