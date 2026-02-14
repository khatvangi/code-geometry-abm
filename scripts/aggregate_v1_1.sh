#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source .venv/bin/activate

RUN_ROOT="${1:-}"
if [[ -z "$RUN_ROOT" ]]; then
  if [[ -f runs/_meta/last_batch_v1_1_phase_root.txt ]]; then
    RUN_ROOT="$(cat runs/_meta/last_batch_v1_1_phase_root.txt)"
  else
    echo "No run root provided and no runs/_meta/last_batch_v1_1_phase_root.txt found" >&2
    exit 1
  fi
fi

mkdir -p "$RUN_ROOT/summary"

# 1) Coarse aggregate
python scripts/aggregate_sigma.py --root "$RUN_ROOT" --suite sigma_sweep --out-prefix sigma

# 2) Refine around detected activation band and aggregate refined
bash scripts/refine_sigma_band_v1_1.sh "$RUN_ROOT"
python scripts/aggregate_sigma.py --root "$RUN_ROOT" --suite sigma_refine --out-prefix sigma_refine

# 3) Optional quick pi sweep for threshold check (seed=1, no_movie)
ABM="src/religion_fundamentalism_abm_v1_1.py"
PI_DIR="$RUN_ROOT/pi_quick"
mkdir -p "$PI_DIR"
for i in $(seq 0 15); do
  pi="$(awk -v x="$i" 'BEGIN { printf "%.2f", x * 0.02 }')"
  outdir="$PI_DIR/pi_${pi}/seed_01"
  mkdir -p "$outdir"
  python "$ABM" \
    --outdir "$outdir" \
    --steps 450 \
    --n 350 \
    --graph scale_free \
    --seed 1 \
    --sigma 0.80 \
    --v_obs 0.95 \
    --a_obs 0.03 \
    --pi_reward "$pi" \
    --kappa_cost 0.08 \
    --lam_punish 0.28 \
    --backlash_base 0.25 \
    --backlash_cost 0.30 \
    --backlash_sensitivity 1.0 \
    --no_movie \
    >> "$RUN_ROOT/run_pi_quick_v1_1.log" 2>&1
  echo "[$(date -Iseconds)] pi_quick pi=$pi done" >> "$RUN_ROOT/run_pi_quick_v1_1.log"
done

python - <<'PY' "$RUN_ROOT"
import sys
from pathlib import Path
import pandas as pd

root = Path(sys.argv[1])
rows = []
for p in sorted((root / 'pi_quick').rglob('metrics.csv')):
    pi = None
    for part in p.parts:
        if part.startswith('pi_'):
            try:
                pi = float(part.split('_',1)[1])
                break
            except ValueError:
                continue
    if pi is None:
        continue
    df = pd.read_csv(p)
    if df.empty:
        continue
    final = df.iloc[-1]
    rows.append({'pi_reward': pi, 'fund_prevalence': float(final['fund_prevalence']), 'punish_rate': float(final['punish_rate'])})

out = pd.DataFrame(rows).sort_values('pi_reward')
out.to_csv(root / 'summary' / 'pi_quick_curve.csv', index=False)

def first_over(th):
    m = out['fund_prevalence'] > th
    return float(out.loc[m, 'pi_reward'].iloc[0]) if m.any() else None

with open(root / 'summary' / 'pi_thresholds.txt', 'w', encoding='utf-8') as f:
    p2 = first_over(0.2)
    p5 = first_over(0.5)
    f.write(f"pi_star_02={p2 if p2 is not None else 'n/a'}\n")
    f.write(f"pi_star_05={p5 if p5 is not None else 'n/a'}\n")
PY

# 4) Enforcement concentration + final results memo (v1.1 name)
python scripts/aggregate_enforcement_concentration.py --root "$RUN_ROOT"
cp -f "$RUN_ROOT/summary/RESULTS_V1.md" "$RUN_ROOT/summary/RESULTS_V1_1.md"

echo "$RUN_ROOT"
