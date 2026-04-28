# INSTRUCTION_BORON_S2 — Phase S2: Argument-template envelope as input to the ABM

**Phase:** Synthesis Phase S2 — ABM Extension 1 (argument-template input vector)
**Author:** Kiran Boggavarapu
**Date:** 2026-04-28
**Status:** Planning artifact. No code yet. Implementation begins on Kiran's go-ahead.
**Read prerequisites:** `SYNTHESIS_WORKING_DOC.md` (revised post-S1), `synthesis/unified_christian_baseline_v1/synthesis_findings.md`, `synthesis/inputs/from_nitrogen/argument_templates.json`, `CLAUDE.md` at repo root.

---

## §1 Goal

Phase S2 implements Extension 1 from `SYNTHESIS_WORKING_DOC.md §5`: argument-template distribution becomes an input to the ABM. Each of the eight templates (T1–T8) carries a theoretically-derived envelope of (σ_max, π_max, base_opp_floor, exit_cost_baseline) describing which regions of the geometry parameter space that template makes structurally available. The modeler then sets concrete σ × π × base_opp × exit_cost values within that envelope to represent a specific historical regime.

The phase tests one substantive claim: **template structure constrains which σ × π regions are reachable, and the ABM dynamics within each envelope produce regime distributions consistent with the templates' theoretical intent.** Specifically:

- Templates whose structural-variable signature includes E (enforcement directive) and M (mandate) — T3, T4, T5 — should produce predominantly mixed and capture regimes within their high-π envelope.
- Templates dominated by P (pluralistic restraint) — T6, T7 — should cap π_max low and produce predominantly quiet regimes regardless of where in the envelope the modeler samples.
- Templates with C/A but no E (T1, T2) should produce mixed regimes when σ is high but capture only when combined with active enforcement structure (which their isolated envelope does not provide).
- T8 should produce mixed-but-not-capture as the asymmetric-modern-rights-borrowing template's modern-restraint overlay caps π enforcement.

If any of these qualitative predictions is violated systematically across seeds, the envelope mapping is wrong and §3 needs revision.

## §2 Decisions inherited from Phase S1

- **Q1 resolved (theoretical derivation).** No empirical calibration of envelopes from the 16-case corpus. Template usage is too skewed (T2 has 0 cases, T1/T6/T8 each ≤1) for corpus calibration to be defensible. The corpus serves as consistency check post-sweep, not primary calibration.
- **Active-rate-at-sweep-time mandatory.** No post-hoc `reclassify_regimes.py` step. The v3.0 model writes `active_punish_rate = punish_rate / max(1 − exit_rate, ε)` directly to `metrics.csv` per timestep, and regime classification reads `active_punish_rate` natively.
- **Append-only model versioning.** New work goes in `src/religion_fundamentalism_abm_v3_0.py`. v2.5–v2.9 are frozen reproducibility artifacts and must not be edited.
- **Christian-only scope inherited from Nitrogen methodology.** Phase S2 sweep parameters refer to Christian templates and Christian regime cases; non-Christian comparisons defer to Paper 4 / comparative phase.

## §3 Envelope derivation — theoretical mapping from structural variables to ABM parameters

The eight templates encode their structural-variable signatures in `synthesis/inputs/from_nitrogen/argument_templates.json` as the `structural_variables` field. The variables and their ABM-parameter consequences are derived as follows.

### §3.1 Variable-to-parameter mapping

Each structural variable maps to an ABM-parameter consequence consistent with the variable's textual function:

| Variable | Function in template grammar | ABM-parameter consequence |
|---|---|---|
| C (classification / boundary) | Defines who is inside vs outside the orthodoxy | Raises σ_max — boundary creates legibility of compliance |
| A (asymmetry / authority) | Establishes non-reciprocal authority claim | Raises σ_max — authority makes orthodoxy categorically askable |
| M (mandate) | Imposes positive obligation to spread, teach, or correct | Raises π_max — mandate licenses outward enforcement |
| E (enforcement directive) | Explicitly authorizes coercion against deviation | Raises π_max directly; also raises base_opp_floor by raising in-group benefits of compliance |
| O (outsider framing) | Marks non-members as lost, condemned, or impure | Raises exit_cost_baseline — leaving means joining the condemned class |
| U (urgency / final-sorting) | Heightens stakes via apocalyptic or last-chance frame | Raises π_max temporarily; lowers patience for non-compliance |
| R (resistance handling) | Specifies response when enforcement meets pushback | Raises π_max conditional on encountering deviation |
| P (pluralistic restraint) | Explicitly caps coercion via mercy, dignity, non-retaliation | Caps σ_max AND caps π_max regardless of other variables present |

P is the only cap-imposing variable; all others raise envelope ceilings. When P appears alongside other variables (T6 "P against C, A, M, E, O, R"), the cap dominates — this is the textual claim the variable encodes.

### §3.2 Envelope formula

For each template, the four envelope parameters are computed from the structural-variable set as:

```
σ_max(template) = base_σ + Σ raise(v, σ) for v in vars(template), capped if P ∈ vars(template)
π_max(template) = base_π + Σ raise(v, π) for v in vars(template), capped if P ∈ vars(template)
base_opp_floor(template) = baseline + bonus if {O, E} ⊆ vars(template)
exit_cost_baseline(template) = baseline + bonus if O ∈ vars(template)
```

Concrete numeric specification (units match v2.5 Params dataclass). The values below reproduce §3.3 exactly; see §3.2.5 for the verification.

```
base_σ = 0.20
σ_raise = {C: 0.20, A: 0.20, M: 0.0, E: 0.0, O: 0.05, U: 0.0, R: 0.0, P_contributes: 0.0}
σ_cap_when_P_present = 0.55

base_π = 0.05
π_raise = {C: 0.05, A: 0.0, M: 0.15, E: 0.15, O: 0.0, U: 0.05, R: 0.05, P_contributes: 0.0}
π_cap_when_P_present = 0.15

base_opp_baseline = 0.30
base_opp_bonus_OE = 0.40

exit_cost_baseline_default = 0.30
exit_cost_baseline_O_bonus = 0.40

# T8-specific overrides (modern-restraint regime — see §3.2.4)
sigma_max_T8_override = 0.45
pi_max_T8_override    = 0.25
```

**Semantic rules layered on top of the additive formula:**

§3.2.1 — P-cap precedence. When P appears in the structural-variable set, σ_max and π_max are computed by the additive formula and then capped at σ_cap_when_P_present (0.55) and π_cap_when_P_present (0.15) respectively. The cap is a hard ceiling, not a floor.

§3.2.2 — P shadows E for base_opp_floor only. The base_opp_floor bonus requires both O and E to be active *and not P-shadowed*. When P is present, E is treated as neutralized for envelope-floor purposes — the regime is rhetorically committed against enforcement, so the {O,E} → "outside-option degraded by enforcement" mechanism does not apply. T6 (P against C,A,M,E,O,R) therefore has base_opp_floor = 0.30 (the baseline) rather than 0.70.

§3.2.3 — P does not shadow O for exit_cost_baseline. The O bonus for exit_cost_baseline applies whenever O is in the variable set, regardless of P. Outsider framing operates psychologically as an exit barrier even under formal restraint — softened-modern-interpretation regimes (T6) still inherit the canonical-text outsider framing as a baseline pull on members not to leave, even though they cap active enforcement. T6 therefore has exit_cost_baseline = 0.70.

§3.2.4 — T8 modern-restraint override. T8's "asymmetric modern rights borrowing" template overrides both σ_max and π_max with fixed values (0.45 and 0.25 respectively), bypassing the additive formula. This reflects the template's structural claim: the regime rhetorically restrains visible enforcement (capping σ below what its A+C+O variable set would suggest) while preserving non-trivial actual enforcement reward (raising π above what the bare formula computes). The override is a setting, not a cap-or-floor pair — T8 envelope is fixed at exactly (0.45, 0.25, 0.30, 0.70).

§3.2.5 — Verification. Applying the additive formula plus §3.2.1–§3.2.4 reproduces §3.3 exactly. T1: σ = 0.20+0.20(C)+0.20(A)+0.05(O) = 0.65; π = 0.05+0.05(C)+0.05(U) = 0.15. T3: σ = 0.20+0.20(A) = 0.40; π = 0.05+0.15(M)+0.05(U) = 0.25. T4: σ = 0.20+0.20(C)+0.05(O) = 0.45; π = 0.05+0.05(C)+0.15(M)+0.15(E)+0.05(R) = 0.45; base_opp_floor = 0.30+0.40 = 0.70 ({O,E} both present, no P). T5: σ = 0.20+0.20(A) = 0.40; π = 0.05+0.15(M)+0.15(E)+0.05(R) = 0.40. T6: pre-cap σ = 0.20+0.20(C)+0.20(A)+0.05(O) = 0.65, capped to 0.55; pre-cap π = 0.05+0.05(C)+0.15(M)+0.15(E)+0.05(R) = 0.45, capped to 0.15; base_opp_floor: {O,E} present but P shadows E → no bonus → 0.30; exit_cost_baseline: O present (P does not shadow) → 0.70. T7: σ = 0.20; π = 0.05; both below P-caps so caps are inert. T8: overridden to (0.45, 0.25). All eight rows reproduced.

### §3.3 Resulting envelope per template

Applying §3.1–§3.2 to the eight templates in `argument_templates.json`:

| Template | structural_variables | σ_max | π_max | base_opp_floor | exit_cost_baseline |
|---|---|---|---|---|---|
| T1 exclusive_salvation | C, A, O, U | 0.65 | 0.15 | 0.30 | 0.70 |
| T2 final_sorting | C, A, U, O | 0.65 | 0.15 | 0.30 | 0.70 |
| T3 expansion_mandate | M, U, A | 0.40 | 0.25 | 0.30 | 0.30 |
| T4 purification | C, M, E, O, R | 0.45 | 0.45 | 0.70 | 0.70 |
| T5 sacred_enforcement | M, E, R, A | 0.40 | 0.40 | 0.30 | 0.30 |
| T6 softened_modern (P caps) | P against C, A, M, E, O, R | 0.55 | 0.15 | 0.30 | 0.70 |
| T7 counter_reading | P only | 0.20 | 0.05 | 0.30 | 0.30 |
| T8 asymmetric_rights | A, C, O + modern restraint | 0.45 | 0.25 | 0.30 | 0.70 |

These are the ceilings of each template's envelope. The grid points within each envelope (§5) sample at low-, mid-, and high-fractions of (σ_max, π_max).

### §3.4 What this derivation does NOT do

- It does not encode template *interactions*. Real regimes activate multiple templates simultaneously (LR001 First Crusade activates T3 + T5; LR015 residential schools activate T3 + T5). Phase S2 sweeps each template in isolation; multi-template regime simulation belongs to Phase S4 (Christian regime replication).
- It does not encode the temporal dimension of U (urgency). U is treated as a steady-state π elevation rather than a time-decaying spike. This is a known simplification consistent with v2.5's steady-state design.
- It does not encode `non_textual_forces`. Forces enter as Phase S3 Extension 3 perturbations on top of the template envelope.

These limits are stated here so a reviewer cannot claim the envelope was overfit to interactions or to non-textual forces.

## §4 v3.0 implementation specification

### §4.1 File: `src/religion_fundamentalism_abm_v3_0.py`

Copy `src/religion_fundamentalism_abm_v2_5.py` to `src/religion_fundamentalism_abm_v3_0.py`. All v2.5 dynamics preserved verbatim. Three additions:

1. **Argument-template input.** `Params` gains a field `argument_template: str = "T_FREE"` where `T_FREE` means "no template, set σ/π/etc. directly as in v2.5" (preserves backward compatibility for any legacy sweep calling v3.0 in free mode). Valid template values: `T1`, `T2`, `T3`, `T4`, `T5`, `T6`, `T7`, `T8`, `T_FREE`.

2. **Envelope-derived parameters.** When `argument_template != "T_FREE"`, the model reads the envelope ceilings from a hard-coded table matching §3.3 above and validates that the user-supplied σ, π, base_opp, exit_cost values lie within the envelope. If any value exceeds its template's ceiling, raise ValueError with a clear message naming the offending parameter. Out-of-envelope sweeps are not silently allowed — that would defeat the purpose of the envelope claim.

3. **Active-rate-at-sweep-time.** `metrics.csv` gains a column `active_punish_rate` computed each timestep as `punished / max(1, N_total - n_exited)`, where `n_exited` is the count of exited agents at that timestep. The regime classifier in `agent_summary.csv` aggregation uses `active_punish_rate` directly. Raw `punish_rate` is still written for backward compatibility.

### §4.2 CLI flags added

```
--argument_template T1|T2|T3|T4|T5|T6|T7|T8|T_FREE   (default: T_FREE)
```

When `T_FREE` is selected, all existing CLI flags work as in v2.5. When a specific template is selected, the user-supplied σ/π/base_opp/exit_cost are validated against §3.3.

### §4.3 What the model does NOT do

- No new agent dynamics. The v2.5 step function, monopoly-on-enforcement logic, literalism trait, patronage, capital compounding, exit decisions — all preserved unchanged.
- No template interaction. The `argument_template` field is single-valued; no weighted mixtures yet (Phase S4 material).
- No automatic envelope-fraction sampling. The user supplies (σ, π, base_opp, exit_cost) explicitly; the model only validates against the envelope. Grid sampling is the sweep script's job.

## §5 Sweep specification

### §5.1 Grid

Per Q1's theoretical-derivation resolution, the sweep tests envelope shape rather than full 4D resolution.

**5 cells per template along a low-π → high-π diagonal within the envelope.** Each cell fixes σ at a fractional position within [0.5 × σ_max, σ_max] and π at the matching fractional position within [0.2 × π_max, π_max], with base_opp at base_opp_floor and exit_cost at exit_cost_baseline. The five fractional positions are 0.0, 0.25, 0.5, 0.75, 1.0 of the way from low-π-low-σ to high-π-high-σ.

Concrete cell list per template (grid_position, σ, π) where σ and π are computed from the envelope:

| grid | σ_fraction | π_fraction |
|---|---|---|
| 0 | 0.50 of σ_max | 0.20 of π_max |
| 1 | 0.625 | 0.40 |
| 2 | 0.75 | 0.60 |
| 3 | 0.875 | 0.80 |
| 4 | 1.00 | 1.00 |

8 templates × 5 cells × 30 seeds = **1,200 runs**. The 30 seeds are integers 1..30 to match v2.5 convention.

### §5.2 Sweep script: `scripts/run_v3_0_envelope_sweep.py`

- Reads template envelopes from a hard-coded table (sourced from §3.3 of this instruction; the table is not duplicated, it is imported from `src/religion_fundamentalism_abm_v3_0.py`).
- For each (template, grid_cell, seed), spawns a subprocess invocation of `src/religion_fundamentalism_abm_v3_0.py` with `--argument_template <T>`, `--sigma <σ>`, `--pi_reward <π>`, `--base_opp <floor>`, `--exit_cost <baseline>`, `--seed <s>`, `--steps 450`, `--n 350`, `--graph scale_free`, `--no_movie`.
- Writes per-run output to `results/v3_0_envelope_sweep/<template>/grid_<i>/seed_<s>/`.
- ThreadPoolExecutor with WORKERS=20 per the standing protocol.

### §5.3 Aggregation: `scripts/aggregate_v3_0_envelope_sweep.py`

- Walks `results/v3_0_envelope_sweep/` and produces `sweep_seed_results.csv` (1,200 rows, one per seed) and `sweep_summary.csv` (40 rows, one per template-grid cell).
- Regime classification uses `active_punish_rate` directly per §4.1 — no post-hoc reclassification.
- Computes per-template regime distribution and writes `template_regime_counts.csv`.
- Produces phase-map figure: 8 panels (one per template), σ × π grid, regime as color, mirroring the v2.5 phase-map style.

### §5.4 Wall-clock estimate

Per CLAUDE.md, v2.5 confirmatory sweep is ~4–6 hours for 360 runs on 64 cores. 1,200 runs scales linearly to ~13–20 hours. Background via `nohup`, poll via `ps aux` per the standing protocol.

## §6 Validation

### §6.1 Pre-sweep validation (must pass before launching)

1. `src/religion_fundamentalism_abm_v3_0.py` runs with `--argument_template T_FREE` and reproduces a v2.5 baseline cell bit-for-bit when the same seed and parameters are passed. (Sanity: backward compatibility.)
2. `src/religion_fundamentalism_abm_v3_0.py --argument_template T1 --sigma 0.99 --pi_reward 0.01` raises ValueError naming σ as out-of-envelope (T1's σ_max is 0.65).
3. `src/religion_fundamentalism_abm_v3_0.py --argument_template T7 --sigma 0.10 --pi_reward 0.04` runs successfully (within T7's envelope).
4. The 5-cell grid coordinates for each template are computed and printed by `scripts/run_v3_0_envelope_sweep.py --dry_run` and inspected before the real launch. The dry-run output goes in `synthesis/envelope_sweep_v1/dry_run.md`.

### §6.2 Post-sweep validation

1. **Sweep completion.** All 1,200 expected `metrics.csv` files exist and are non-empty.
2. **Active-rate sanity.** For each run, `active_punish_rate` ≥ `punish_rate` (since N_total ≥ N_total − n_exited). Spot-check 10 random runs.
3. **Qualitative envelope predictions** (per §1):
   - T3, T4, T5 high-π cells produce >50% mixed/capture across seeds.
   - T6, T7 produce >80% quiet across all cells regardless of grid position.
   - T1, T2 produce mostly mixed at high σ but rarely capture (capture requires E in their structural-variable set, which they lack).
   - T8 produces mixed at high cells but rarely capture.

   Violations of any qualitative prediction across multiple seeds are findings — they constrain §3.

## §7 Deliverables

After the sweep completes, produce in `synthesis/envelope_sweep_v1/`:

- `synthesis_findings_s2.md` — Phase S2 findings report. Same discipline as Phase S1's report: substantive vs boring-null vs formal-only-mechanism-mismatch decomposition, headline numbers, recommendations for Phase S3.
- `template_regime_counts.csv` — per-template regime distribution (40 rows: template × grid_position × regime_count).
- `envelope_predictions_summary.csv` — per-template predicted-vs-observed regime distribution.
- `mismatches_report.md` — for any template whose qualitative prediction is violated.
- `MANIFEST.md` — file inventory, pipeline diagram, hard-rule compliance checklist (matching Phase S1 style).
- `_dry_run.md` — pre-launch grid coordinate inspection.
- `phase_map_v3_0.png` — 8-panel phase map across templates.

Plus committed `results/v3_0_envelope_sweep/**` with whitelist entry added to `.gitignore`.

## §8 Hard rules (operational)

1. No file outside `src/`, `scripts/`, `synthesis/`, `results/v3_0_envelope_sweep/`, `.gitignore`, and `HISTORY.md` may be modified.
2. v2.5–v2.9 model files stay frozen. Do not edit them.
3. The S1 deliverables in `synthesis/unified_christian_baseline_v1/` are immutable per the frozen-baseline rule.
4. The PLOS submission package in `synthesis/inputs/manuscript_plosone_v3/` is immutable.
5. Manuscript files in `manuscript/` are not touched.
6. `scripts/reclassify_regimes.py` is not used in Phase S2 — active-rate computed at sweep time per §4.1.
7. No synthetic data — all values come from real ABM runs with fixed seeds.
8. Existing `results/` directories are not overwritten; the new sweep goes in a new whitelisted directory.
9. Append `HISTORY.md` Q&A entry per repo convention.
10. If during implementation Phase S2 reveals a structural problem with the §3 envelope mapping (e.g., a template's qualitative prediction is violated systematically), STOP, write the finding to `synthesis/envelope_sweep_v1/synthesis_findings_s2.md`, and ask Kiran. Do not silently retune the envelope to make the predictions match.

## §9 Sequencing within S2

Recommended order (each step gates the next):

1. **Step S2.1 — write `src/religion_fundamentalism_abm_v3_0.py`** with the §4 spec. Run §6.1 validations 1–3.
2. **Step S2.2 — write `scripts/run_v3_0_envelope_sweep.py`** and run with `--dry_run`. Inspect the printed grid coordinates against §3.3 and §5.1. Output the dry-run to `synthesis/envelope_sweep_v1/_dry_run.md`. **Stop here for Kiran's go-ahead before launching.**
3. **Step S2.3 — launch the sweep** via `nohup`. Update `HISTORY.md` with the launch entry.
4. **Step S2.4 — wait for completion** (~13–20 wall-clock hours). Poll via `ps aux` and output file count.
5. **Step S2.5 — write `scripts/aggregate_v3_0_envelope_sweep.py`** and run it. Produce the §7 deliverables.
6. **Step S2.6 — write `synthesis_findings_s2.md`** with the qualitative-prediction check (§6.2) and Phase S3 recommendation.

---

*End of Phase S2 instruction. Update upon Phase S2 completion with a "Status: COMPLETE" entry and a link to `synthesis_findings_s2.md`.*
