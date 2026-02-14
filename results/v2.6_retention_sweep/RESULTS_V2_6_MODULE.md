# RESULTS_V2_6_MODULE

## Task 9 Validation
- check1_v2.5_recovery_bitwise: True
- check2_alpha_lowers_exit: True
- check3_delta_lowers_exit: True
- validation_all_pass: True

## Task 10 Retention Sweep
- n_cells: 144
- n_runs: 720
- regime_majority_counts: {'MIXED': 128, 'QUIET': 16}
- seed_regime_counts: {'MIXED': 638, 'QUIET': 80, 'CAPTURE': 2}
- capture_majority_cells (alpha>=0.4 or delta>=0.4): 0
- capture_majority_cells_with_>=70pct_seed_consensus: 0
- capture_seed_runs: 2

### Nearest Capture Cells (by exit rate)
 sigma  pi_reward  alpha  delta  n_seeds regime_majority  n_collapse  n_capture  n_mixed  n_quiet  median_fund_prevalence  median_exit_rate  median_top5_share  median_max_punish  median_enforcer_punish_share
  0.25       0.05    0.2    0.6        5           QUIET           0          0        0        5                     0.0          0.037143           0.673325           0.048571                      0.687021
  0.25       0.05    0.0    0.6        5           QUIET           0          0        0        5                     0.0          0.040000           0.674213           0.048571                      0.700553
  0.25       0.05    0.0    0.4        5           QUIET           0          0        0        5                     0.0          0.045714           0.671176           0.048571                      0.700042
  0.25       0.05    0.4    0.6        5           QUIET           0          0        0        5                     0.0          0.048571           0.674641           0.048571                      0.703508
  0.25       0.05    0.2    0.4        5           QUIET           0          0        0        5                     0.0          0.051429           0.640824           0.048571                      0.657973
  0.25       0.05    0.6    0.6        5           QUIET           0          0        0        5                     0.0          0.051429           0.685665           0.048571                      0.701605
  0.25       0.05    0.6    0.2        5           QUIET           0          0        0        5                     0.0          0.054286           0.623077           0.048571                      0.639975
  0.25       0.05    0.0    0.2        5           QUIET           0          0        0        5                     0.0          0.062857           0.656397           0.048571                      0.680951
  0.25       0.05    0.4    0.4        5           QUIET           0          0        0        5                     0.0          0.062857           0.686526           0.048571                      0.687649
  0.25       0.05    0.6    0.4        5           QUIET           0          0        0        5                     0.0          0.062857           0.678193           0.048571                      0.707963

## Task 11 Ablations
- alpha_only_total_capture_seed_runs: 0
- delta_only_total_capture_seed_runs: 9
- strongest_delta_only: delta=0.8, n_capture=9/10, median_exit=0.172857
- strongest_alpha_only: alpha=0.8, n_capture=0/10, median_exit=0.295714
- v25_recovery_changed_labels (ablation C vs v2.5 reference schema): 8/45

## Success Criteria
- criterion_1_v25_recovery: True
- criterion_2_capture_robust_>=15_cells_70pct_consensus: False
- criterion_3_concentration_preserved_in_capture_cells: False
- criterion_4_ablation_causal_signal: True

Capture was not robust in the 144-cell sweep under capture_exit_cap=0.20. This is reported as a negative result without threshold retuning.
