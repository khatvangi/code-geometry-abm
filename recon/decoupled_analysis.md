# Decoupled-delta factorial analysis

## Method

The four `sweep_seed_results.csv` files were loaded after adding the repository root to `sys.path`. Each was reclassified with `src.regime_classifier.classify_dataframe(df, schema="hierarchical", exit_col="final_exit_rate", punish_col="max_punish", enforcer_col="enforcer_punish_share")`; the pre-existing `regime` field was not used. The drift column in all four files is `eta_delta_drift`, and drift-on means `eta_delta_drift > 0`. Each arm contains 4,050 runs; 3,240 are drift-on. Drift-on cell rates use the 108 unique `(eta_delta_drift, delta0, sigma, pi_reward)` cells (30 seeds per cell). Wilson intervals below are two-sided 95% intervals.

## Capture comparison

| arm | drift-on CAPTURE / runs | drift-on rate | Wilson 95% CI | full-grid CAPTURE / runs | full-grid rate |
|---|---:|---:|---:|---:|---:|
| legacy | 2,880 / 3,240 | 88.89% | 87.76%-89.93% | 2,880 / 4,050 | 71.11% |
| k1.5 | 0 / 3,240 | 0.00% | 0.00%-0.12% | 0 / 4,050 | 0.00% |
| k3.0 | 0 / 3,240 | 0.00% | 0.00%-0.12% | 0 / 4,050 | 0.00% |
| k6.0 | 0 / 3,240 | 0.00% | 0.00%-0.12% | 0 / 4,050 | 0.00% |

## Emergence test: distribution of drift-on cell capture rates

| arm | cells at exactly 0 | strictly intermediate cells | cells at exactly 1 | intermediate share | assessment |
|---|---:|---:|---:|---:|---|
| legacy | 12 | 0 | 96 | 0 / 108 (0.0%) | degenerate, mostly one |
| k1.5 | 108 | 0 | 0 | 0 / 108 (0.0%) | degenerate, all zero |
| k3.0 | 108 | 0 | 0 | 0 / 108 (0.0%) | degenerate, all zero |
| k6.0 | 108 | 0 | 0 | 0 / 108 (0.0%) | degenerate, all zero |

Small histogram (cell counts):

| arm | `=0` | `(0,0.2]` | `(0.2,0.4]` | `(0.4,0.6]` | `(0.6,0.8]` | `(0.8,1)` | `=1` |
|---|---:|---:|---:|---:|---:|---:|---:|
| legacy | 12 | 0 | 0 | 0 | 0 | 0 | 96 |
| k1.5 | 108 | 0 | 0 | 0 | 0 | 0 | 0 |
| k3.0 | 108 | 0 | 0 | 0 | 0 | 0 | 0 |
| k6.0 | 108 | 0 | 0 | 0 | 0 | 0 | 0 |

The histogram isolates exact zero and exact one, with intermediate intervals left-open and right-closed except `(0.8,1)`, which excludes one. The legacy result reproduces the supplied 960/1,080-cell-equivalent pattern: 96 of 108 drift-on cells are always CAPTURE and 12 are never CAPTURE. De-circularization does not turn this into graded, seed-sensitive emergence; it moves every cell to the zero endpoint. Thus every arm remains degenerate, although the decoupled degeneracy is uniformly no capture rather than mostly certain capture.

## Terminal delta among CAPTURE runs

The terminal-delta column is `final_current_delta`.

| arm | median `final_current_delta` among CAPTURE runs |
|---|---:|
| legacy | 1.0000 |
| k1.5 | N/A (no CAPTURE runs) |
| k3.0 | N/A (no CAPTURE runs) |
| k6.0 | N/A (no CAPTURE runs) |

Consequently, the requested claim that median terminal delta is below 1.0 among decoupled CAPTURE runs cannot be confirmed: there are no such runs under the canonical classifier. The legacy median is approximately 1.0 as expected (and its drift-on CAPTURE values range from 0.9989 to 1.0). As a diagnostic, drift-on regime counts in each decoupled arm are 2,880 MIXED and 360 QUIET; none are CAPTURE. Only 360 drift-on runs per decoupled arm satisfy the classifier's retention condition (`final_exit_rate <= 0.20`), while 2,880 satisfy active punishment, and no run satisfies all three CAPTURE conditions simultaneously. This indicates that the decoupled runs chiefly lose CAPTURE because they do not retain enough members, not because the canonical reclassification was skipped.

## k3.0 capture map

There are **no** `(sigma, pi_reward)` cells with drift-on capture rate at least 0.5 after aggregation over `eta_delta_drift` and `delta0`. All nine combinations have rate 0/360 = 0.0:

| sigma | pi_reward values with capture rate >= 0.5 |
|---:|---|
| 0.25 | none |
| 0.75 | none |
| 0.95 | none |

Surviving capture therefore does not concentrate anywhere in sigma-pi space at k3.0; it is absent across the complete 3-by-3 map.

## Bottom line

Under the canonical hierarchical classifier, no capture survives de-circularization in any of the 12,150 drift-on decoupled runs. Each kappa arm has a point estimate of 0%, and its Wilson upper bound is only 0.12%, compared with 88.89% capture in the legacy drift-on runs. Within the tested values, capture is therefore not detectably sensitive to kappa: k1.5, k3.0, and k6.0 all give the same zero result. De-circularization also does not reveal graded stochastic emergence, because none of the 324 decoupled drift-on parameter cells has an intermediate seed-level capture rate. Instead, every decoupled cell is degenerate at zero, whereas legacy is degenerate mostly at one. At k3.0 there is no surviving sigma-pi region, including the highest sigma or reward settings. The absence of decoupled CAPTURE runs makes their median terminal delta undefined, while legacy CAPTURE remains pinned near delta = 1.0. These results do not support a real emergent-capture claim from the decoupled mechanism as currently parameterized. Unless another independently justified endogenous mechanism restores capture and produces graded cell-level probabilities, the paper should treat delta as exogenous and describe the legacy capture result as dependent on the circular delta feedback.

DECOUPLED ANALYSIS DONE
