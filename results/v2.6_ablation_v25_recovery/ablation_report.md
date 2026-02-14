# v2.6 Ablation C v2.5 recovery

- n_seed_runs: 45
- varying_dims: ['sigma', 'pi_reward']
- regime_counts: {'MIXED': 40, 'QUIET': 5}
- capture_threshold=none

## Medians
 sigma  pi_reward  n_runs  n_capture  median_exit_rate  median_top5_share  median_enforcer_share
  0.25       0.05       5          0          0.082857           0.601725               0.643123
  0.25       0.25       5          0          0.417143           0.827919               0.789105
  0.25       0.50       5          0          0.434286           0.776189               0.687626
  0.75       0.05       5          0          0.348571           0.829451               0.934474
  0.75       0.25       5          0          0.377143           0.816746               0.958270
  0.75       0.50       5          0          0.374286           0.821035               0.964335
  0.95       0.05       5          0          0.302857           0.788606               0.957958
  0.95       0.25       5          0          0.317143           0.796600               0.970729
  0.95       0.50       5          0          0.297143           0.782783               0.967382
