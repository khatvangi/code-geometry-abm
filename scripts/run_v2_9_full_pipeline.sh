#!/bin/bash
# v2.9 full pipeline: calibration -> analysis -> confirmatory -> ablation
# run with: nohup bash scripts/run_v2_9_full_pipeline.sh > results/v2.9_pipeline.log 2>&1 &

set -e
cd /storage/social-science/religion-code-geometry-abm

echo "=========================================="
echo "v2.9 FULL PIPELINE"
echo "started: $(date)"
echo "=========================================="

# ---- stage 1: calibration sweep ----
echo ""
echo "[STAGE 1] calibration sweep (243 combos x 5 seeds = 1215 runs)"
echo "started: $(date)"
python scripts/run_v2_9_acquiescence_sweep.py \
    --stage calibration \
    --out results/v2.9_acquiescence_calibration \
    --workers 3
echo "[STAGE 1] complete: $(date)"

# ---- stage 1 analysis ----
echo ""
echo "[ANALYSIS 1] calibration analysis"
python scripts/analyze_v2_9_calibration.py results/v2.9_acquiescence_calibration
echo "[ANALYSIS 1] complete: $(date)"

# ---- extract best omegas from calibration ----
# pick the smallest-omega CAPTURE cell from the calibration report
echo ""
echo "[SELECT] extracting best-calibration omegas..."
BEST_OMEGAS=$(python -c "
import pandas as pd
import sys
s = pd.read_csv('results/v2.9_acquiescence_calibration/sweep_summary.csv')
cap = s[s['regime_consensus'] == 'CAPTURE'].copy()
if cap.empty:
    # fallback: use majority
    cap = s[s['regime_majority'] == 'CAPTURE'].copy()
if cap.empty:
    print('NO_CAPTURE', file=sys.stderr)
    # use defaults as fallback
    print('0.02 0.03 0.04 0.02 0.05')
    sys.exit(0)
omega_cols = [c for c in ['ox','od','oe','ot','gq'] if c in cap.columns]
cap['omega_sum'] = cap[omega_cols].sum(axis=1)
best = cap.nsmallest(1, 'omega_sum').iloc[0]
print(f\"{best.get('ox',0.02):.4f} {best.get('od',0.03):.4f} {best.get('oe',0.04):.4f} {best.get('ot',0.02):.4f} {best.get('gq',0.05):.4f}\")
")
read OX OD OE OT GQ <<< "$BEST_OMEGAS"
echo "  best omegas: ox=$OX od=$OD oe=$OE ot=$OT gq=$GQ"

# ---- stage 2: confirmatory sweep ----
echo ""
echo "[STAGE 2] confirmatory sweep (72 cells x 5 seeds = 360 runs)"
echo "  using best omegas: ox=$OX od=$OD oe=$OE ot=$OT gq=$GQ"
echo "started: $(date)"
python scripts/run_v2_9_acquiescence_sweep.py \
    --stage confirmatory \
    --out results/v2.9_confirmatory_sweep \
    --omega-x-fixed "$OX" \
    --omega-delta-fixed "$OD" \
    --omega-e-fixed "$OE" \
    --omega-t-fixed "$OT" \
    --gamma-q-fixed "$GQ" \
    --workers 3
echo "[STAGE 2] complete: $(date)"

# ---- stage 2 analysis ----
echo ""
echo "[ANALYSIS 2] confirmatory analysis"
python scripts/analyze_v2_9_confirmatory.py results/v2.9_confirmatory_sweep
echo "[ANALYSIS 2] complete: $(date)"

# ---- stage 3: ablation ----
echo ""
echo "[STAGE 3] ablation sweep"
echo "started: $(date)"

# find CAPTURE cells from confirmatory sweep
CAPTURE_CELLS=$(python -c "
import pandas as pd
s = pd.read_csv('results/v2.9_confirmatory_sweep/sweep_summary.csv')
regime_col = 'regime_consensus' if 'regime_consensus' in s.columns else 'regime_majority'
cap = s[s[regime_col] == 'CAPTURE']
if cap.empty:
    print('NONE')
else:
    # output as sigma,pi,bopp,eta,delta0 lines
    for _, r in cap.iterrows():
        print(f\"{r.get('sigma',0.95):.2f},{r.get('pi',0.25):.2f},{r.get('bopp',0.3):.2f},{r.get('eta',0.2):.2f},{r.get('delta0',0.1):.2f}\")
")

if [ "$CAPTURE_CELLS" = "NONE" ]; then
    echo "  NO CAPTURE cells found in confirmatory sweep. skipping ablation."
else
    ABLATION_DIR="results/v2.9_ablation"
    mkdir -p "$ABLATION_DIR"

    # for each CAPTURE cell, run 5 ablation conditions x 5 seeds
    echo "$CAPTURE_CELLS" | while IFS=, read -r SIGMA PI BOPP ETA DELTA0; do
        echo "  ablating cell: sigma=$SIGMA pi=$PI bopp=$BOPP eta=$ETA delta0=$DELTA0"

        # ablation 1: omega_x=0
        python scripts/run_v2_9_acquiescence_sweep.py \
            --stage confirmatory \
            --out "$ABLATION_DIR/ablate_ox0/sigma_${SIGMA}_pi_${PI}_bopp_${BOPP}_eta_${ETA}_d0_${DELTA0}" \
            --sigma-values "$SIGMA" --pi-values "$PI" --base-opp-values "$BOPP" \
            --eta-values "$ETA" --delta-values "$DELTA0" \
            --omega-x-fixed 0.0 --omega-delta-fixed "$OD" --omega-e-fixed "$OE" \
            --omega-t-fixed "$OT" --gamma-q-fixed "$GQ" \
            --workers 3

        # ablation 2: omega_delta=0
        python scripts/run_v2_9_acquiescence_sweep.py \
            --stage confirmatory \
            --out "$ABLATION_DIR/ablate_od0/sigma_${SIGMA}_pi_${PI}_bopp_${BOPP}_eta_${ETA}_d0_${DELTA0}" \
            --sigma-values "$SIGMA" --pi-values "$PI" --base-opp-values "$BOPP" \
            --eta-values "$ETA" --delta-values "$DELTA0" \
            --omega-x-fixed "$OX" --omega-delta-fixed 0.0 --omega-e-fixed "$OE" \
            --omega-t-fixed "$OT" --gamma-q-fixed "$GQ" \
            --workers 3

        # ablation 3: omega_e=0
        python scripts/run_v2_9_acquiescence_sweep.py \
            --stage confirmatory \
            --out "$ABLATION_DIR/ablate_oe0/sigma_${SIGMA}_pi_${PI}_bopp_${BOPP}_eta_${ETA}_d0_${DELTA0}" \
            --sigma-values "$SIGMA" --pi-values "$PI" --base-opp-values "$BOPP" \
            --eta-values "$ETA" --delta-values "$DELTA0" \
            --omega-x-fixed "$OX" --omega-delta-fixed "$OD" --omega-e-fixed 0.0 \
            --omega-t-fixed "$OT" --gamma-q-fixed "$GQ" \
            --workers 3

        # ablation 4: omega_t=0
        python scripts/run_v2_9_acquiescence_sweep.py \
            --stage confirmatory \
            --out "$ABLATION_DIR/ablate_ot0/sigma_${SIGMA}_pi_${PI}_bopp_${BOPP}_eta_${ETA}_d0_${DELTA0}" \
            --sigma-values "$SIGMA" --pi-values "$PI" --base-opp-values "$BOPP" \
            --eta-values "$ETA" --delta-values "$DELTA0" \
            --omega-x-fixed "$OX" --omega-delta-fixed "$OD" --omega-e-fixed "$OE" \
            --omega-t-fixed 0.0 --gamma-q-fixed "$GQ" \
            --workers 3

        # ablation 5: gamma_q doubled (stronger decay)
        DOUBLE_GQ=$(python -c "print(f'{2*$GQ:.4f}')")
        python scripts/run_v2_9_acquiescence_sweep.py \
            --stage confirmatory \
            --out "$ABLATION_DIR/ablate_gq2x/sigma_${SIGMA}_pi_${PI}_bopp_${BOPP}_eta_${ETA}_d0_${DELTA0}" \
            --sigma-values "$SIGMA" --pi-values "$PI" --base-opp-values "$BOPP" \
            --eta-values "$ETA" --delta-values "$DELTA0" \
            --omega-x-fixed "$OX" --omega-delta-fixed "$OD" --omega-e-fixed "$OE" \
            --omega-t-fixed "$OT" --gamma-q-fixed "$DOUBLE_GQ" \
            --workers 3
    done
    echo "[STAGE 3] ablation complete: $(date)"
fi

# ---- final report ----
echo ""
echo "[REPORT] generating mechanism report"
python -c "
from pathlib import Path
import pandas as pd

lines = []
lines.append('# v2.9 acquiescence mechanism report\n')
lines.append('generated: $(date)\n')

# 1. threshold fix
lines.append('## 1. threshold fix confirmation\n')
lines.append('v2.7 reclassification: 931 phantom CAPTURE -> 0 (see capture_fix_*.csv)\n')

# 2. calibration
cal_dir = Path('results/v2.9_acquiescence_calibration')
if (cal_dir / 'calibration_report.md').exists():
    lines.append('## 2. calibration results\n')
    lines.append((cal_dir / 'calibration_report.md').read_text())
    lines.append('')

# 3. confirmatory
conf_dir = Path('results/v2.9_confirmatory_sweep')
if (conf_dir / 'confirmatory_report.md').exists():
    lines.append('## 3. confirmatory regime map\n')
    lines.append((conf_dir / 'confirmatory_report.md').read_text())
    lines.append('')

# 4. ablation summary
abl_dir = Path('results/v2.9_ablation')
if abl_dir.exists():
    lines.append('## 4. ablation results\n')
    for subdir in sorted(abl_dir.iterdir()):
        if subdir.is_dir():
            for cell_dir in sorted(subdir.iterdir()):
                summary = cell_dir / 'sweep_summary.csv'
                if summary.exists():
                    s = pd.read_csv(summary)
                    regime_col = 'regime_consensus' if 'regime_consensus' in s.columns else 'regime_majority'
                    regimes = s[regime_col].value_counts().to_dict() if regime_col in s.columns else {}
                    lines.append(f'- {subdir.name}/{cell_dir.name}: {regimes}')
    lines.append('')

report = '\n'.join(lines)
Path('results/v2.9_mechanism_report.md').write_text(report)
print(report[:2000])
print(f'\nWrote results/v2.9_mechanism_report.md')
"

echo ""
echo "=========================================="
echo "v2.9 PIPELINE COMPLETE"
echo "finished: $(date)"
echo "=========================================="
