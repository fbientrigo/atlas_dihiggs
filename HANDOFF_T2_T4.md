# Handoff T2 → T4

Prioridad vigente: resolver T2 (viabilidad física) antes de la integración final de T4. No iniciar desarrollo nuevo al retomar sin atender primero esa prioridad.

## Estado de la sesión y alcance

- Sesión ejecutada en **debsat**, workspace `/home/fabian/atlas_dihiggs`; no en el nodo solicitado `nasapcdeb`.
- T4 llegó únicamente al reconocimiento local, de solo lectura. No se implementó la interfaz, no se ejecutaron tests ni el baseline T4, no se inició compilación ni piloto remoto.
- No había una operación científica propia en curso al recibir el cambio de prioridad. Se terminó únicamente la captura segura de estado y este handoff.
- El único archivo creado para este cierre es `HANDOFF_T2_T4.md`. No se modificaron código, autoridades, UFO, resultados históricos ni archivos de configuración científica durante T4.
- El intento SSH con `StrictHostKeyChecking=accept-new` añadió la clave pública del host a `~/.ssh/known_hosts`; no se obtuvo acceso. No se consultaron ni copiaron claves privadas.
- El workspace raíz tiene un repositorio Git independiente inicialmente sin commits (rama `master`). Para el checkpoint documental se creó `checkpoint/t2-t4-handoff-20261008`; no se cambiaron las ramas de los repositorios de código. El checkpoint registra solo este handoff, sin incorporar cambios de otros trabajos. Su hash se obtiene con `git -C /home/fabian/atlas_dihiggs rev-parse HEAD` después del commit.

## Arquitectura encontrada y código reutilizable

| Archivo / módulo (rutas relativas al workspace) | Función y hallazgo |
| --- | --- |
| `dihiggs/dihiggs/src/DihiggsPointV2Evaluator.cpp` | Evaluador canónico de coordenadas físicas. Ya recibe λ₆ y λ₇ explícitos; construye m₁₂² = M² sinβ cosβ y llama `THDM::set_param_phys`. Exporta reconstrucción, coupling con signo, controles y observables. |
| `dihiggs/dihiggs/src/Lambda1EvaluatorV2.cpp` | Ruta canónica de λ₁ fijo, con λ₆ y λ₇ externos en CSV. Usa `set_param_phys_lam1`; registra residual de λ₁. |
| `dihiggs/2hdmc/src/THDM.cpp` | 2HDMC parcheado: ambas rutas ya admiten λ₇. La ruta λ₁ deriva m₁₂² y posteriormente impone λ₁ solicitado; comprobar el residual previo, no confundir esa imposición con una reconstrucción independiente. |
| `dihiggs/dihiggs/app/orchestrator/lambda1_v2.py` | Dataclass de inputs, CSV, identificadores reproducibles, manifiestos y ejecución por lotes reutilizables. |
| `dihiggs/dihiggs/app/orchestrator/{cli.py,models.py,engines/m2.py}` | λ₇ ya atraviesa la interfaz y la ruta física. Falta contrato explícito de modos y regresiones dirigidas. |
| `dihiggs_boundary/src/evaluate_point.cpp` | Backend de compatibilidad fija `kLambda7 = 0`; sus contratos también congelan ese supuesto. No modificarlo indiscriminadamente. |
| `dihiggs/docs/contracts/canonical_evaluators_v2.md` | Contratos de evaluadores y persistencia. |
| `dihiggs/docs/theory/2hdm_conventions.md` | Convenciones genérica/Higgs Basis; contrastar con el apéndice canónico. |
| `dihiggs_hep_cross/docs/WORKSPACE_MAP.md` | Mapa de consumidores, producción y autoridad del workspace. |

Flujo actual: Python/input → evaluadores C++17 → 2HDMC/GSL (`THDM`, `Constraints`, `DecayTable`) → CSV/manifiestos → consumidores de frontera, producción y LLP. Las masas se construyen/reconstruyen en THDM; anchos y BR proceden de DecayTable; ctau usa hbar·c/Γ. La producción usa σ externa y los consumidores de eventos combinan luminosidad, producción, BR y aceptación según sus contratos. No se ejecutó MadGraph, CALCHEP, UFO ni recast para T4. No hace falta modificarlos para la preparación mínima de λ₇.

Unidades: masas y anchos en GeV; M² y m₁₂² en GeV²; λᵢ y Zᵢ adimensionales; ctau en mm. λᵢ son de base genérica, Zᵢ de Higgs Basis; M², m₁₂² y Y₂ no son intercambiables.

## Baseline y tests: identificados, no ejecutados para T4

Baseline propuesto desde `dihiggs/tests/test_dihiggs_point_v2.py`, `test_pilot_anchors_at_125_13`:

```text
mh = 125.13 GeV
mH = mφ = 200 GeV
mA = mH± = 500 GeV
sin(β−α) = 1
tanβ = 10000
M² = 39999.9995713761 GeV²
λ₆ = 1e-10
λ₇ = 0
m₁₂² dependiente = M² sinβ cosβ
```

El test existente espera `theory_ok = 1`; esto es una expectativa histórica, no un resultado nuevo obtenido aquí. Segundo control candidato: `test_validated_h2_benchmark_exports_frozen_coupling` (mφ=150, mA=mH±=450, t=300000, M²=22499.999999500335, λ₆=1e-10, λ₇=0). No mezclar parámetros entre ambos.

Pruebas ya disponibles: schema/cardinalidad/provenance, reproducción determinista, m₁₂²/M², coupling con signo, clasificación de fallos de construcción y teoría, observables y anclas históricas; `test_golden_lambda1.py` cubre serialización/residuales y clasificación no finita.

Pendientes de T4: λ₇=0 contra baseline medido; propagación de λ₇≠0 y conservación de λ₆; cierre independiente del espectro; modos legacy/explicit/analytic; rechazo claro del analítico sin contrato; unidades y signos; tanβ≈10⁶ sin NaN/Inf silenciosos; separación de rechazo físico y fallo numérico; incompatibilidad de inputs; reproducibilidad. No se autoriza ocultar discrepancias ampliando tolerancias.

## Decisiones pendientes y riesgos científicos para T2

1. **No se derivó ni implementó una fórmula analítica de λ₇.** Recibir contrato validado T1: ecuación exacta, definiciones/signos/bases, parámetros independientes y dependientes, ramas, dominio, singularidades, forma estable a t alto y puntos de referencia numéricos.
2. Evaluar primero en T2 si la propuesta λ₁ fijo + M²=mh²/2 tiene región viable con los controles originales. Fijar esas condiciones junto con λ₆ y t exige resolver λ₇ consistentemente; no tratarlas como coordenadas independientes libres.
3. No trasladar automáticamente identidades previamente usadas con λ₇=0 al caso λ₇≠0. Auditar especialmente la relación entre Y₂ y M² y el coupling antes de afirmar equivalencias físicas.
4. Los términos λ₇·t³ de la inversión y `beta=atan(t)`/`cos(beta)` pueden amplificar cancelaciones a t alto. Distinguir inputs solicitados, valores reconstruidos y residual previo al ajuste de λ₁. Getters cacheados no prueban el espectro por sí solos.
5. El mandato T4 fija mh=125.13; autoridades actuales del workspace usan 125.20. Registrar la comparación histórica explícitamente, sin cambiar autoridades ni usar defaults actuales silenciosamente.
6. El usuario proporcionó el texto del apéndice canónico en la conversación previa; no se encontró el archivo completo `appendix_2hdm_with_gao(1).tex` en el checkout inspeccionado. Existe un extracto preservado en la campaña anterior; no presentarlo como copia íntegra del apéndice.
7. Pasar controles escalares no equivale a viabilidad física general: separar Yukawa, mínimo global y restricciones experimentales; informar lo pendiente.

Diseño mínimo propuesto, aún no implementado: registrar `legacy` (λ₇=0), `explicit` (valor externo conservado) y `analytic` (error claro hasta recibir contrato). Reutilizar la ruta C++ existente y el manifiesto Python; no cambiar UFO ni normalización T3.

## Acceso remoto y recursos

`ssh nasapcdeb` no resuelve el alias. Tailscale mostró `nasapcdeb` online en `100.114.108.82` (`nasapcdeb.tail76e833.ts.net`), pero `ssh fabian@100.114.108.82` terminó en `Permission denied (publickey)` después de aceptar la clave pública de host. Falta destino/usuario autenticable y ruta del checkout remoto. Estado remoto, branch, procesos y recursos **no verificados**.

Antes de futuros jobs pesados en ese nodo: `lab-health`, piloto pequeño y medición real. Jobs largos mediante tmux y wrappers disponibles:

```sh
SAFE_MEM=11G SAFE_HIGH=9G SAFE_CPU=900% runlog safe-run bash -lc 'COMANDO'
```

## Jobs al cierre: evitar duplicación

En debsat, captura local de procesos: no aparecieron evaluadores, búsquedas, pytest, MadGraph, safe-run/runlog ni monitor de la campaña propios activos. El agente `t4_inventory` está completado; no hay worker T4 ejecutándose.

Sesiones tmux existentes (ajenas o de infraestructura; no detenerlas):

- `dihiggs1006`: pane 0.0, PID 4171623 (shell), comando actual `codex`, cwd workspace.
- `meeting_http`: pane 0.0, PID 2330386, `python3 -m http.server 8765 --bind 100.104.114.38`, cwd `/home/fabian/evidence/dihiggs_m2_vs_mphi_20260920/meeting_final`.
- `4`, `rootkata`, `sprint1`: shells en otros proyectos.

También continúa el servicio ajeno `jev_gateway_proxy.py`, PID 3565719. No se terminaron procesos. Verificar jobs remotos cuando haya acceso; no asumir que no existen allí.

## Resultados previos conservados (exploratorios, no autoridad promovida)

Se preservan íntegros los directorios existentes:

- `dihiggs_hep_cross/campaigns/20261006_honly_production_pilot/`
- `dihiggs_hep_cross/campaigns/20261006_y2_zero_directed_search/`
- `dihiggs_hep_cross/campaigns/20261007_positive_g_envelope/`

La última campaña ya contiene `meeting_packet.tar.gz`, `campaign_raw_cache.tar.gz`, README, scripts reproducibles, candidatos y revisión independiente. `final_validation_summary.json` registra 122 candidatos de envolvente reevaluados y aceptados por controles escalares, 3 anclas Y₂=0, 61 probes y 26 candidatos con advertencia de precisión. Hay huecos de exploración/fronteras altas pendientes; estos datos no demuestran máximos globales ni viabilidad general y no son una validación T4 de λ₇≠0. No relanzar esa campaña al retomar T2/T4.

## Comandos y verificaciones de esta preparación/cierre

Reconocimiento: lectura de AGENTS/RTK/README/contratos/autoridades, `hostname`, Git branch/HEAD/status, consultas de código y grafo existente, Tailscale y los intentos SSH indicados. Cierre: Git branch/HEAD/status de todos los repositorios, `ps`, `tmux list-sessions/list-panes`, lectura de `final_validation_summary.json`, escritura de este documento y commit documental local. Los comandos shell se ejecutaron mediante `rtk proxy`. No se ejecutaron tests de física para T4, builds ni jobs pesados; no hay resultados de regresión nuevos que reportar.

## Instrucción corta para retomar

**Leer este handoff y las autoridades; continuar con T2 y recibir el contrato T1. Resolver acceso a nasapcdeb y comprobar jobs antes de cualquier ejecución. Solo tras la decisión de viabilidad, reanudar T4 desde el baseline histórico en una rama dedicada: medir baseline → interfaz mínima → regresiones → revisión independiente del diff. No push ni merge.**

## Snapshot Git al cierre, antes del commit documental

Los cambios listados a continuación permanecen en disco. Eran previos al reconocimiento T4; no se descartaron ni se incluyeron en el checkpoint documental. `git status --short` incluye cambios de otros trabajos y paquetes exploratorios. Las eliminaciones ya presentes en `dihiggs_ufo` no fueron hechas por esta sesión.

Captura UTC: 2026-10-08T04:00:16.074865+00:00

### .

Rama: `checkpoint/t2-t4-handoff-20261008`

HEAD: sin commit previo (repositorio raíz)

```text
?? .venv-rebuild-20260924/
?? AGENTS.md
?? CLAUDE.md
?? MG5_debug
?? appendix.tex
?? boundary
?? codex-session-01a1143f-ec3c-7260-b983-b41d2e6b704c.md
?? dihiggs-cleanrefactor-3-10-preserve-the-signed-physical/
?? dihiggs/
?? dihiggs_boundary/
?? dihiggs_hep_cross/
?? dihiggs_llp_recast/
?? dihiggs_ufo/
?? env.sh
?? graphify-out/
?? hep_cross
?? llm_wiki
?? llp_recast
?? main_dihiggs
?? mission_runs/
?? notas/
?? py.py
?? recast_viewer/
?? runs/
?? ufos
?? untitled-2.md
?? untitled-3.md
?? untitled.md
```

### dihiggs

Rama: `feat/autoharness`

HEAD: `087ba246e9a9fa34b16249b52629a62703893b5c`

```text
M docs/pilots/high_mass_h2_v1/pilot_points.csv
 M docs/pilots/high_mass_h2_v1/pilot_validation.json
 M scripts/gemini_contract_templates.py
 M scripts/gemini_worker_loop.py
?? autoresearch/tests/test_jev_canonical_adapter.py
?? autoresearch/tests/test_jev_policy.py
?? autoresearch/tests/test_jev_run_once.py
?? scripts/jev_adapter.py
?? scripts/jev_decide_once.py
?? scripts/jev_policy.py
?? scripts/jev_run_once.py
?? scripts/jev_smoke.py
?? scripts/jev_worker_config.sample.json
```

### dihiggs_boundary

Rama: `main`

HEAD: `32dd9df533cd4b4d613daaf516b6b25254bdaf25`

```text
M .gitignore
 M lib/2HDMC-1.8.0/Makefile
 M lib/2HDMC-1.8.0/src/THDM.cpp
 M lib/2HDMC-1.8.0/src/THDM.h
?? campaigns/
?? configs/adaptive_m2_boundary_v1.yaml
?? configs/adaptive_m2_boundary_v1_extension.yaml
?? configs/adaptive_m2_exploration_v1.yaml
?? configs/profiled_m2_boundary_v1.yaml
?? configs/survivor_adaptive_12520_v1.yaml
?? docs/profiled_m2_boundary_v1_implementation.md
?? python/dhb/adaptive_exploration.py
?? python/dhb/adaptive_m2_mesh.py
?? python/dhb/profiled_m2_scan.py
?? python/dhb/survivor_adaptive_aggregate.py
?? python/dhb/survivor_adaptive_campaign.py
?? scripts/aggregate_adaptive_boundary.py
?? scripts/aggregate_profiled_boundary.py
?? scripts/aggregate_survivor_adaptive_12520.py
?? scripts/archive_adaptive_m2_boundary.py
?? scripts/run_adaptive_exploration.py
?? scripts/run_adaptive_m2_mesh.py
?? scripts/run_survivor_adaptive_12520.py
?? tests/test_adaptive_boundary_aggregate.py
?? tests/test_adaptive_m2_mesh.py
?? tests/test_profiled_boundary_aggregate.py
?? tests/test_profiled_m2_scan.py
?? tests/test_survivor_adaptive_12520_tanbeta_v2.py
?? tests/test_survivor_adaptive_campaign.py
```

### dihiggs_hep_cross

Rama: `main`

HEAD: `f8893bea1627b2091f4d3e782ed3a2d575066365`

```text
M campaigns/20260901_photonic_requalification/event_yields/event_yields_photonic_requalified.csv
 M campaigns/20260901_photonic_requalification/event_yields/photonic_tables_requalified.tex
 M campaigns/20260901_photonic_requalification/validated/REQUALIFICATION_SUMMARY.md
 M campaigns/20260901_photonic_requalification/validated/comparison_target_vs_validated.csv
 M campaigns/20260901_photonic_requalification/validated/photonic_requalified.csv
 M campaigns/20260901_photonic_requalification/work/calculator_runs/selected/out_mh125p00.csv
 M campaigns/20260901_photonic_requalification/work/calculator_runs/selected/out_mh125p20.csv
 M campaigns/physical_vs_effective_coupling_v1/2hdmc_build/CalcGen
 M campaigns/physical_vs_effective_coupling_v1/2hdmc_build/CalcLH
 M campaigns/physical_vs_effective_coupling_v1/2hdmc_build/GeneralProbe
 M campaigns/physical_vs_effective_coupling_v1/2hdmc_build/Makefile
 M campaigns/physical_vs_effective_coupling_v1/2hdmc_build/lib/Constraints.o
 M campaigns/physical_vs_effective_coupling_v1/2hdmc_build/lib/DecayTable.o
 M campaigns/physical_vs_effective_coupling_v1/2hdmc_build/lib/THDM.o
 M campaigns/physical_vs_effective_coupling_v1/2hdmc_build/lib/lib2HDMC.a
 M campaigns/physical_vs_effective_coupling_v1/2hdmc_build/src/THDM.cpp
 M campaigns/physical_vs_effective_coupling_v1/2hdmc_build/src/THDM.h
 M campaigns/physical_vs_effective_coupling_v1/COUPLING_STUDY_REPORT.md
 M campaigns/physical_vs_effective_coupling_v1/coupling_comparison/coupling_table.csv
 M campaigns/physical_vs_effective_coupling_v1/coupling_comparison/coupling_vs_mass.pdf
 M campaigns/physical_vs_effective_coupling_v1/coupling_comparison/coupling_vs_mass.png
 M campaigns/physical_vs_effective_coupling_v1/coupling_comparison/physical_vs_M2.pdf
 M campaigns/physical_vs_effective_coupling_v1/coupling_comparison/physical_vs_M2.png
RM campaigns/physical_vs_effective_coupling_v1/coupling_comparison/make_plot.py -> campaigns/physical_vs_effective_coupling_v1/coupling_comparison/plot_coupling_vs_mass.py
R  campaigns/physical_vs_effective_coupling_v1/coupling_comparison/make_plot_M2.py -> campaigns/physical_vs_effective_coupling_v1/coupling_comparison/plot_physical_vs_M2.py
 M campaigns/physical_vs_effective_coupling_v1/logs/run_all_probes.py
 M campaigns/physical_vs_effective_coupling_v1/m2_study/m2_variation.csv
 M campaigns/physical_vs_effective_coupling_v1/m2_study/m2_variation_finegrid_tanbeta10_illustrative.csv
 M campaigns/physical_vs_effective_coupling_v1/m2_study/m2_variation_moderate_tanbeta_illustrative.csv
 M campaigns/physical_vs_effective_coupling_v1/m2_study/m2_variation_summary.md
 M campaigns/physical_vs_effective_coupling_v1/m2_study/sensitivity_probes.csv
 M state/CURRENT_CAMPAIGN.yaml
?? campaigns/20261006_honly_production_pilot/
?? campaigns/20261006_y2_zero_directed_search/
?? campaigns/20261007_positive_g_envelope/
?? campaigns/physical_vs_effective_coupling_v1/2hdmc_build/CalcGen.d
?? campaigns/physical_vs_effective_coupling_v1/2hdmc_build/CalcLH.d
?? campaigns/physical_vs_effective_coupling_v1/2hdmc_build/M2IdentityProbe
?? campaigns/physical_vs_effective_coupling_v1/2hdmc_build/lib/Constraints.d
?? campaigns/physical_vs_effective_coupling_v1/2hdmc_build/lib/DecayTable.d
?? campaigns/physical_vs_effective_coupling_v1/2hdmc_build/lib/SM.d
?? campaigns/physical_vs_effective_coupling_v1/2hdmc_build/lib/THDM.d
?? campaigns/physical_vs_effective_coupling_v1/2hdmc_build/lib/Util.d
?? campaigns/physical_vs_effective_coupling_v1/2hdmc_build/src/M2IdentityProbe.cpp
?? campaigns/physical_vs_effective_coupling_v1/SOURCE_LEVEL_HPHIPHI_DERIVATION.md
?? campaigns/physical_vs_effective_coupling_v1/source_level_coupling_audit/
?? campaigns/physical_vs_effective_coupling_v1/validation/M2IdentityProbe.cpp
?? campaigns/physical_vs_effective_coupling_v1/validation/MASS_RECONSTRUCTION_FIX.md
?? campaigns/physical_vs_effective_coupling_v1/validation/PI_M2_IDENTITY_VALIDATION.md
?? campaigns/physical_vs_effective_coupling_v1/validation/SOL_BIAS_AUDIT.md
?? campaigns/physical_vs_effective_coupling_v1/validation/SOL_BIAS_AUDIT_RESPONSE.md
?? campaigns/physical_vs_effective_coupling_v1/validation/SOL_FINAL_RESPONSE_2.md
?? campaigns/physical_vs_effective_coupling_v1/validation/SOL_FINAL_REVIEW_2.md
?? campaigns/physical_vs_effective_coupling_v1/validation/SOL_HIGH_DISAGREEMENTS.md
?? campaigns/physical_vs_effective_coupling_v1/validation/SOL_HIGH_FINAL_SOURCE_AUDIT.md
?? campaigns/physical_vs_effective_coupling_v1/validation/SOL_HIGH_INDEPENDENT_ALGEBRA.md
?? campaigns/physical_vs_effective_coupling_v1/validation/SOL_HIGH_INDEPENDENT_NUMERICS.csv
?? campaigns/physical_vs_effective_coupling_v1/validation/SOL_PI_M2_REVIEW_AND_RESPONSE.md
?? campaigns/physical_vs_effective_coupling_v1/validation/StarRelationProbe.cpp
?? campaigns/physical_vs_effective_coupling_v1/validation/Y3SignProbe.cpp
?? campaigns/physical_vs_effective_coupling_v1/validation/pi_m2_identity_tests.csv
?? campaigns/physical_vs_effective_coupling_v1/validation/pi_m2_identity_tests_raw.csv
?? campaigns/physical_vs_effective_coupling_v1/validation/run_pi_m2_identity_tests.sh
?? campaigns/physical_vs_effective_coupling_v1/validation/sol_high_probe.cpp
?? campaigns/physical_vs_effective_coupling_v1/validation/symbolic_step_tests.txt
?? py.py
```

### dihiggs_llp_recast

Rama: `main`

HEAD: `72b8638671b788c35260491c06b3ab406775b5ae`

```text

```

### dihiggs_ufo

Rama: `main`

HEAD: `7dd02c14e2314f9d172a0782d7860826a52600d6`

```text
D CURRENT_PACK_A
 D PACK_AA_PRESENTATION_EVIDENCE.zip
?? LLscalar_v3_UFO.zip
?? LLscalar_v3_UFO_external_GHphiphi/
?? LLscalar_v3_UFO_original/
?? releases/pack_b/candidates/H2scan_mH150_tb300000_MODEL_DERIVED/MASS_RECONSTRUCTION_CONTAMINATION_WARNING.md
```

### recast_viewer

Rama: `main`

HEAD: `19c18ee336c0299deec5e2bd381fa02f68a1d836`

```text

```
