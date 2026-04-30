#!/usr/bin/env python3
"""validate that all expected methodology-paper figures and inputs exist and are non-empty."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIGURES_DIR = REPO_ROOT / "figures"
SUBMISSION_DIR = REPO_ROOT / "figures" / "submission"
CANONICAL = REPO_ROOT / "results" / "v2.5_methodology_paper_canonical"

# expected outputs in figures/submission/ (manuscript-referenced)
EXPECTED_SUBMISSION = [
    "fig2_phase_map.pdf",
    "fig3_concentration.pdf",
    "fig6_regime_counts.pdf",
    "table6_regime_metrics.tex",
]
# expected outputs in figures/ (build artifacts, not in manuscript)
EXPECTED_BUILD_ARTIFACTS = [
    "figure4_trajectories.pdf",
]

# key input CSVs that must exist for figures to be reproducible
EXPECTED_INPUTS = [
    "sweep_seed_results.csv",
    "sweep_summary.csv",
    "phase_bundle/phase_table.csv",
    "phase_bundle/regime_counts.csv",
    "phase_bundle/seed_regime_counts.csv",
    "timeseries_regime_hier_QUIET.csv",
    "timeseries_regime_hier_MIXED.csv",
    "timeseries_regime_hier_COLLAPSE.csv",
    "timeseries_regime_hier_CAPTURE_HIERARCHICAL.csv",
]


def main() -> int:
    failures = []

    for name in EXPECTED_SUBMISSION:
        p = SUBMISSION_DIR / name
        if not p.exists():
            failures.append(f"  MISSING: {p.relative_to(REPO_ROOT)}")
        elif p.stat().st_size == 0:
            failures.append(f"  EMPTY: {p.relative_to(REPO_ROOT)}")

    for name in EXPECTED_BUILD_ARTIFACTS:
        p = FIGURES_DIR / name
        if not p.exists():
            failures.append(f"  MISSING: {p.relative_to(REPO_ROOT)}")
        elif p.stat().st_size == 0:
            failures.append(f"  EMPTY: {p.relative_to(REPO_ROOT)}")

    for rel in EXPECTED_INPUTS:
        p = CANONICAL / rel
        if not p.exists():
            failures.append(f"  MISSING: {p.relative_to(REPO_ROOT)}")
        elif p.stat().st_size == 0:
            failures.append(f"  EMPTY: {p.relative_to(REPO_ROOT)}")

    if failures:
        print("VALIDATION FAILED:")
        for f in failures:
            print(f)
        return 1

    n_figures = len(EXPECTED_SUBMISSION) + len(EXPECTED_BUILD_ARTIFACTS)
    print(
        f"VALIDATION PASSED: all {n_figures} figures + "
        f"{len(EXPECTED_INPUTS)} inputs verified"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
