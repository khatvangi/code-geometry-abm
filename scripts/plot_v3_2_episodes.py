#!/usr/bin/env python3
"""Timeline figure for v3.2 endogenous episodic recurrence.

Shows fundamentalist episodes rising and falling on their own, driven by a
persistent (unchanging) book: grievance cycles, the exit seals and reopens, and
successive leaders seize the same latent exploit.

usage:
    .venv/bin/python scripts/plot_v3_2_episodes.py <metrics.csv> [out.png]
"""
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# note: repo deps are pinned and seaborn is not installed, so this uses matplotlib
# directly (consistent with the rest of the codebase) with a clean grid style.

def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "figures/v3_2_episodes_timeline.png"
    df = pd.read_csv(src)
    t = df["t"].values
    act = df["episode_active"].values
    edges = np.diff(np.concatenate([[0], act, [0]]))
    starts = np.where(edges == 1)[0]
    ends = np.where(edges == -1)[0]

    plt.rcParams.update({"axes.grid": True, "grid.alpha": 0.3, "font.size": 12})
    fig, ax = plt.subplots(2, 1, figsize=(13, 7), sharex=True)

    def shade(a):
        for s, e in zip(starts, ends):
            a.axvspan(t[s], t[min(e, len(t) - 1)], color="#c1121f", alpha=0.12, lw=0)

    # panel A: grievance reservoir + pushback threshold
    shade(ax[0])
    ax[0].plot(t, df["grievance"], color="#780000", lw=1.8, label="grievance")
    ax[0].axhline(0.60, ls="--", color="#5a5a5a", lw=1.2, label="pushback threshold")
    ax[0].set_ylabel("grievance")
    ax[0].legend(loc="upper right", fontsize=11, framealpha=0.9)
    ax[0].set_title("v3.2 endogenous episodic recurrence — the book (σ, π) is held constant throughout",
                    fontsize=14)

    # panel B: exit-sealing (delta) — episodes seal the exit, quiescence reopens it
    shade(ax[1])
    ax[1].plot(t, df["current_delta"], color="#003049", lw=1.8, label="exit-sealing (δ)")
    ax[1].set_ylabel("exit-seal δ")
    ax[1].set_xlabel("time step")
    ax[1].legend(loc="upper right", fontsize=11, framealpha=0.9)

    # mark leader id at each episode start
    for s in starts:
        lid = int(df["leader_id"].iloc[s])
        ax[0].annotate(f"L{lid}", (t[s], 0.92), fontsize=8, color="#c1121f",
                       ha="left", va="top", rotation=90)

    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"wrote {out}  ({len(starts)} episodes shaded)")

if __name__ == "__main__":
    main()
