# RESULTS_V2_6_DELTA_THRESHOLD

- n_cells: 24
- n_runs: 240
- regime_majority_counts: {'MIXED': 18, 'CAPTURE': 6}
- seed_regime_counts: {'MIXED': 175, 'CAPTURE': 65}

## Threshold Summary
 delta  n_cells  majority_capture_cells  consensus70_capture_cells  capture_seed_runs  seed_runs_total  median_exit_rate_mean  median_exit_rate_min  median_exit_rate_max
   0.0        4                       0                          0                  0               40               0.342500              0.297143              0.384286
   0.4        4                       0                          0                  0               40               0.324643              0.280000              0.364286
   0.6        4                       0                          0                  0               40               0.292857              0.241429              0.335714
   0.7        4                       0                          0                  5               40               0.261786              0.220000              0.298571
   0.8        4                       2                          2                 20               40               0.209286              0.172857              0.247143
   0.9        4                       4                          4                 40               40               0.125000              0.095714              0.165714

## Checks
- capture_absent_for_delta<=0.6: True
- consensus70_capture_cells_for_delta>=0.7: 6
- consensus70_capture_cells_for_delta>=0.8: 6

## Capture Majority Cells
 delta  sigma  pi_reward  n_capture  median_exit_rate  median_fund_prevalence  median_max_punish  median_top5_share  median_enforcer_punish_share
   0.8   0.95       0.25         10          0.172857                0.119850           0.154286           0.734339                      0.979129
   0.8   0.95       0.50          9          0.172857                0.119594           0.148571           0.737495                      0.979359
   0.9   0.75       0.25         10          0.165714                0.119432           0.180000           0.721348                      0.982530
   0.9   0.75       0.50         10          0.141429                0.119988           0.181429           0.715659                      0.981084
   0.9   0.95       0.25         10          0.097143                0.112683           0.154286           0.715696                      0.979693
   0.9   0.95       0.50         10          0.095714                0.113959           0.155714           0.718395                      0.980158
