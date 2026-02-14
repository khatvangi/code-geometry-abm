#!/usr/bin/env bash
set -euo pipefail

OUT_ROOT="${1:-runs/batch_v2_4_internal_army_$(date +%Y%m%d_%H%M%S)}"
BEST_JSON="${2:-runs/batch_v2_3_search_20260213_043518/summary/BEST_PARAMS.json}"
QUOTA="${3:-0.08}"

if [[ ! -f "$BEST_JSON" ]]; then
  echo "BEST_PARAMS not found: $BEST_JSON" >&2
  exit 1
fi

mkdir -p "$OUT_ROOT/sweep2"
if command -v ffmpeg >/dev/null 2>&1; then
  export IMAGEIO_FFMPEG_EXE=ffmpeg
fi

eval "$(python - <<'PY' "$BEST_JSON"
import json,sys
p=json.load(open(sys.argv[1], 'r', encoding='utf-8')).get('params', {})
print(f"MB={float(p.get('membership_benefit', 0.03))!r}")
print(f"OPP_THREAT={float(p.get('exit_opportunity_threat_coeff', 1.5))!r}")
print(f"BLOCK_EXP={float(p.get('exit_block_exponent', 2.5))!r}")
print(f"COMMIT_STEPS={int(p.get('exit_commit_steps', 8))!r}")
print(f"EXIT_COST={float(p.get('exit_cost', 0.4))!r}")
print(f"SHOCK={float(p.get('shock_strength', 0.25))!r}")
PY
)"

MBTS=(0.00 0.05 0.10 0.15 0.22 0.30)
OPP_BASES=(0.10 0.25 0.40 0.55 0.70 0.85)
qfmt=$(printf "%.2f" "$QUOTA")

for mbt in "${MBTS[@]}"; do
  mbt_fmt=$(printf "%.2f" "$mbt")
  for oppb in "${OPP_BASES[@]}"; do
    oppb_fmt=$(printf "%.2f" "$oppb")
    for seed in $(seq -w 1 5); do
      iseed=$((10#$seed))
      outdir="$OUT_ROOT/sweep2/quota_${qfmt}/mbt_${mbt_fmt}/oppBase_${oppb_fmt}/seed_${seed}"
      mkdir -p "$outdir"
      echo "[$(date -Iseconds)] RUN v2.4 sweep2 quota=${qfmt} mbt=${mbt_fmt} oppBase=${oppb_fmt} seed=${iseed}"
      python src/religion_fundamentalism_abm_v2_4.py \
        --outdir "$outdir" \
        --steps 450 \
        --n 350 \
        --graph scale_free \
        --seed "$iseed" \
        --sigma 0.80 \
        --shock_schedule 100,220,320 \
        --shock_strength "$SHOCK" \
        --membership_benefit "$MB" \
        --membership_benefit_threat "$mbt" \
        --exit_opportunity_base "$oppb" \
        --exit_opportunity_threat_coeff "$OPP_THREAT" \
        --exit_block_exponent "$BLOCK_EXP" \
        --exit_commit_steps "$COMMIT_STEPS" \
        --exit_cost "$EXIT_COST" \
        --enforcer_quota_frac "$QUOTA" \
        --A_gain_threat 2.0 \
        --budget_base 0.02 \
        --budget_threat_gain 0.08 \
        --cap_decay 0.01 \
        --cap_gain_per_punish 0.06 \
        --cap_to_enforcer 0.25 \
        --cap_max 2.0 \
        --service_decay 0.02 \
        --non_enforcer_punish_mult 0.25 \
        --enforcer_punish_mult 1.5 \
        --kappa_cap_discount 0.20 \
        --no_movie >/dev/null 2>&1
    done
  done
done

echo "$OUT_ROOT"
