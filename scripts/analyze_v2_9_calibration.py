#!/usr/bin/env python3
"""analyze v2.9 stage 1 calibration results.

reads sweep_seed_results.csv and sweep_summary.csv from calibration sweep.
identifies which omega combos produce CAPTURE, parameter sensitivities,
and selects best calibration (robust CAPTURE with smallest omegas).

outputs calibration_report.md alongside results.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def main():
    if len(sys.argv) < 2:
        results_dir = Path("results/v2.9_acquiescence_calibration")
    else:
        results_dir = Path(sys.argv[1])

    seed_path = results_dir / "sweep_seed_results.csv"
    summary_path = results_dir / "sweep_summary.csv"

    if not seed_path.exists():
        print(f"ERROR: {seed_path} not found. run calibration sweep first.")
        sys.exit(1)

    seeds_df = pd.read_csv(seed_path)
    summary = pd.read_csv(summary_path)

    omega_cols = ["ox", "od", "oe", "ot", "gq"]
    # ensure columns exist
    for c in omega_cols:
        if c not in summary.columns:
            print(f"WARNING: column {c} not found in summary. available: {list(summary.columns)}")

    lines = []
    lines.append("# v2.9 acquiescence calibration report\n")

    # overview
    n_cells = len(summary)
    n_runs = len(seeds_df)
    lines.append(f"## overview\n")
    lines.append(f"- total cells: {n_cells}")
    lines.append(f"- total runs: {n_runs}")
    lines.append(f"- regime distribution (seeds): {seeds_df['regime'].value_counts().to_dict()}")
    if "regime_consensus" in summary.columns:
        lines.append(f"- regime distribution (consensus): {summary['regime_consensus'].value_counts().to_dict()}")
    lines.append("")

    # which omega combos produce CAPTURE?
    if "regime_consensus" in summary.columns:
        capture_cells = summary[summary["regime_consensus"] == "CAPTURE"]
    else:
        capture_cells = summary[summary["regime_majority"] == "CAPTURE"]

    lines.append(f"## CAPTURE cells\n")
    lines.append(f"- cells with CAPTURE consensus: {len(capture_cells)} / {n_cells}")
    if not capture_cells.empty:
        available_cols = [c for c in omega_cols if c in capture_cells.columns]
        lines.append(f"- omega ranges in CAPTURE cells:")
        for c in available_cols:
            vals = capture_cells[c].unique()
            lines.append(f"  - {c}: {sorted(vals)}")
        lines.append("")

        # show top CAPTURE cells by capture_prevalence
        if "median_capture_prevalence" in capture_cells.columns:
            top = capture_cells.nlargest(10, "median_capture_prevalence")
            lines.append("### top 10 CAPTURE cells by median_capture_prevalence\n")
            display_cols = available_cols + ["median_capture_prevalence", "median_mean_q", "median_fund_prevalence", "n_capture"]
            display_cols = [c for c in display_cols if c in top.columns]
            lines.append(top[display_cols].to_markdown(index=False))
            lines.append("")
    else:
        lines.append("- **NO CAPTURE cells found.** omega values may need widening.\n")

    # parameter sensitivity: for each omega, what fraction of cells are CAPTURE at each value?
    lines.append(f"## parameter sensitivity\n")
    available_cols = [c for c in omega_cols if c in summary.columns]
    regime_col = "regime_consensus" if "regime_consensus" in summary.columns else "regime_majority"
    for c in available_cols:
        lines.append(f"### {c}\n")
        pivot = summary.groupby(c)[regime_col].value_counts().unstack(fill_value=0)
        lines.append(pivot.to_markdown())
        lines.append("")

    # best calibration: smallest total omega that still produces CAPTURE
    lines.append(f"## best calibration (parsimony)\n")
    if not capture_cells.empty and available_cols:
        capture_cells = capture_cells.copy()
        capture_cells["omega_sum"] = capture_cells[available_cols].sum(axis=1)
        best = capture_cells.nsmallest(1, "omega_sum").iloc[0]
        lines.append("smallest-omega CAPTURE cell:")
        for c in available_cols:
            lines.append(f"  - {c}: {best[c]}")
        lines.append(f"  - omega_sum: {best['omega_sum']:.4f}")
        if "median_capture_prevalence" in best.index:
            lines.append(f"  - median_capture_prevalence: {best['median_capture_prevalence']:.4f}")
        if "median_mean_q" in best.index:
            lines.append(f"  - median_mean_q: {best['median_mean_q']:.4f}")
        lines.append("")

        # also report most robust (highest capture_prevalence)
        if "median_capture_prevalence" in capture_cells.columns:
            robust = capture_cells.nlargest(1, "median_capture_prevalence").iloc[0]
            lines.append("most robust CAPTURE cell:")
            for c in available_cols:
                lines.append(f"  - {c}: {robust[c]}")
            lines.append(f"  - median_capture_prevalence: {robust['median_capture_prevalence']:.4f}")
            lines.append("")
    else:
        lines.append("no CAPTURE cells to select from.\n")

    # non-CAPTURE regime analysis
    lines.append(f"## non-CAPTURE regimes\n")
    non_capture = summary[summary.get(regime_col, pd.Series()) != "CAPTURE"] if regime_col in summary.columns else summary
    if not non_capture.empty and "median_capture_prevalence" in non_capture.columns:
        lines.append(f"- median_capture_prevalence range in non-CAPTURE: "
                      f"({non_capture['median_capture_prevalence'].min():.4f}, "
                      f"{non_capture['median_capture_prevalence'].max():.4f})")
        lines.append(f"- median_mean_q range in non-CAPTURE: "
                      f"({non_capture['median_mean_q'].min():.4f}, "
                      f"{non_capture['median_mean_q'].max():.4f})")

    report = "\n".join(lines) + "\n"
    report_path = results_dir / "calibration_report.md"
    report_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nWrote {report_path}")


if __name__ == "__main__":
    main()
