# v2.6 Ablation B delta-only

- n_seed_runs: 50
- varying_dims: ['delta']
- regime_counts: {'MIXED': 41, 'CAPTURE': 9}
- capture_threshold~delta=0.8

## Medians
 delta  n_runs  n_capture  median_exit_rate  median_top5_share  median_enforcer_share
   0.0      10          0          0.297143           0.782316               0.967563
   0.2      10          0          0.287143           0.761121               0.970473
   0.4      10          0          0.280000           0.763751               0.974023
   0.6      10          0          0.241429           0.756631               0.976291
   0.8      10          9          0.172857           0.737495               0.979359
