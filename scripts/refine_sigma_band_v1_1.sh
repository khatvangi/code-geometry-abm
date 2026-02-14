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
  if [[ -f runs/_meta/last_batch_v1_1_phase_root.txt ]]; then
    RUN_ROOT="$(cat runs/_meta/last_batch_v1_1_phase_root.txt)"
  else
    echo "No run root provided and no runs/_meta/last_batch_v1_1_phase_root.txt found" >&2
    exit 1
  fi
fi

BAND_FILE="$RUN_ROOT/summary/sigma_activation_band.txt"
if [[ ! -f "$BAND_FILE" ]]; then
  echo "Activation band file not found: $BAND_FILE" >&2
  exit 1
fi

sigma_low="$(awk -F= '$1=="sigma_low" {print $2}' "$BAND_FILE")"
sigma_high="$(awk -F= '$1=="sigma_high" {print $2}' "$BAND_FILE")"

if [[ -z "$sigma_low" || -z "$sigma_high" || "$sigma_low" == "n/a" || "$sigma_high" == "n/a" ]]; then
  echo "Activation band unavailable in $BAND_FILE" >&2
  exit 1
fi

read sigma_low sigma_high < <(python - <<'PY' "$sigma_low" "$sigma_high"
import sys
lo=float(sys.argv[1]); hi=float(sys.argv[2])
if hi < lo:
    lo, hi = hi, lo
if abs(hi-lo) < 0.01:
    c=(hi+lo)/2.0
    lo=max(0.0, c-0.02)
    hi=min(1.0, c+0.02)
print(f"{lo:.2f} {hi:.2f}")
PY
)

LOG="$RUN_ROOT/run_sigma_refine_v1_1.log"
echo "[$(date -Iseconds)] Refining sigma v1.1 in [$sigma_low, $sigma_high]" | tee -a "$LOG"

run_one() {
  local sigma="$1"
  local seed="$2"
  local outdir="$RUN_ROOT/sigma_refine/sigma_${sigma}/seed_$(printf '%02d' "$seed")"
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

mapfile -t sigma_values < <(python - <<'PY' "$sigma_low" "$sigma_high"
import sys
lo=float(sys.argv[1]); hi=float(sys.argv[2])
if hi < lo:
    lo, hi = hi, lo
n=int(round((hi-lo)/0.01))
vals=[round(lo + i*0.01, 2) for i in range(n+1)]
vals=sorted(set(max(0.0, min(1.0, v)) for v in vals))
for v in vals:
    print(f"{v:.2f}")
PY
)

for sigma in "${sigma_values[@]}"; do
  for seed in $(seq 1 20); do
    run_one "$sigma" "$seed"
  done
done

echo "[$(date -Iseconds)] Sigma refinement v1.1 complete" | tee -a "$LOG"
printf '%s\n' "$RUN_ROOT"
