#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source .venv/bin/activate

RUN_ROOT="${1:-runs/batch_v2_2_regimegrid_$(date +%Y%m%d_%H%M%S)}"
mkdir -p "$RUN_ROOT/grid"
mkdir -p runs/_meta
printf "%s\n" "$RUN_ROOT" > runs/_meta/last_batch_v2_2_regimegrid_root.txt

ABM="src/religion_fundamentalism_abm_v2_2.py"
SEEDS="${2:-5}"
STEPS="${3:-450}"
N="${4:-350}"
GRAPH="${5:-scale_free}"

EXIT_COSTS=(0.5 1.0 2.0 4.0 8.0)
SHOCKS=(0.10 0.20 0.30 0.40)

for exit_cost in "${EXIT_COSTS[@]}"; do
  for shock in "${SHOCKS[@]}"; do
    for seed in $(seq 1 "$SEEDS"); do
      seed_str=$(printf "%02d" "$seed")
      outdir="$RUN_ROOT/grid/exit_${exit_cost}/shock_${shock}/seed_${seed_str}"
      mkdir -p "$outdir"

      echo "[$(date -Iseconds)] RUN grid exit_cost=${exit_cost} shock=${shock} seed=${seed}" | tee -a "$RUN_ROOT/run_grid.log"
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
        --w_heresy 0.60 \
        --d0 0.18 \
        --pi_reward 0.24 \
        --kappa_cost 0.08 \
        --lam_punish 0.28 \
        --backlash_base 0.25 \
        --backlash_cost 0.30 \
        --backlash_sensitivity 1.0 \
        --exit_cost "$exit_cost" \
        --exit_threshold -1.0 \
        --exit_prob_slope 3.0 \
        --exit_rewire_fraction 0.90 \
        --exit_degree_coeff 0.03 \
        --exit_epc_lockin_coeff 0.25 \
        --exit_min_cost 0.0 \
        --exit_opportunity_base 0.6 \
        --exit_opportunity_deg_coeff 0.03 \
        --exit_opportunity_threat_coeff 1.5 \
        --exit_commit_steps 8 \
        --exit_cooldown 0 \
        --shock_schedule "100,220,320" \
        --shock_strength "$shock" \
        --tighten_gain_pi 0.20 \
        --tighten_gain_lam 0.20 \
        --tighten_gain_d0 0.08 \
        --relax_rate 0.03 \
        --baseline_pi 0.24 \
        --baseline_lam 0.28 \
        --baseline_d0 0.18 \
        --no_movie \
        >> "$RUN_ROOT/run_grid.log" 2>&1
    done
  done
done

echo "$RUN_ROOT"
