#!/usr/bin/env python3
"""validate that all expected publication figures exist and are non-empty."""

from pathlib import Path
import sys

FIGURES_DIR = Path("results/v2.5_corrected_three_regime_confirm/figures_publication")

# expected outputs from build_v2_5_publication_figures.py
EXPECTED = [
    "fig1_phase_map_hierarchical.png",
    "fig1_phase_map_hierarchical.pdf",
    "fig2_regime_counts.png",
    "fig2_regime_counts.pdf",
    "fig3_concentration_by_regime.png",
    "fig3_concentration_by_regime.pdf",
    "fig4_regime_timeseries.png",
    "fig4_regime_timeseries.pdf",
    "fig5_literalism_enrichment.png",
    "fig5_literalism_enrichment.pdf",
    "FIGURE_CAPTIONS.md",
]

# key input CSVs that must exist for figures to be reproducible
INPUT_CSVS = [
    "results/v2.5_corrected_three_regime_confirm/phase_bundle/phase_table.csv",
    "results/v2.5_corrected_three_regime_confirm/phase_bundle/regime_counts.csv",
    "results/v2.5_corrected_three_regime_confirm/phase_bundle/seed_regime_counts.csv",
    "results/v2.5_corrected_three_regime_confirm/sweep_seed_results.csv",
]


def main() -> int:
    errors = []

    # check input data
    for csv_path in INPUT_CSVS:
        p = Path(csv_path)
        if not p.exists():
            errors.append(f"MISSING input: {p}")
        elif p.stat().st_size == 0:
            errors.append(f"EMPTY input: {p}")

    # check output figures
    for name in EXPECTED:
        p = FIGURES_DIR / name
        if not p.exists():
            errors.append(f"MISSING figure: {p}")
        elif p.stat().st_size == 0:
            errors.append(f"EMPTY figure: {p}")

    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"VALIDATION PASSED: all {len(EXPECTED)} figures + {len(INPUT_CSVS)} inputs verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
