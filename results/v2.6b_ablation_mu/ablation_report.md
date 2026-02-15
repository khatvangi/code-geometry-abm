# v2.6b ablation A (mu only)

- n_seed_runs: 60
- varying_dims: ['mu_membership_reward']
- regime_counts: {'MIXED': 60}
- capture_threshold=none

## Medians
 mu_membership_reward  n_runs  n_capture  n_mixed  median_exit_rate  median_top5_share  median_enforcer_share
                  0.0      10          0       10          0.297143           0.782316               0.967563
                  0.1      10          0       10          0.310000           0.766694               0.969147
                  0.2      10          0       10          0.300000           0.776082               0.968278
                  0.3      10          0       10          0.301429           0.782591               0.970576
                  0.4      10          0       10          0.301429           0.775984               0.969916
                  0.5      10          0       10          0.295714           0.773705               0.970138
