#!/usr/bin/env bash
# reproduce.sh -- regenerate the methodology paper's canonical artifacts from
# committed CSV data and the immutable v2.5 confirmatory sweep run dirs.
# usage: ./reproduce.sh
# no simulation reruns; reads only metrics.csv / agent_summary.csv from
# results/v2.5_corrected_three_regime_confirm/ and rebuilds:
#   - results/v2.5_methodology_paper_canonical/         (deterministic)
#   - figures/figure{1..4}*.pdf                          (publication figures)
#   - figures/table5_regime_metrics.tex                  (regime-metrics table)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

LEGACY_DIR="results/v2.5_corrected_three_regime_confirm"
LEGACY_SWEEP_CSV="${LEGACY_DIR}/sweep_seed_results.csv"

echo "=== code-geometry-abm: reproduce methodology-paper figures ==="
echo "repo root: ${REPO_ROOT}"

# --- step 1: set up venv if needed ---
if [ ! -d ".venv" ]; then
    echo "[1/5] creating virtual environment..."
    python3 -m venv .venv
else
    echo "[1/5] virtual environment exists, skipping creation"
fi

source .venv/bin/activate
echo "      python: $(python --version)"

# --- step 2: install deps ---
echo "[2/5] installing dependencies..."
pip install -q -r requirements.txt

# --- step 3: rebase legacy absolute paths if needed (back-compat for legacy dir) ---
# the legacy frozen CSV contains absolute paths from the original run env.
# the new canonical pipeline does not need this rewrite (it writes repo-relative
# paths from the start); this step is preserved for the legacy directory only.
if grep -q "/storage/social-science/religion-code-geometry-abm" "$LEGACY_SWEEP_CSV" 2>/dev/null; then
    echo "[3/5] rebasing absolute paths in legacy ${LEGACY_SWEEP_CSV}..."
    echo "       (paths only -- numeric data unchanged; backup at .csv.bak)"
    cp "$LEGACY_SWEEP_CSV" "${LEGACY_SWEEP_CSV}.bak"
    sed -i "s|/storage/social-science/religion-code-geometry-abm|${REPO_ROOT}|g" "$LEGACY_SWEEP_CSV"
else
    echo "[3/5] legacy CSV already rebased or absent, skipping"
fi

# --- step 4: build canonical directory + figures ---
echo "[4/5] building canonical directory and methodology figures..."
python scripts/build_methodology_paper_canonical.py
python scripts/build_methodology_paper_figures.py

# --- step 5: validate ---
echo "[5/5] validating outputs..."
python scripts/validate_methodology_figures.py

echo ""
echo "=== done ==="
echo "canonical: results/v2.5_methodology_paper_canonical/"
echo "figures:   figures/figure{1..4}*.pdf, figures/table5_regime_metrics.tex"
