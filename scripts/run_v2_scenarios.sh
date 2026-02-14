#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source .venv/bin/activate

if command -v ffmpeg >/dev/null 2>&1; then
  export IMAGEIO_FFMPEG_EXE=ffmpeg
fi

TS="$(date +%Y%m%d_%H%M%S)"
RUN_ROOT="runs/batch_v2_heresy_apostasy_${TS}"
mkdir -p "$RUN_ROOT"
mkdir -p runs/_meta
printf "%s\n" "$RUN_ROOT" > runs/_meta/last_batch_v2_heresy_apostasy_root.txt

ABM="src/religion_fundamentalism_abm_v2.py"
SEEDS="${1:-10}"
STEPS="${2:-450}"
N="${3:-350}"
GRAPH="${4:-scale_free}"

cat > "$RUN_ROOT/scenario_config.csv" << 'CSV'
scenario,sigma,h_obs,w_heresy,d0,shock_schedule,shock_strength,tighten_gain_pi,tighten_gain_lam,tighten_gain_d0,enable_exit,exit_cost,exit_threshold,exit_prob_slope
S0_no_controller_no_exit,0.80,0.15,0.30,0.20,,0.00,0.00,0.00,0.00,false,5.00,-10.0,6.0
S1_controller_no_exit,0.80,0.15,0.60,0.18,100\,220\,320,0.25,0.20,0.20,0.08,false,5.00,-10.0,6.0
S2_controller_exit,0.80,0.15,0.60,0.18,100\,220\,320,0.25,0.20,0.20,0.08,true,0.40,-1.0,6.0
S3_high_heresy,0.80,0.25,1.20,0.10,100\,220\,320,0.25,0.20,0.20,0.08,false,5.00,-10.0,6.0
S4_low_legibility_controller,0.15,0.15,0.60,0.18,100\,220\,320,0.25,0.20,0.20,0.08,true,0.40,-1.0,6.0
CSV

run_scenario() {
  local scenario="$1"
  local sigma="$2"
  local h_obs="$3"
  local w_heresy="$4"
  local d0="$5"
  local shock_schedule="$6"
  local shock_strength="$7"
  local gain_pi="$8"
  local gain_lam="$9"
  local gain_d0="${10}"
  local exit_cost="${11}"
  local exit_threshold="${12}"
  local exit_slope="${13}"
  local enable_exit="${14}"

  for seed in $(seq 1 "$SEEDS"); do
    seed_str=$(printf "%02d" "$seed")
    outdir="$RUN_ROOT/$scenario/seed_${seed_str}"
    mkdir -p "$outdir"

    echo "[$(date -Iseconds)] RUN $scenario seed=$seed" | tee -a "$RUN_ROOT/run.log"
    extra_exit_flag=()
    if [[ "$enable_exit" == "false" ]]; then
      extra_exit_flag=(--disable_exit)
    fi
    python "$ABM" \
      --outdir "$outdir" \
      --steps "$STEPS" \
      --n "$N" \
      --graph "$GRAPH" \
      --seed "$seed" \
      --sigma "$sigma" \
      --v_obs 0.95 \
      --a_obs 0.03 \
      --h_obs "$h_obs" \
      --w_heresy "$w_heresy" \
      --d0 "$d0" \
      --pi_reward 0.24 \
      --kappa_cost 0.08 \
      --lam_punish 0.28 \
      --backlash_base 0.25 \
      --backlash_cost 0.30 \
      --backlash_sensitivity 1.0 \
      --exit_cost "$exit_cost" \
      --exit_threshold "$exit_threshold" \
      --exit_prob_slope "$exit_slope" \
      --exit_rewire_fraction 0.90 \
      "${extra_exit_flag[@]}" \
      --shock_schedule "$shock_schedule" \
      --shock_strength "$shock_strength" \
      --tighten_gain_pi "$gain_pi" \
      --tighten_gain_lam "$gain_lam" \
      --tighten_gain_d0 "$gain_d0" \
      --relax_rate 0.03 \
      --baseline_pi 0.24 \
      --baseline_lam 0.28 \
      --baseline_d0 "$d0" \
      --no_movie \
      >> "$RUN_ROOT/run.log" 2>&1
  done
}

run_scenario "S0_no_controller_no_exit" 0.80 0.15 0.30 0.20 "" 0.00 0.00 0.00 0.00 5.00 -10.0 6.0 false
run_scenario "S1_controller_no_exit" 0.80 0.15 0.60 0.18 "100,220,320" 0.25 0.20 0.20 0.08 5.00 -10.0 6.0 false
run_scenario "S2_controller_exit" 0.80 0.15 0.60 0.18 "100,220,320" 0.25 0.20 0.20 0.08 0.40 -1.0 6.0 true
run_scenario "S3_high_heresy" 0.80 0.25 1.20 0.10 "100,220,320" 0.25 0.20 0.20 0.08 5.00 -10.0 6.0 false
run_scenario "S4_low_legibility_controller" 0.15 0.15 0.60 0.18 "100,220,320" 0.25 0.20 0.20 0.08 0.40 -1.0 6.0 true

echo "$RUN_ROOT"
