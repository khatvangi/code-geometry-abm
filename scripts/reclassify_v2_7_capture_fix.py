#!/usr/bin/env python3
"""reclassify v2.7 sweep results with corrected CAPTURE threshold (0.90).

the original sweep scripts had threshold 0.10 instead of 0.90, producing
465 phantom CAPTURE runs. the threshold bug is already fixed in all 8
sweep scripts. this script reclassifies existing result CSVs without
re-running any simulations.

outputs:
  capture_fix_seed_results.csv   - per-seed reclassified regimes
  capture_fix_summary.csv        - per-cell summary with corrected counts
"""
import math
from pathlib import Path

import numpy as np
import pandas as pd

REGIME_ORDER = ["COLLAPSE", "CAPTURE", "MIXED", "QUIET"]
CAPTURE_EXIT_CAP = 0.20  # matches sweep default


def classify_regime(exit_rate: float, prevalence: float, max_punish: float) -> str:
    """classify with corrected 0.90 threshold."""
    if exit_rate >= 0.90:
        return "COLLAPSE"
    # corrected threshold: 0.90, not 0.10
    if prevalence >= 0.90 and exit_rate <= CAPTURE_EXIT_CAP:
        return "CAPTURE"
    if max_punish >= 0.10:
        return "MIXED"
    return "QUIET"


def majority_regime(s: pd.Series) -> str:
    vc = s.value_counts()
    if vc.empty:
        return "QUIET"
    topn = vc.max()
    tied = sorted([k for k, n in vc.items() if n == topn], key=lambda x: REGIME_ORDER.index(x))
    return tied[0]


def reclassify_directory(results_dir: Path):
    seed_path = results_dir / "sweep_seed_results.csv"
    if not seed_path.exists():
        print(f"  SKIP: {seed_path} not found")
        return

    df = pd.read_csv(seed_path)
    n_original = len(df)
    original_capture = int((df["regime"] == "CAPTURE").sum())

    # reclassify each row
    df["regime"] = df.apply(
        lambda r: classify_regime(r["final_exit_rate"], r["final_fund_prevalence"], r["max_punish"]),
        axis=1,
    )
    new_capture = int((df["regime"] == "CAPTURE").sum())

    # save reclassified seed results
    out_seed = results_dir / "capture_fix_seed_results.csv"
    df.to_csv(out_seed, index=False)

    # build summary (same logic as sweep script)
    gcols = ["eta_delta_drift", "delta0", "sigma", "pi_reward", "alpha", "mu_membership_reward"]
    rows = []
    for keys, g in df.groupby(gcols):
        eta, delta0, sigma, pi, alpha, mu = keys
        rows.append({
            "eta_delta_drift": float(eta),
            "delta0": float(delta0),
            "sigma": float(sigma),
            "pi_reward": float(pi),
            "alpha": float(alpha),
            "mu_membership_reward": float(mu),
            "n_seeds": int(len(g)),
            "regime_majority": majority_regime(g["regime"]),
            "n_collapse": int((g["regime"] == "COLLAPSE").sum()),
            "n_capture": int((g["regime"] == "CAPTURE").sum()),
            "n_mixed": int((g["regime"] == "MIXED").sum()),
            "n_quiet": int((g["regime"] == "QUIET").sum()),
            "median_fund_prevalence": float(g["final_fund_prevalence"].median()),
            "median_exit_rate": float(g["final_exit_rate"].median()),
            "median_top5_share": float(g["top5_punishment_share"].median()),
            "median_max_punish": float(g["max_punish"].median()),
            "median_enforcer_punish_share": float(g["enforcer_punish_share"].median()),
            "median_final_delta": float(g["final_current_delta"].median()),
        })
    summary = pd.DataFrame(rows).sort_values(gcols)
    out_summary = results_dir / "capture_fix_summary.csv"
    summary.to_csv(out_summary, index=False)

    print(f"  {results_dir.name}:")
    print(f"    rows={n_original}  CAPTURE_before={original_capture}  CAPTURE_after={new_capture}")
    print(f"    -> {out_seed.name}")
    print(f"    -> {out_summary.name}")


def main():
    base = Path(__file__).resolve().parent.parent / "results"
    dirs = [
        base / "v2.7_endogenous_delta_sweep",
        base / "v2.7b_endogenous_delta_sweep_gated",
    ]

    print("reclassifying v2.7 results with corrected CAPTURE threshold (>= 0.90)\n")
    for d in dirs:
        reclassify_directory(d)

    print("\nconfirmation: CAPTURE should be 0 across all runs (fund_prevalence never reaches 0.90)")


if __name__ == "__main__":
    main()
