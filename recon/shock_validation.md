# Shock Factorial Validation

## Run selection

The first available seed in both arms is seed 1.

- Primary cell: `eta_delta_drift=0.30`, `delta0=0.1`, `sigma=0.95`, `pi_reward=0.25`
  - shock_off run: `/storage/kiran-stuff/code-geometry-abm/recon/factorial_shock_off/eta_0.30/delta0_0.10/sigma_0.95/pi_0.25/seed_01`
  - shock_on run: `/storage/kiran-stuff/code-geometry-abm/recon/factorial_shock_on/eta_0.30/delta0_0.10/sigma_0.95/pi_0.25/seed_01`
- Cross-check cell: `eta_delta_drift=0.10`, `delta0=0.2`, `sigma=0.75`, `pi_reward=0.50`
  - shock_off run: `/storage/kiran-stuff/code-geometry-abm/recon/factorial_shock_off/eta_0.10/delta0_0.20/sigma_0.75/pi_0.50/seed_01`
  - shock_on run: `/storage/kiran-stuff/code-geometry-abm/recon/factorial_shock_on/eta_0.10/delta0_0.20/sigma_0.75/pi_0.50/seed_01`

## 1. metrics.csv columns

Both arms have the same columns:

```text
t, mean_x, mean_y, mean_x_all, mean_y_all, mean_L, y0, mean_epc, mean_r, mean_b, fund_prevalence, mean_epc_all, mean_r_all, mean_b_all, fund_prevalence_all, punish_rate, mean_punished, exit_rate, mean_exit_intent, exit_attempt_rate, exit_success_rate, p_opp_mean, stay_value, mean_degree_active, threat, A, budget, enforcer_frac, n_cadre_fallback, cap_mean, cap_p90, service_mean, service_p90, monopoly_on, enforcer_punish_share_step, alpha_punish_revalue, delta_outside_degrade, mu_membership_reward, current_delta, eta_delta_drift, punish_floor, punish_intensity_step, pi_reward, lam_punish
```

The requested fields are:

- Step/tick: `t`
- Shock-affected threat variable: `threat`
- Current delta: `current_delta`

## 2. Shock plumbing check: primary cell

Threat values:

| t | shock_off | shock_on |
|---:|---:|---:|
| 98 | 0 | 0 |
| 99 | 0 | 0 |
| 100 | 0 | 0 |
| 101 | 0 | 0.1 |
| 102 | 0 | 0.097 |
| 218 | 0 | 0.0028333022672758926 |
| 219 | 0 | 0.0027483031992576157 |
| 220 | 0 | 0.0026658541032798873 |
| 221 | 0 | 0.1026658541032799 |
| 222 | 0 | 0.09958587848018149 |
| 318 | 0 | 0.0053491434948933 |
| 319 | 0 | 0.005188669190046501 |
| 320 | 0 | 0.005033009114345106 |
| 321 | 0 | 0.10503300911434511 |
| 322 | 0 | 0.10188201884091476 |

The scheduled shocks are visible in `shock_on` as +0.1 jumps on the next recorded trajectory row: 100→101, 220→221, and 320→321. This indicates that the metric row labelled `t` contains the threat state before the shock scheduled at that step, or equivalently that the shock becomes visible in the `t+1` row. The subsequent values decay by a factor of 0.97 per step.

The `shock_off` threat is exactly zero throughout every inspected window. It has no jump at the scheduled shocks or on the following logged rows. **Yes: the shock_off arm actually ran shock-free. The `--shock-schedule ""` plumbing did not fail.**

## 3. Delta saturation timing: primary shock_off run

- First step with `current_delta >= 0.99`: **t=58**, value **0.99127998906337**
- t=50: **0.9258811299999999**
- t=80: **0.9999965906317696**
- t=100: **0.9999999972795878**
- t=150: **0.9999999999999999**

Delta therefore saturates before the first shock: it crosses 0.99 at t=58 and is effectively 1.0 by t=80. By itself, this explains why shocks beginning at step 100 cannot change a delta-mediated final outcome in this run.

## 4. Second-cell cross-check

Requested threat values at the scheduled step labels:

| t | shock_off | shock_on |
|---:|---:|---:|
| 100 | 0 | 0 |
| 220 | 0 | 0.0026658541032798873 |
| 320 | 0 | 0.005033009114345106 |

As in the primary cell, the schedule's +0.1 impulses appear on the next recorded rows in `shock_on`: t=101 is 0.1, t=221 is 0.1026658541032799, and t=321 is 0.10503300911434511. The corresponding `shock_off` values are zero at all those next rows as well. This independently confirms that shock_on receives shocks and shock_off does not.

## Conclusion

- (a) Was shock_off genuinely shock-free? **YES.**
- (b) Does delta saturate before the first shock? **YES** for the requested primary run (`current_delta >= 0.99` first at t=58).
- (c) Is the factorial's "shocks add zero capture" conclusion valid? **VALID.** The arms are genuinely different in shock exposure, so the zero effect is not an empty-schedule plumbing artifact. For this capture-region run, early delta saturation supplies a direct mechanism for the zero endpoint effect. The result should be interpreted as zero added capture under this factorial's timing and parameterization, not as proof that shocks can never matter under schedules occurring before delta saturation.

VALIDATION DONE
