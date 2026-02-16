#!/usr/bin/env python3
import argparse
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--capture-consensus", type=float, default=0.70)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    ss = pd.read_csv(root / "sweep_summary.csv")
    sr = pd.read_csv(root / "sweep_seed_results.csv")

    n_cells = len(ss)
    n_runs = len(sr)
    maj_counts = ss["regime_majority"].value_counts().to_dict()
    seed_counts = sr["regime"].value_counts().to_dict()

    # task criteria checks
    cutoff = (ss["n_seeds"] * args.capture_consensus).round().astype(int)
    capture_cons_cells = ss[
        (ss["n_capture"] >= cutoff)
        & (ss["delta0"].isin([0.1, 0.2]))
        & (ss["eta_delta_drift"] > 0.0)
        & (ss["sigma"] >= 0.75)
    ]

    sigma025_capture = ss[(ss["sigma"] == 0.25) & (ss["n_capture"] > 0)]
    eta0_lowdelta_capture = ss[
        (ss["eta_delta_drift"] == 0.0)
        & (ss["delta0"] <= 0.3)
        & (ss["n_capture"] > 0)
    ]

    # threshold view
    threshold_view = (
        ss.groupby(["delta0", "eta_delta_drift", "sigma", "pi_reward"], as_index=False)
        .agg(
            n_capture=("n_capture", "sum"),
            n_seeds=("n_seeds", "sum"),
            median_exit_rate=("median_exit_rate", "median"),
            median_final_delta=("median_final_delta", "median"),
            regime_majority=("regime_majority", lambda s: s.value_counts().index[0]),
        )
        .sort_values(["delta0", "eta_delta_drift", "sigma", "pi_reward"])
    )
    threshold_view.to_csv(root / "capture_threshold_view.csv", index=False)

    lines = [
        "# RESULTS_V2_7_ENDOGENOUS_DELTA",
        "",
        f"- n_cells: {n_cells}",
        f"- n_runs: {n_runs}",
        f"- majority_regimes: {maj_counts}",
        f"- seed_regimes: {seed_counts}",
        "",
        "## Success Criteria Checks",
        f"- low-delta capture cells (delta0 in {{0.1,0.2}}, eta>0, sigma>=0.75, >=70% capture seeds): {len(capture_cons_cells)}",
        f"- sigma=0.25 capture violations: {len(sigma025_capture)}",
        f"- eta=0 and delta0<=0.3 capture violations: {len(eta0_lowdelta_capture)}",
        "",
        "## Cells Meeting Low-Delta Capture Criterion",
        capture_cons_cells[[
            "eta_delta_drift",
            "delta0",
            "sigma",
            "pi_reward",
            "n_capture",
            "n_seeds",
            "median_exit_rate",
            "median_final_delta",
            "median_top5_share",
            "median_enforcer_punish_share",
            "regime_majority",
        ]].to_string(index=False) if not capture_cons_cells.empty else "none",
        "",
        "## Strongest Capture Candidates",
        ss.sort_values(["n_capture", "median_exit_rate"], ascending=[False, True]).head(15)[[
            "eta_delta_drift",
            "delta0",
            "sigma",
            "pi_reward",
            "n_capture",
            "n_seeds",
            "median_exit_rate",
            "median_final_delta",
            "median_top5_share",
            "median_enforcer_punish_share",
            "regime_majority",
        ]].to_string(index=False),
    ]

    out_md = root / "RESULTS_V2_7_ENDOGENOUS_DELTA.md"
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_md}")
    print(f"Wrote {root / 'capture_threshold_view.csv'}")


if __name__ == "__main__":
    main()
