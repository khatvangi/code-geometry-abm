#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source .venv/bin/activate

RUN_ROOT="${1:-}"
if [[ -z "$RUN_ROOT" ]]; then
  if [[ -f runs/_meta/last_batch_v2_1_exitfriction_root.txt ]]; then
    RUN_ROOT="$(cat runs/_meta/last_batch_v2_1_exitfriction_root.txt)"
  else
    RUN_ROOT="runs/batch_v2_1_exitfriction_$(date +%Y%m%d_%H%M%S)"
  fi
fi
mkdir -p "$RUN_ROOT"
printf "%s\n" "$RUN_ROOT" > runs/_meta/last_batch_v2_1_exitfriction_root.txt

ABM="src/religion_fundamentalism_abm_v2_1.py"
SEEDS="${2:-10}"
STEPS="${3:-450}"
N="${4:-350}"
GRAPH="${5:-scale_free}"

run_case() {
  local label="$1"
  local sigma="$2"
  local disable_exit="$3"

  for seed in $(seq 1 "$SEEDS"); do
    seed_str=$(printf "%02d" "$seed")
    outdir="$RUN_ROOT/$label/seed_${seed_str}"
    mkdir -p "$outdir"

    extra_exit_flag=()
    if [[ "$disable_exit" == "true" ]]; then
      extra_exit_flag=(--disable_exit)
    fi

    echo "[$(date -Iseconds)] RUN $label seed=$seed" | tee -a "$RUN_ROOT/run.log"
    python "$ABM" \
      --outdir "$outdir" \
      --steps "$STEPS" \
      --n "$N" \
      --graph "$GRAPH" \
      --seed "$seed" \
      --sigma "$sigma" \
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
      --exit_cost 0.40 \
      --exit_threshold -1.0 \
      --exit_prob_slope 6.0 \
      --exit_rewire_fraction 0.90 \
      --exit_degree_coeff 0.03 \
      --exit_epc_lockin_coeff 0.25 \
      --exit_min_cost 0.0 \
      "${extra_exit_flag[@]}" \
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
      >> "$RUN_ROOT/run.log" 2>&1
  done
}

run_case "S2_prime" 0.80 false
run_case "S4_prime" 0.15 false
run_case "S1_prime" 0.80 true

echo "$RUN_ROOT"
