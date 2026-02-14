# v2.6 Ablation A alpha-only

- n_seed_runs: 50
- varying_dims: ['alpha']
- regime_counts: {'MIXED': 50}
- capture_threshold=none

## Medians
 alpha  n_runs  n_capture  median_exit_rate  median_top5_share  median_enforcer_share
   0.0      10          0          0.297143           0.782316               0.967563
   0.2      10          0          0.297143           0.772158               0.969576
   0.4      10          0          0.305714           0.777372               0.967662
   0.6      10          0          0.302857           0.779634               0.967357
   0.8      10          0          0.295714           0.769946               0.967734
