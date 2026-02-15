# v2.6b ablation C (mu-delta interaction)

- n_seed_runs: 60
- varying_dims: ['mu_membership_reward', 'delta']
- regime_counts: {'MIXED': 60}
- capture_threshold=none

## Medians
 mu_membership_reward  delta  n_runs  n_capture  n_mixed  median_exit_rate  median_top5_share  median_enforcer_share
                  0.2    0.3      10          0       10          0.280000           0.759899               0.972774
                  0.2    0.4      10          0       10          0.272857           0.753538               0.973195
                  0.2    0.5      10          0       10          0.255714           0.749668               0.974732
                  0.3    0.3      10          0       10          0.282857           0.767340               0.970794
                  0.3    0.4      10          0       10          0.278571           0.761951               0.971635
                  0.3    0.5      10          0       10          0.271429           0.756277               0.974630
