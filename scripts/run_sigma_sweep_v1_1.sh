#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source .venv/bin/activate

ABM="src/religion_fundamentalism_abm_v1_1.py"
if [[ ! -f "$ABM" ]]; then
  echo "ABM script not found at $ABM" >&2
  exit 1
fi

RUN_ROOT="${1:-}"
if [[ -z "$RUN_ROOT" ]]; then
  TS="$(date +%Y%m%d_%H%M%S)"
  RUN_ROOT="runs/batch_v1_1_phase_${TS}"
fi
mkdir -p "$RUN_ROOT" runs/_meta
printf '%s\n' "$RUN_ROOT" > runs/_meta/last_batch_v1_1_phase_root.txt

LOG="$RUN_ROOT/run_sigma_sweep_v1_1.log"

echo "[$(date -Iseconds)] Starting coarse sigma sweep v1.1 at $RUN_ROOT" | tee -a "$LOG"

echo "[$(date -Iseconds)] ABM=$ABM" | tee -a "$LOG"

run_one() {
  local sigma="$1"
  local seed="$2"
  local outdir="$RUN_ROOT/sigma_sweep/sigma_${sigma}/seed_$(printf '%02d' "$seed")"
  mkdir -p "$outdir"

  local cmd=(python "$ABM"
    --outdir "$outdir"
    --steps 450
    --n 350
    --graph scale_free
    --seed "$seed"
    --sigma "$sigma"
    --v_obs 0.95
    --a_obs 0.03
    --pi_reward 0.24
    --kappa_cost 0.08
    --lam_punish 0.28
    --backlash_base 0.25
    --backlash_cost 0.30
    --backlash_sensitivity 1.0
    --no_movie
  )

  echo "[$(date -Iseconds)] RUN ${cmd[*]}" | tee -a "$LOG"
  "${cmd[@]}" >> "$LOG" 2>&1
}

for i in $(seq 0 20); do
  sigma="$(awk -v x="$i" 'BEGIN { printf "%.2f", x * 0.05 }')"
  for seed in $(seq 1 10); do
    run_one "$sigma" "$seed"
  done
done

echo "[$(date -Iseconds)] Coarse sigma sweep v1.1 complete" | tee -a "$LOG"
printf '%s\n' "$RUN_ROOT"
