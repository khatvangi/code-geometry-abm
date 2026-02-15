# RESULTS_V2_6B_MEMBERSHIP

## Task 13 Validation (`v2.6b`)
- `mu=0, alpha=0, delta=0` recovers `v2.5` on shared outputs: **PASS**.
- Validation report: `results/v2.6b_validation/validation_report.json`.
- `all_pass=true`.

Key values (5-seed sanity check, `sigma=0.95, pi=0.50`):
- Baseline median exit: `0.2971`
- `mu=0.5` median exit: `0.2943` (lower)
- Top-5 punishment share stable (`0.7828` -> `0.7864`)
- Enforcer punishment share stable (`0.9674` -> `0.9713`)

## Task 14 Carrot-and-Stick Sweep (600 runs)
- Root: `results/v2.6b_membership_sweep/`
- Grid: `mu={0.0,0.1,0.2,0.3,0.4}`, `delta={0.0,0.3,0.6}`, `sigma={0.75,0.95}`, `pi={0.25,0.50}`, `10` seeds/cell.

Majority regimes (60 cells):
- `MIXED=60`
- `CAPTURE=0`
- `COLLAPSE=0`
- `QUIET=0`

Seed-level regimes (600 runs):
- `MIXED=594`
- `CAPTURE=6`

Sweep diagnostics:
- `exit_rate` median range: `0.2386..0.3886`
- `max_punish` median range: `0.1257..0.1714`
- `enforcer_punish_share` median range: `0.9511..0.9768`

Synergy check (from `synergy_summary.csv`):
- `synergy_capture70_count=0`
- `moderate_synergy_capture70_count=0`
- `interaction_exit_median=0.00143` (near-additive/negligible)

Conclusion: in this grid, `mu x delta` does **not** create robust capture.

## Task 15 Ablations (`sigma=0.95`, `pi=0.50`, 10 seeds/value)

### A) `mu` alone (`delta=0`)
- Root: `results/v2.6b_ablation_mu/`
- Capture: **none** across `mu in {0.0,0.1,0.2,0.3,0.4,0.5}`.
- Exit median remains around `0.296..0.310`.

### B) `delta` alone (`mu=0`)
- Root: `results/v2.6b_ablation_delta/`
- `delta=0.7`: `2/10` capture seeds.
- `delta=0.8`: `9/10` capture seeds (robust at seed level).
- Exit median drops from `0.2971` (`delta=0`) to `0.1729` (`delta=0.8`).

### C) Interaction (`mu in {0.2,0.3}`, `delta in {0.3,0.4,0.5}`)
- Root: `results/v2.6b_ablation_interaction/`
- Capture: **none** in all tested cells.
- Exit reduced to `~0.256..0.283`, but not below capture threshold (`<=0.20`).

## Overall Interpretation
- `mu_membership_reward` is weak/inert over tested range (`<=0.5`) for regime transition.
- `delta_outside_degrade` is the active retention lever with a sharp threshold near `delta ~ 0.8` in this setup.
- Enforcement concentration remains high throughout (`top5 ~0.74..0.78`, enforcer share `~0.97+`) and is not disrupted.
- Robust capture still requires strong outside-degradation; moderate `mu + delta` did not produce the hypothesized synergy.
