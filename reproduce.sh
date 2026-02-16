#!/usr/bin/env bash
# reproduce.sh -- regenerate publication figures from committed CSV data
# usage: ./reproduce.sh
# no simulation reruns; reads only from results/ CSVs
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

CONFIRM_DIR="results/v2.5_corrected_three_regime_confirm"
FIGURES_DIR="${CONFIRM_DIR}/figures_publication"
SWEEP_CSV="${CONFIRM_DIR}/sweep_seed_results.csv"

echo "=== code-geometry-abm: reproduce publication figures ==="
echo "repo root: ${REPO_ROOT}"

# --- step 1: set up venv if needed ---
if [ ! -d ".venv" ]; then
    echo "[1/4] creating virtual environment..."
    python3 -m venv .venv
else
    echo "[1/4] virtual environment exists, skipping creation"
fi

source .venv/bin/activate
echo "      python: $(python --version)"

# --- step 2: install deps ---
echo "[2/4] installing dependencies..."
pip install -q -r requirements.txt

# --- step 3: fix absolute paths in sweep_seed_results.csv ---
# the CSV contains absolute paths from the original machine; rebase to clone location
if grep -q "/storage/social-science/religion-code-geometry-abm" "$SWEEP_CSV" 2>/dev/null; then
    echo "[3/4] rebasing absolute paths in sweep_seed_results.csv..."
    sed -i "s|/storage/social-science/religion-code-geometry-abm|${REPO_ROOT}|g" "$SWEEP_CSV"
fi

# --- step 4: build figures ---
echo "[4/4] building publication figures..."
python scripts/build_v2_5_publication_figures.py \
    --root "$CONFIRM_DIR" \
    --outdir "$FIGURES_DIR"

echo ""
echo "=== validating outputs ==="
python scripts/validate_figures_from_csv.py

echo ""
echo "=== done ==="
echo "figures written to: ${FIGURES_DIR}/"
