#!/usr/bin/env bash
set -euo pipefail

# Usage examples:
#   bash scripts/run_abm.sh runs/high_sigma 450 350 scale_free 1 0.80 0.95 0.03 0.24 0.08 0.28
# Args:
#   outdir steps n graph seed sigma v_obs a_obs pi_reward kappa_cost lam_punish

OUTDIR="${1:-runs/demo}"
STEPS="${2:-350}"
N="${3:-300}"
GRAPH="${4:-scale_free}"
SEED="${5:-1}"

SIGMA="${6:-0.75}"
VOBS="${7:-0.90}"
AOBS="${8:-0.05}"

PI="${9:-0.22}"
KAPPA="${10:-0.08}"
LAM="${11:-0.25}"

source .venv/bin/activate

python src/religion_fundamentalism_abm.py \
  --outdir "$OUTDIR" \
  --steps "$STEPS" \
  --n "$N" \
  --graph "$GRAPH" \
  --seed "$SEED" \
  --sigma "$SIGMA" \
  --v_obs "$VOBS" \
  --a_obs "$AOBS" \
  --pi_reward "$PI" \
  --kappa_cost "$KAPPA" \
  --lam_punish "$LAM"
