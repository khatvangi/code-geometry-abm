# Completed shock factorial analysis

## Setup and validation

The analysis loaded both CSVs with pandas after adding the repository root to `sys.path`, and imported the canonical functions with:

```python
from src.regime_classifier import classify_dataframe, classify
```

Each arm was classified with `classify_dataframe(df, schema="hierarchical", exit_col="final_exit_rate", punish_col="max_punish", enforcer_col="enforcer_punish_share")`. The imported `classify` function was not reimplemented or replaced by an inline rule.

| Arm | Rows | Unique `(eta, delta0, sigma, pi_reward)` cells | Seeds per cell |
|---|---:|---:|---:|
| shock_off | 4,050 | 135 | 30 |
| shock_on | 4,050 | 135 | 30 |

Full column list (the two files have the same schema):

```text
['eta_delta_drift', 'delta0', 'sigma', 'pi_reward', 'alpha',
 'mu_membership_reward', 'seed', 'final_fund_prevalence',
 'final_exit_rate', 'max_punish', 'top5_punishment_share',
 'top10_punishment_share', 'enforcer_punish_share',
 'final_current_delta', 'regime', 'run_dir']
```

The actual parameter/metric names are:

- Drift parameter (`eta`): `eta_delta_drift`
- Initial delta (`delta0`): `delta0`
- Final delta: `final_current_delta`

The grid is `eta_delta_drift = {0, 0.05, 0.10, 0.20, 0.30}`, `delta0 = {0.1, 0.2, 0.3}`, `sigma = {0.25, 0.75, 0.95}`, and `pi_reward = {0.05, 0.25, 0.50}`.

## Analysis 1: overall hierarchical-regime counts

| Subset | Arm | CAPTURE | MIXED | QUIET | COLLAPSE | Total |
|---|---|---:|---:|---:|---:|---:|
| Full | shock_off | 2,880 | 720 | 450 | 0 | 4,050 |
| Full | shock_on | 2,880 | 720 | 450 | 0 | 4,050 |
| Drift on (`eta_delta_drift > 0`) | shock_off | 2,880 | 0 | 360 | 0 | 3,240 |
| Drift on (`eta_delta_drift > 0`) | shock_on | 2,880 | 0 | 360 | 0 | 3,240 |
| Drift off (`eta_delta_drift == 0`) | shock_off | 0 | 720 | 90 | 0 | 810 |
| Drift off (`eta_delta_drift == 0`) | shock_on | 0 | 720 | 90 | 0 | 810 |

The regime counts are identical across shock arms. Capture occurs only when delta drift is enabled; all drift-off runs are MIXED or QUIET.

## Analysis 2: capture map

A cell is one unique `(eta_delta_drift, delta0, sigma, pi_reward)` tuple. Its capture rate is the fraction of its 30 seeds labeled CAPTURE. All observed cell rates are exactly either 0 or 1; there are no borderline majority cells.

| Cell category (majority threshold = 0.5) | Count |
|---|---:|
| Endogenous region: shock_off capture rate >= 0.5 | 96 |
| Shock-driven expansion: shock_on >= 0.5 and shock_off < 0.5 | 0 |
| Robust: both arms >= 0.5 | 96 |
| Never: neither arm >= 0.5 | 39 |
| shock_off only | 0 |

Majority-capture totals are 96 cells under shock_off and 96 under shock_on. The shock contribution is therefore **0 cells**.

### Endogenous-region cell list

The complete list of 96 endogenous cells can be stated exactly and compactly as the following Cartesian product:

- `eta_delta_drift` is any of `{0.05, 0.10, 0.20, 0.30}`;
- `delta0` is any of `{0.1, 0.2, 0.3}`; and
- `(sigma, pi_reward)` is any of `{(0.25, 0.25), (0.25, 0.50), (0.75, 0.05), (0.75, 0.25), (0.75, 0.50), (0.95, 0.05), (0.95, 0.25), (0.95, 0.50)}`.

Every one of these cells has capture rate 1.000 in both arms. Thus the endogenous region covers every positive eta and every delta0, and it clusters in either moderate/high sigma (`0.75` or `0.95`) at every reward level, or low sigma (`0.25`) when reward is `0.25` or `0.50`. The sole excluded `(sigma, pi_reward)` combination within the positive-eta region is `(0.25, 0.05)`.

There are no shock-driven expansion cells to list or locate. The 39 never-capture cells consist of all 27 drift-off cells plus the 12 positive-eta cells with `(sigma, pi_reward) = (0.25, 0.05)` (four positive eta values times three delta0 values).

## Analysis 3: seed-level uncertainty

Wilson score intervals use a two-sided 95% confidence level.

| Arm | CAPTURE seeds | Total seeds | Rate | Wilson 95% CI |
|---|---:|---:|---:|---:|
| shock_off | 2,880 | 4,050 | 71.11% | [69.70%, 72.49%] |
| shock_on | 2,880 | 4,050 | 71.11% | [69.70%, 72.49%] |

Every cell has a shock_on-minus-shock_off capture-rate gap of exactly 0.000, so there is no unique set of five “largest” gaps. The table reports the first five cells in lexicographic coordinate order among the 135-way tie.

| eta | delta0 | sigma | pi_reward | Off rate (95% Wilson CI) | On rate (95% Wilson CI) | Gap |
|---:|---:|---:|---:|---:|---:|---:|
| 0.00 | 0.1 | 0.25 | 0.05 | 0.000 [0.000, 0.114] | 0.000 [0.000, 0.114] | 0.000 |
| 0.00 | 0.1 | 0.25 | 0.25 | 0.000 [0.000, 0.114] | 0.000 [0.000, 0.114] | 0.000 |
| 0.00 | 0.1 | 0.25 | 0.50 | 0.000 [0.000, 0.114] | 0.000 [0.000, 0.114] | 0.000 |
| 0.00 | 0.1 | 0.75 | 0.05 | 0.000 [0.000, 0.114] | 0.000 [0.000, 0.114] | 0.000 |
| 0.00 | 0.1 | 0.75 | 0.25 | 0.000 [0.000, 0.114] | 0.000 [0.000, 0.114] | 0.000 |

## Analysis 4: delta saturation check

| Arm | CAPTURE runs | Final delta p10 | Final delta median | Final delta p90 | Median enforcer punishment share | Final delta >= 0.99 |
|---|---:|---:|---:|---:|---:|---:|
| shock_off | 2,880 | 0.9999999991 | 1.0000000000 | 1.0000000000 | 0.981486 | 100.0% |
| shock_on | 2,880 | 0.9999999991 | 1.0000000000 | 1.0000000000 | 0.981493 | 100.0% |

Final delta is unambiguously pinned at or extremely near 1.0 in CAPTURE runs: every CAPTURE run has `final_current_delta >= 0.99`, and even the 10th percentile is above 0.999999999. The simultaneous median enforcer punishment share of about 0.9815 is consistent with final delta being mechanically driven by concentrated enforcer punishment. This saturation is a strong circularity signal: the classifier uses enforcer share while the endogenous delta state appears to be driven to its ceiling alongside that same quantity. The descriptive check supports the reviewers' concern, although it does not alone establish causal direction; that would require inspecting or intervening on the delta update rule.

## BOTTOM LINE

Capture is fully endogenous in this factorial: without shocks, 2,880 of 4,050 seeds (71.11%) and 96 of 135 cells show capture. Shocks add no capture at all—the seed counts, regime counts, per-cell rates, and 96-cell majority-capture map are identical in the two arms. The endogenous region requires positive eta, spans every tested initial delta, and covers all moderate/high-sigma cells plus low-sigma cells when reward is not at its minimum. No drift-off cell captures, and the only positive-eta non-capture strip is low sigma paired with minimum reward. All 96 endogenous majority-capture cells are robust across both arms, while 39 cells never majority-capture. In CAPTURE runs, final delta is effectively saturated at 1.0 in both arms and median enforcer punishment share is about 0.9815. That near-perfect co-saturation strongly supports the reviewers' delta-circularity concern, while remaining a diagnostic association rather than by itself proving the update mechanism's causal direction.

ANALYSIS DONE
