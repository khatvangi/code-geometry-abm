# RESULTS_CONTINUOUS.md — continuous primary surfaces

Threshold-free surfaces underlying the Results. Means over seeds per cell.
Generated 2026-07-19 from committed CSVs. Cell count = seeds per cell (uniform).

## boundary_open (exit OPEN, delta0=0) — `recon/boundary_open/sweep_seed_results.csv`
n=1890 runs, 9 sigma x 7 pi x 30 seeds/cell.

### mean terminal exit rate (final_exit_rate)
```
pi_reward   0.01   0.03   0.05   0.10   0.15   0.25   0.50
sigma                                                     
0.05       0.176  0.173  0.176  0.174  0.172  0.542  0.500
0.15       0.096  0.097  0.094  0.374  0.490  0.464  0.440
0.25       0.046  0.044  0.044  0.446  0.433  0.405  0.426
0.35       0.016  0.016  0.319  0.409  0.383  0.403  0.446
0.45       0.005  0.005  0.400  0.385  0.382  0.400  0.448
0.55       0.002  0.219  0.380  0.384  0.393  0.417  0.440
0.65       0.000  0.306  0.368  0.378  0.384  0.424  0.419
0.75       0.000  0.343  0.366  0.374  0.389  0.400  0.399
0.95       0.000  0.319  0.318  0.324  0.322  0.317  0.310
```
### mean max_punish (enforcement intensity)
```
pi_reward   0.01   0.03   0.05   0.10   0.15   0.25   0.50
sigma                                                     
0.05       0.050  0.050  0.050  0.050  0.050  0.091  0.110
0.15       0.050  0.050  0.050  0.064  0.098  0.109  0.148
0.25       0.051  0.051  0.051  0.102  0.110  0.132  0.172
0.35       0.046  0.047  0.074  0.117  0.130  0.156  0.181
0.45       0.046  0.046  0.105  0.133  0.152  0.173  0.181
0.55       0.044  0.066  0.126  0.149  0.164  0.173  0.180
0.65       0.042  0.093  0.136  0.156  0.163  0.171  0.174
0.75       0.039  0.118  0.143  0.154  0.162  0.162  0.163
0.95       0.033  0.128  0.130  0.136  0.138  0.136  0.135
```

## boundary_sealed (exit SEALED, delta0=0.95) — `recon/boundary_sealed/sweep_seed_results.csv`
n=1890 runs, 9 sigma x 7 pi x 30 seeds/cell.

### mean terminal exit rate (final_exit_rate)
```
pi_reward   0.01   0.03   0.05   0.10   0.15   0.25   0.50
sigma                                                     
0.05       0.008  0.008  0.009  0.007  0.008  0.084  0.107
0.15       0.004  0.004  0.004  0.047  0.080  0.099  0.138
0.25       0.002  0.002  0.002  0.077  0.081  0.105  0.141
0.35       0.001  0.001  0.042  0.076  0.096  0.128  0.128
0.45       0.000  0.000  0.068  0.089  0.110  0.117  0.118
0.55       0.000  0.023  0.068  0.100  0.108  0.113  0.110
0.65       0.000  0.041  0.073  0.092  0.100  0.097  0.097
0.75       0.000  0.058  0.076  0.081  0.083  0.082  0.083
0.95       0.000  0.056  0.053  0.055  0.055  0.054  0.054
```
### mean max_punish (enforcement intensity)
```
pi_reward   0.01   0.03   0.05   0.10   0.15   0.25   0.50
sigma                                                     
0.05       0.050  0.050  0.050  0.050  0.050  0.107  0.126
0.15       0.050  0.050  0.050  0.087  0.113  0.131  0.186
0.25       0.051  0.051  0.051  0.121  0.129  0.164  0.196
0.35       0.046  0.047  0.099  0.136  0.159  0.192  0.202
0.45       0.046  0.046  0.130  0.163  0.183  0.197  0.204
0.55       0.044  0.086  0.147  0.182  0.192  0.200  0.202
0.65       0.042  0.125  0.161  0.179  0.189  0.197  0.195
0.75       0.039  0.151  0.173  0.179  0.189  0.189  0.189
0.95       0.033  0.154  0.158  0.164  0.166  0.165  0.165
```

## exogenous_delta_fixed (imposed exit closure) — `recon/exogenous_delta_fixed/sweep_seed_results.csv`
n=1620 runs, sigma[np.float64(0.25), np.float64(0.75), np.float64(0.95)] x pi[np.float64(0.05), np.float64(0.25), np.float64(0.5)] x delta0[np.float64(0.0), np.float64(0.2), np.float64(0.4), np.float64(0.6), np.float64(0.8), np.float64(0.95)] x 30 seeds/cell.

### mean max_punish and mean exit by imposed delta0 (pooled over sigma,pi)
```
        mean_max_punish  mean_exit    n
delta0                                 
0.00              0.136      0.332  270
0.20              0.139      0.324  270
0.40              0.143      0.313  270
0.60              0.148      0.288  270
0.80              0.155      0.216  270
0.95              0.161      0.072  270
```

### mean max_punish over sigma x pi at delta0=0.95 (fully sealed)
```
pi_reward   0.05   0.25   0.50
sigma                         
0.25       0.051  0.164  0.196
0.75       0.173  0.189  0.189
0.95       0.158  0.165  0.165
```

## Threshold-free necessity claim (sigma=0.25, pi=0.05 corner)
If code geometry gates activation, closing the exit should NOT raise enforcement
intensity in a dead corner. Mean over 30 seeds:

| delta0 | n | mean max_punish | mean exit |
|---|---|---|---|
| 0.0 | 30 | 0.051 | 0.044 |
| 0.95 | 30 | 0.051 | 0.002 |

Enforcement intensity at delta=0.95 (0.051) vs delta=0.0 (0.051): change +0.000. Both far below the 0.10 activation band, and sealing the exit
does NOT raise enforcement in this corner — the necessity result holds
without any threshold: it is a statement about the continuous enforcement surface.
