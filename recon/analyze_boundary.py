#!/usr/bin/env python3
"""Map the activation/capture frontier in sigma x pi space (v2.7 exogenous).

Two panels, from the fine 9x7 boundary sweeps:
  LEFT  (open, delta=0):   where the enforcement apparatus FORMS (activates).
        activation rate = fraction of seeds with active enforcement (regime MIXED;
        open exit never captures, so MIXED == activated-but-not-retained).
  RIGHT (sealed, delta=0.95): where it HOLDS. capture rate = fraction CAPTURE.

Turns the earlier single dead corner into a mapped boundary: code geometry
(sigma x pi) sets whether the apparatus exists; exit capacity sets whether it
holds anyone. Each is necessary; capture needs the conjunction.

usage: .venv/bin/python recon/analyze_boundary.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OPEN = ROOT / "recon/boundary_open/sweep_seed_results.csv"
SEALED = ROOT / "recon/boundary_sealed/sweep_seed_results.csv"
OUT = ROOT / "figures/v2_7_activation_boundary.png"


def rate_grid(path, regime):
    df = pd.read_csv(path)
    g = (df.assign(hit=(df["regime"] == regime).astype(float))
           .groupby(["sigma", "pi_reward"])["hit"].mean().reset_index())
    piv = g.pivot(index="pi_reward", columns="sigma", values="hit").sort_index(ascending=False)
    return piv


def panel(ax, piv, title, cbar_label):
    im = ax.imshow(piv.values, aspect="auto", cmap="rocket" if "rocket" in plt.colormaps() else "magma",
                   vmin=0, vmax=1, origin="upper")
    ax.set_xticks(range(len(piv.columns)))
    ax.set_xticklabels([f"{c:.2f}" for c in piv.columns])
    ax.set_yticks(range(len(piv.index)))
    ax.set_yticklabels([f"{r:.2f}" for r in piv.index])
    ax.set_xlabel("code legibility  σ")
    ax.set_ylabel("enforcement reward  π")
    ax.set_title(title)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.values[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                    color="white" if v < 0.55 else "black", fontsize=8)
    return im


def main():
    act = rate_grid(OPEN, "MIXED")       # activation (open exit)
    cap = rate_grid(SEALED, "CAPTURE")   # capture (sealed exit)

    plt.rcParams.update({"font.size": 11})
    fig, ax = plt.subplots(1, 2, figsize=(15, 6))
    im0 = panel(ax[0], act, "Where the apparatus FORMS\n(open exit δ=0 · activation rate)", "activation")
    im1 = panel(ax[1], cap, "Where it HOLDS\n(sealed exit δ=0.95 · capture rate)", "capture")
    fig.colorbar(im1, ax=ax, fraction=0.025, pad=0.02, label="fraction of seeds")
    fig.suptitle("Activation × capture frontier in code-geometry space (v2.7): "
                 "geometry builds the apparatus, exit closure lets it hold",
                 fontsize=13)
    fig.savefig(OUT, dpi=150, bbox_inches="tight")

    # quantitative frontier summary
    print("=== activation (open) by sigma, averaged over pi ===")
    print(act.mean(axis=0).round(2).to_string())
    print("\n=== capture (sealed) by sigma, averaged over pi ===")
    print(cap.mean(axis=0).round(2).to_string())
    print("\n=== the former 'dead corner' region (low sigma, low pi) ===")
    lowcap = cap.loc[cap.index <= 0.05, cap.columns <= 0.25]
    print(f"capture in sigma<=0.25 & pi<=0.05: max={float(lowcap.values.max()):.2f} (should be ~0: no activation)")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
