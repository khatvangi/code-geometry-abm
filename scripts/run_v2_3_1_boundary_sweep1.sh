#!/usr/bin/env bash
set -euo pipefail

OUT_ROOT="${1:-runs/batch_v2_3_1_boundaries_$(date +%Y%m%d_%H%M%S)}"
BEST_JSON="${2:-runs/batch_v2_3_search_20260213_043518/summary/BEST_PARAMS.json}"

if [[ ! -f "$BEST_JSON" ]]; then
  echo "BEST_PARAMS not found: $BEST_JSON" >&2
  exit 1
fi

mkdir -p "$OUT_ROOT/sweep1"

if command -v ffmpeg >/dev/null 2>&1; then
  export IMAGEIO_FFMPEG_EXE=ffmpeg
fi

eval "$(python - <<'PY' "$BEST_JSON"
import json, sys
p = json.load(open(sys.argv[1], 'r', encoding='utf-8')).get('params', {})
print(f"MB={float(p.get('membership_benefit', 0.03))!r}")
print(f"MBT={float(p.get('membership_benefit_threat', 0.10))!r}")
print(f"OPP_BASE={float(p.get('exit_opportunity_base', 0.6))!r}")
print(f"BLOCK_EXP={float(p.get('exit_block_exponent', 2.5))!r}")
print(f"COMMIT_STEPS={int(p.get('exit_commit_steps', 8))!r}")
print(f"EXIT_COST={float(p.get('exit_cost', 0.4))!r}")
PY
)"

THREAT_COEFFS=(0.5 1.0 2.0 3.5 5.0 7.0)
SHOCKS=(0.10 0.20 0.30 0.40 0.55)

for coeff in "${THREAT_COEFFS[@]}"; do
  coeff_fmt=$(printf "%.2f" "$coeff")
  for shock in "${SHOCKS[@]}"; do
    shock_fmt=$(printf "%.2f" "$shock")
    for seed in $(seq -w 1 5); do
      iseed=$((10#$seed))
      outdir="$OUT_ROOT/sweep1/threatCoeff_${coeff_fmt}/shock_${shock_fmt}/seed_${seed}"
      mkdir -p "$outdir"
      echo "[$(date -Iseconds)] RUN sweep1 coeff=${coeff_fmt} shock=${shock_fmt} seed=${iseed}"
      python src/religion_fundamentalism_abm_v2_3_1.py \
        --outdir "$outdir" \
        --steps 450 \
        --n 350 \
        --graph scale_free \
        --seed "$iseed" \
        --sigma 0.80 \
        --shock_schedule 100,220,320 \
        --shock_strength "$shock" \
        --membership_benefit "$MB" \
        --membership_benefit_threat "$MBT" \
        --exit_opportunity_base "$OPP_BASE" \
        --exit_opportunity_threat_coeff "$coeff" \
        --exit_block_exponent "$BLOCK_EXP" \
        --exit_commit_steps "$COMMIT_STEPS" \
        --exit_cost "$EXIT_COST" \
        --no_movie >/dev/null 2>&1
    done
  done
done

echo "$OUT_ROOT"
