#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source .venv/bin/activate

SEARCH_ROOT="${1:-}"
if [[ -z "$SEARCH_ROOT" ]]; then
  latest=$(ls -dt runs/batch_v2_3_search_* 2>/dev/null | head -n1 || true)
  if [[ -z "$latest" ]]; then
    echo "No search root provided and no runs/batch_v2_3_search_* found" >&2
    exit 1
  fi
  SEARCH_ROOT="$latest"
fi

BEST_JSON="$SEARCH_ROOT/summary/BEST_PARAMS.json"
if [[ ! -f "$BEST_JSON" ]]; then
  echo "BEST_PARAMS.json not found at $BEST_JSON" >&2
  exit 1
fi

found_hit=$(python - <<'PY' "$BEST_JSON"
import json,sys
j=json.load(open(sys.argv[1]))
print("1" if j.get("found_hit") else "0")
PY
)
if [[ "$found_hit" != "1" ]]; then
  echo "No hit in BEST_PARAMS; skipping confirm grid." >&2
  exit 2
fi

TS="$(date +%Y%m%d_%H%M%S)"
RUN_ROOT="runs/batch_v2_3_confirm_${TS}"
mkdir -p "$RUN_ROOT/grid"
mkdir -p runs/_meta
printf "%s\n" "$RUN_ROOT" > runs/_meta/last_batch_v2_3_confirm_root.txt

readarray -t vals < <(python - <<'PY' "$BEST_JSON"
import json,sys
j=json.load(open(sys.argv[1]))
p=j["params"]
exit_cost=float(p["exit_cost"])
print(exit_cost)
print(p["membership_benefit"])
print(p["membership_benefit_threat"])
print(p["exit_opportunity_base"])
print(p["exit_opportunity_threat_coeff"])
print(p["exit_block_exponent"])
print(int(p["exit_commit_steps"]))
PY
)

BEST_EXIT="${vals[0]}"
MB="${vals[1]}"
MBT="${vals[2]}"
EOB="${vals[3]}"
EOTC="${vals[4]}"
EBE="${vals[5]}"
ECS="${vals[6]}"

ABM="src/religion_fundamentalism_abm_v2_3.py"
SEEDS="${2:-5}"
STEPS="${3:-450}"
N="${4:-350}"
GRAPH="${5:-scale_free}"

exit_half=$(python - <<'PY' "$BEST_EXIT"
import sys
v=float(sys.argv[1])
print(max(0.1, v/2.0))
PY
)
exit_double=$(python - <<'PY' "$BEST_EXIT"
import sys
v=float(sys.argv[1])
print(v*2.0)
PY
)

EXIT_COSTS=("$exit_half" "$BEST_EXIT" "$exit_double")
SHOCKS=(0.20 0.30 0.40)

for ec in "${EXIT_COSTS[@]}"; do
  ecf=$(python - <<'PY' "$ec"
import sys
print(f"{float(sys.argv[1]):.3f}")
PY
)
  for sh in "${SHOCKS[@]}"; do
    for seed in $(seq 1 "$SEEDS"); do
      seed_str=$(printf "%02d" "$seed")
      outdir="$RUN_ROOT/grid/exit_${ecf}/shock_${sh}/seed_${seed_str}"
      mkdir -p "$outdir"
      echo "[$(date -Iseconds)] RUN confirm exit_cost=$ecf shock=$sh seed=$seed" | tee -a "$RUN_ROOT/run_confirm.log"
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
        --exit_cost "$ecf" \
        --exit_threshold -1.0 \
        --exit_prob_slope 3.0 \
        --exit_rewire_fraction 0.90 \
        --exit_degree_coeff 0.03 \
        --exit_epc_lockin_coeff 0.25 \
        --exit_min_cost 0.0 \
        --exit_opportunity_base "$EOB" \
        --exit_opportunity_deg_coeff 0.03 \
        --exit_opportunity_threat_coeff "$EOTC" \
        --exit_block_exponent "$EBE" \
        --exit_block_floor 0.02 \
        --exit_commit_steps "$ECS" \
        --membership_benefit "$MB" \
        --membership_benefit_sigma 0.08 \
        --membership_benefit_threat "$MBT" \
        --shock_schedule "100,220,320" \
        --shock_strength "$sh" \
        --tighten_gain_pi 0.20 \
        --tighten_gain_lam 0.20 \
        --tighten_gain_d0 0.08 \
        --relax_rate 0.03 \
        --baseline_pi 0.24 \
        --baseline_lam 0.28 \
        --baseline_d0 0.18 \
        --no_movie \
        >> "$RUN_ROOT/run_confirm.log" 2>&1
    done
  done
done

echo "$RUN_ROOT"
