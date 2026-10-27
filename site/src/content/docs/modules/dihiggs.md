---
title: "Module // dihiggs"
description: "Canonical 2HDM Type-I parameter evaluation, decay widths, branching ratios, and theory convention authority."
---

<div class="wired-card">
  <div class="wired-card-header">
    <span>// module · dihiggs</span>
    <span class="wired-pill red">THEORY CONVENTION AUTHORITY</span>
  </div>
  <div class="wired-grid">
    <div><strong>REPOSITORY:</strong> <a href="https://github.com/fbientrigo/dihiggs">fbientrigo/dihiggs</a></div>
    <div><strong>PINNED COMMIT:</strong> <code>47fcfe8</code></div>
    <div><strong>PRIMARY ROLE:</strong> Theory Evaluation & Scans</div>
  </div>
</div>

## Scientific Responsibility

The `dihiggs` repository serves as the single source of truth for all theory definitions and 2HDM parameter evaluations across the workspace:

- **Theory Convention Authority**: Maintains canonical theory parameters in [`conventions/physics_conventions.yaml`](https://github.com/fbientrigo/dihiggs/blob/main/conventions/physics_conventions.yaml) and documented in [`docs/PROJECT_PHYSICS_AUTHORITY.md`](https://github.com/fbientrigo/dihiggs/blob/main/docs/PROJECT_PHYSICS_AUTHORITY.md).
- **Physical Evaluation**: Computes parameter construction, perturbativity, tree-level unitarity, positivity/stability, decay widths, branching ratios ($H_2 \to b\bar{b}$), and proper lifetimes ($c\tau$).
- **Active SM Higgs Mass**: Standard Model $m_h = 125.20\text{ GeV}$ (`mh_125p20_active_2026`).

---

## Key Executables & Drivers

- `dihiggs/app/Lambda1EvaluatorV2`: Point evaluation for explicit $(m_H, \lambda_1)$ target inputs using schema `dihiggs.lambda1.v2`.
- `dihiggs/app/DihiggsPointV2Evaluator`: Rectangular grid evaluation in $(m_H, M_2)$ using schema `dihiggs.point.v2`.
- `dihiggs/src/ColabRecomputeValidation.cpp`: Cross-validation between legacy Colab analytical implementations and 2HDMC base calculator.

---

## Authoritative Documentation Links

- [GitHub Repository](https://github.com/fbientrigo/dihiggs)
- [Repository README](https://github.com/fbientrigo/dihiggs#readme)
- [Project Physics Authority](https://github.com/fbientrigo/dihiggs/blob/main/docs/PROJECT_PHYSICS_AUTHORITY.md)
- [Canonical Evaluators v2 Contract](https://github.com/fbientrigo/dihiggs/blob/main/docs/contracts/canonical_evaluators_v2.md)
- [Quickstart Guide](https://github.com/fbientrigo/dihiggs/blob/main/docs/quickstart.md)
- [Physics Conventions YAML](https://github.com/fbientrigo/dihiggs/blob/main/conventions/physics_conventions.yaml)

---

## API Reference

Symbols for this module are listed per source file in the [API reference](/api/); the coverage table links to each group.
