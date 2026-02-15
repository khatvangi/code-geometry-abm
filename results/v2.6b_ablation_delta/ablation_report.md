# v2.6b ablation B (delta only)

- n_seed_runs: 50
- varying_dims: ['delta']
- regime_counts: {'MIXED': 39, 'CAPTURE': 11}
- capture_threshold~delta=0.7

## Medians
 delta  n_runs  n_capture  n_mixed  median_exit_rate  median_top5_share  median_enforcer_share
   0.0      10          0       10          0.297143           0.782316               0.967563
   0.3      10          0       10          0.284286           0.766834               0.971385
   0.6      10          0       10          0.241429           0.756631               0.976291
   0.7      10          2        8          0.232857           0.742431               0.977880
   0.8      10          9        1          0.172857           0.737495               0.979359
