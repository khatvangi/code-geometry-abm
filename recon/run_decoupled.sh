#!/usr/bin/env bash
set -u
cd /storage/kiran-stuff/code-geometry-abm
echo "DECOUPLED SWEEP START $(date -Is)"
for K in 1.5 3.0 6.0; do
  python scripts/run_v2_7_endogenous_delta_sweep.py --out recon/decoupled_k${K} --seeds 30 --workers 20 --shock-schedule "" --delta-mode decoupled --delta-cap 0.85 --delta-kappa ${K} > recon/decoupled_k${K}.log 2>&1 &
done
wait
echo "DECOUPLED SWEEP COMPLETE $(date -Is)"
