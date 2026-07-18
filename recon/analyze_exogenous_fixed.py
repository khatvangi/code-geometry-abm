#!/usr/bin/env python3
"""Analyze the exogenous exit-closure test: broken vs fixed x legacy vs hierarchical.

Answers: does imposed exit-closure (exogenous delta) produce capture? The original
recon/exogenous_delta run said no, for two compounding reasons this script isolates:
  1. a wiring bug -- exogenous delta never closed the exit (fixed by the v2_7 patch;
     rerun lives in recon/exogenous_delta_fixed).
  2. the sweep's built-in classifier is LEGACY (requires belief prevalence >= 0.90),
     which never fires because belief stays ~0.13, masking enforcement-lock-in capture.

Under the canonical HIERARCHICAL schema (retained + active + concentrated, no belief
gate -- the manuscript's choice, regime_classifier.py) the fixed run shows a sharp
dose-response of capture vs imposed delta.

usage:
    .venv/bin/python recon/analyze_exogenous_fixed.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import regime_classifier as rc

BROKEN = ROOT / "recon/exogenous_delta/sweep_seed_results.csv"
FIXED = ROOT / "recon/exogenous_delta_fixed/sweep_seed_results.csv"
OUT_FIG = ROOT / "figures/v2_7_exogenous_dose_response.png"


def hier_capture_by_delta(path):
    df = pd.read_csv(path)
    df["regime_hier"] = [
        rc.classify(df["final_exit_rate"].iloc[i], df["max_punish"].iloc[i],
                    df["enforcer_punish_share"].iloc[i], schema="hierarchical")
        for i in range(len(df))
    ]
    cap = df.groupby("delta0")["regime_hier"].apply(lambda s: (s == "CAPTURE").mean())
    # median exit in enforcement-active cells (max_punish >= 0.10)
    act = df[df["max_punish"] >= 0.10]
    exit_by = act.groupby("delta0")["final_exit_rate"].median()
    return cap, exit_by, (df["regime_hier"] == "CAPTURE").mean()


def main():
    bc, be, btot = hier_capture_by_delta(BROKEN)
    fc, fe, ftot = hier_capture_by_delta(FIXED)

    print("=== capture rate vs exogenous delta0 (CANONICAL hierarchical schema) ===")
    tab = pd.DataFrame({"broken_capture": bc, "fixed_capture": fc}).round(3)
    print(tab.to_string())
    print(f"\noverall hierarchical capture: broken={btot:.3f}  fixed={ftot:.3f}")
    print("legacy schema (sweep default, belief>=0.90 gate): 0.000 in BOTH runs")

    plt.rcParams.update({"axes.grid": True, "grid.alpha": 0.3, "font.size": 12})
    fig, ax = plt.subplots(1, 2, figsize=(13, 5))

    # panel A: the patch -- exit vs imposed delta (broken flat, fixed collapses)
    ax[0].plot(be.index, be.values, "o--", color="#5a5a5a", label="broken (δ inert)")
    ax[0].plot(fe.index, fe.values, "o-", color="#003049", label="fixed (patch)")
    ax[0].axhline(0.20, ls=":", color="#c1121f", label="retention gate (0.20)")
    ax[0].set_xlabel("imposed exit-closure δ")
    ax[0].set_ylabel("median exit rate (enforcement-active cells)")
    ax[0].set_title("Patch: imposed δ now closes the exit")
    ax[0].legend(fontsize=10)

    # panel B: dose-response of capture vs delta (hierarchical), legacy flat at 0
    ax[1].plot(fc.index, fc.values, "o-", color="#780000", label="fixed, hierarchical")
    ax[1].plot(bc.index, bc.values, "o--", color="#adb5bd", label="broken, hierarchical")
    ax[1].axhline(0.0, ls=":", color="#5a5a5a", label="legacy schema (both runs)")
    ax[1].set_xlabel("imposed exit-closure δ")
    ax[1].set_ylabel("capture rate")
    ax[1].set_title("Closed exit → capture: sharp δ threshold")
    ax[1].legend(fontsize=10)

    fig.suptitle("Exogenous exit-closure test (v2.7, no acquiescence): retention alone drives hierarchical capture",
                 fontsize=13)
    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=150, bbox_inches="tight")
    print(f"\nwrote {OUT_FIG}")


if __name__ == "__main__":
    main()
