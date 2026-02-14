#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source .venv/bin/activate

if command -v ffmpeg >/dev/null 2>&1; then
  export IMAGEIO_FFMPEG_EXE=ffmpeg
fi

RUN_ROOT="${1:-}"
if [[ -z "$RUN_ROOT" ]]; then
  if [[ -f runs/_meta/last_batch_v2_regimemap_root.txt ]]; then
    RUN_ROOT="$(cat runs/_meta/last_batch_v2_regimemap_root.txt)"
  else
    RUN_ROOT="runs/batch_v2_regimemap_$(date +%Y%m%d_%H%M%S)"
  fi
fi
mkdir -p "$RUN_ROOT/heresy_weight_sweep"
printf "%s\n" "$RUN_ROOT" > runs/_meta/last_batch_v2_regimemap_root.txt

ABM="src/religion_fundamentalism_abm_v2.py"
SEEDS="${2:-10}"
STEPS="${3:-450}"
N="${4:-350}"
GRAPH="${5:-scale_free}"

for v in $(seq 0 1 10); do
  w="$(awk -v x="$v" 'BEGIN { printf "%.2f", x/10.0 }')"
  for seed in $(seq 1 "$SEEDS"); do
    seed_str=$(printf "%02d" "$seed")
    outdir="$RUN_ROOT/heresy_weight_sweep/w_heresy_${w}/seed_${seed_str}"
    mkdir -p "$outdir"

    echo "[$(date -Iseconds)] heresy_weight_sweep w_heresy=${w} seed=${seed}" | tee -a "$RUN_ROOT/run_heresy_weight_sweep.log"
    python "$ABM" \
      --outdir "$outdir" \
      --steps "$STEPS" \
      --n "$N" \
      --graph "$GRAPH" \
      --seed "$seed" \
      --sigma 0.80 \
      --v_obs 0.95 \
      --a_obs 0.03 \
      --h_obs 0.15 \
      --w_heresy "$w" \
      --d0 0.18 \
      --pi_reward 0.24 \
      --kappa_cost 0.08 \
      --lam_punish 0.28 \
      --backlash_base 0.25 \
      --backlash_cost 0.30 \
      --backlash_sensitivity 1.0 \
      --disable_exit \
      --exit_cost 999 \
      --exit_threshold -999 \
      --exit_prob_slope 6.0 \
      --exit_rewire_fraction 0.90 \
      --shock_schedule "100,220,320" \
      --shock_strength 0.25 \
      --tighten_gain_pi 0.20 \
      --tighten_gain_lam 0.20 \
      --tighten_gain_d0 0.08 \
      --relax_rate 0.03 \
      --baseline_pi 0.24 \
      --baseline_lam 0.28 \
      --baseline_d0 0.18 \
      --no_movie \
      >> "$RUN_ROOT/run_heresy_weight_sweep.log" 2>&1
  done
done

echo "$RUN_ROOT"
