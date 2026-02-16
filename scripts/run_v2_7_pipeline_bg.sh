#!/usr/bin/env bash
set -euo pipefail
cd /storage/social-science/religion-code-geometry-abm
source .venv/bin/activate

python scripts/run_v2_7_endogenous_delta_sweep.py \
  --out results/v2.7_endogenous_delta_sweep \
  --model src/religion_fundamentalism_abm_v2_7.py \
  --eta-values 0.0,0.05,0.1,0.2,0.3 \
  --delta-values 0.1,0.2,0.3 \
  --sigma-values 0.25,0.75,0.95 \
  --pi-values 0.05,0.25,0.50 \
  --alpha-fixed 0.0 --mu-fixed 0.0 \
  --seeds 10 --workers 3 --steps 450 \
  --base-opp 0.3 --exit-threshold -1.0 --capture-exit-cap 0.20

python scripts/run_v2_7_endogenous_delta_sweep.py \
  --out results/v2.7_ablation_emergence \
  --model src/religion_fundamentalism_abm_v2_7.py \
  --eta-values 0.0,0.05,0.1,0.15,0.2,0.3 \
  --delta-values 0.2 \
  --sigma-values 0.95 \
  --pi-values 0.50 \
  --alpha-fixed 0.0 --mu-fixed 0.0 \
  --seeds 10 --workers 3 --steps 450 \
  --base-opp 0.3 --exit-threshold -1.0 --capture-exit-cap 0.20

python scripts/analyze_v2_7_emergence_ablation.py \
  --root results/v2.7_ablation_emergence \
  --capture-exit-cap 0.20
