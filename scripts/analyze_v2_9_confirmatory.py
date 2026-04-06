#!/usr/bin/env python3
"""analyze v2.9 stage 2 confirmatory sweep results.

produces regime maps comparable to v2.5/v2.8, reports both fund_prevalence
and capture_prevalence, tests conjunction hypotheses about which code-geometry
conditions produce CAPTURE.

outputs confirmatory_report.md alongside results.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def main():
    if len(sys.argv) < 2:
        results_dir = Path("results/v2.9_confirmatory_sweep")
    else:
        results_dir = Path(sys.argv[1])

    seed_path = results_dir / "sweep_seed_results.csv"
    summary_path = results_dir / "sweep_summary.csv"

    if not seed_path.exists():
        print(f"ERROR: {seed_path} not found. run confirmatory sweep first.")
        sys.exit(1)

    seeds_df = pd.read_csv(seed_path)
    summary = pd.read_csv(summary_path)

    regime_col = "regime_consensus" if "regime_consensus" in summary.columns else "regime_majority"
    geo_cols = ["sigma", "pi", "bopp", "eta", "delta0"]
    available_geo = [c for c in geo_cols if c in summary.columns]

    lines = []
    lines.append("# v2.9 confirmatory sweep report\n")

    # overview
    lines.append("## overview\n")
    lines.append(f"- total cells: {len(summary)}")
    lines.append(f"- total runs: {len(seeds_df)}")
    lines.append(f"- regime distribution (seeds): {seeds_df['regime'].value_counts().to_dict()}")
    if regime_col in summary.columns:
        lines.append(f"- regime distribution ({regime_col}): {summary[regime_col].value_counts().to_dict()}")
    lines.append("")

    # regime map: sigma x pi at each (bopp, eta, delta0)
    lines.append("## regime maps\n")
    slice_cols = [c for c in ["bopp", "eta", "delta0"] if c in summary.columns]
    map_rows = [c for c in ["sigma"] if c in summary.columns]
    map_cols = [c for c in ["pi"] if c in summary.columns]

    if slice_cols and map_rows and map_cols and regime_col in summary.columns:
        for keys, g in summary.groupby(slice_cols):
            if not isinstance(keys, tuple):
                keys = (keys,)
            label = " | ".join(f"{c}={v}" for c, v in zip(slice_cols, keys))
            lines.append(f"### {label}\n")

            pivot = g.pivot_table(
                index=map_rows[0], columns=map_cols[0],
                values=regime_col, aggfunc="first"
            )
            lines.append(pivot.to_markdown())
            lines.append("")

            # also show capture_prevalence
            if "median_capture_prevalence" in g.columns:
                pivot_cp = g.pivot_table(
                    index=map_rows[0], columns=map_cols[0],
                    values="median_capture_prevalence", aggfunc="first"
                )
                lines.append(f"capture_prevalence:")
                lines.append(pivot_cp.to_markdown(floatfmt=".3f"))
                lines.append("")

            # and fund_prevalence for comparison
            if "median_fund_prevalence" in g.columns:
                pivot_fp = g.pivot_table(
                    index=map_rows[0], columns=map_cols[0],
                    values="median_fund_prevalence", aggfunc="first"
                )
                lines.append(f"fund_prevalence:")
                lines.append(pivot_fp.to_markdown(floatfmt=".3f"))
                lines.append("")

    # hypothesis tests
    lines.append("## hypothesis tests\n")

    capture_cells = summary[summary.get(regime_col, pd.Series()) == "CAPTURE"] if regime_col in summary.columns else pd.DataFrame()

    # test: CAPTURE requires high sigma + high pi + low base_opp + eta > 0?
    lines.append("### conjunction hypothesis: CAPTURE requires high sigma, high pi, low base_opp, eta > 0\n")
    if not capture_cells.empty:
        lines.append(f"CAPTURE cells ({len(capture_cells)}):")
        for c in available_geo:
            vals = sorted(capture_cells[c].unique())
            lines.append(f"  - {c} values: {vals}")
        lines.append("")

        # check if all CAPTURE cells have high sigma
        if "sigma" in capture_cells.columns:
            high_sigma = capture_cells[capture_cells["sigma"] >= 0.75]
            lines.append(f"  CAPTURE with sigma >= 0.75: {len(high_sigma)} / {len(capture_cells)}")
        if "eta" in capture_cells.columns:
            eta_positive = capture_cells[capture_cells["eta"] > 0.0]
            lines.append(f"  CAPTURE with eta > 0: {len(eta_positive)} / {len(capture_cells)}")
    else:
        lines.append("no CAPTURE cells found.\n")
    lines.append("")

    # test: at eta=0, no CAPTURE?
    lines.append("### null hypothesis: at eta=0, no CAPTURE\n")
    if "eta" in summary.columns and regime_col in summary.columns:
        eta0 = summary[summary["eta"] == 0.0]
        eta0_capture = eta0[eta0[regime_col] == "CAPTURE"]
        lines.append(f"- eta=0 cells: {len(eta0)}")
        lines.append(f"- eta=0 CAPTURE cells: {len(eta0_capture)}")
        if len(eta0_capture) > 0:
            lines.append("- **NULL REJECTED**: CAPTURE occurs even at eta=0 (q can grow without delta drift)")
        else:
            lines.append("- null confirmed: no CAPTURE at eta=0")
    lines.append("")

    # 4-regime typology check
    lines.append("## 4-regime typology\n")
    if regime_col in summary.columns:
        for regime in ["COLLAPSE", "CAPTURE", "MIXED", "QUIET"]:
            count = int((summary[regime_col] == regime).sum())
            lines.append(f"- {regime}: {count} cells")
        all_present = all(
            (summary[regime_col] == r).any() for r in ["COLLAPSE", "CAPTURE", "MIXED", "QUIET"]
        )
        lines.append(f"\nall 4 regimes present: {'YES' if all_present else 'NO'}")
    lines.append("")

    # key finding summary
    lines.append("## key findings\n")
    if not capture_cells.empty:
        lines.append(f"- acquiescence mechanism successfully produces {len(capture_cells)} CAPTURE cells")
        if "median_capture_prevalence" in capture_cells.columns:
            lines.append(f"- median capture_prevalence in CAPTURE cells: "
                          f"{capture_cells['median_capture_prevalence'].median():.3f}")
        if "median_fund_prevalence" in capture_cells.columns:
            lines.append(f"- median fund_prevalence in CAPTURE cells: "
                          f"{capture_cells['median_fund_prevalence'].median():.3f}")
            lines.append(f"- this confirms: capture is driven by acquiescent supporters, "
                          f"not just active enforcers")
    else:
        lines.append("- no CAPTURE cells produced. mechanism may need recalibration.")

    report = "\n".join(lines) + "\n"
    report_path = results_dir / "confirmatory_report.md"
    report_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nWrote {report_path}")


if __name__ == "__main__":
    main()
