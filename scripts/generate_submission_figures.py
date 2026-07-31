#!/usr/bin/env python3
"""Generate 5 publication-quality figures from confirmatory ABM data.

Figures:
  1. Dose-response curves (enforcement metrics vs sigma)
  2. Hierarchical phase map (72-cell grid)
  3. Punishment concentration by regime (box plots)
  4. Representative time-series trajectories per regime
  5. Retention mechanism comparison (monopoly ablation + cadre quota)

Usage:
  python scripts/generate_submission_figures.py
  python scripts/generate_submission_figures.py --data results/v2.5_corrected_three_regime_confirm --outdir figures/submission
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

# ---------------------------------------------------------------------------
# palette -- four colors only, no blue, no green
# ---------------------------------------------------------------------------
COLORS = {
    "QUIET":                  "#E8D5B7",  # sand
    "MIXED":                  "#D4764E",  # burnt sienna
    "CAPTURE_HIERARCHICAL":   "#8B2F4A",  # deep wine
    "COLLAPSE":               "#2D2D2D",  # charcoal
}
# short labels for display
LABELS = {
    "QUIET":                  "Quiet",
    "MIXED":                  "Mixed",
    "CAPTURE_HIERARCHICAL":   "Capture",
    "COLLAPSE":               "Collapse",
}
REGIME_ORDER = ["QUIET", "MIXED", "CAPTURE_HIERARCHICAL", "COLLAPSE"]


def apply_style() -> None:
    """set publication rc params."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.linewidth": 0.8,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def save(fig: plt.Figure, outdir: Path, stem: str) -> None:
    """save figure as pdf and png."""
    outdir.mkdir(parents=True, exist_ok=True)
    fig.savefig(outdir / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(outdir / f"{stem}.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"  saved {stem}.pdf / .png")


# ===================================================================
# figure 1 -- dose-response curves
# ===================================================================
def fig1_dose_response(root: Path, outdir: Path) -> None:
    """dose-response: enforcement metrics vs sigma.

    uses results/dose_response/ if available (10 sigma values, drift_on only).
    columns: sigma, pi_reward, drift_condition, pct_active,
             median_enforcer_share, median_exit_rate, median_final_delta
    """
    dr_path = root.parent / "dose_response" / "summary.csv"
    if dr_path.exists():
        df = pd.read_csv(dr_path)
        # keep drift_on only for cleaner picture
        df = df[df["drift_condition"] == "drift_on"].copy()
    else:
        # fallback: group confirmatory sweep by sigma
        seed = pd.read_csv(root / "sweep_seed_results.csv")
        df = (
            seed
            .groupby("sigma")
            .agg(
                pct_active=("regime_hier",
                            lambda s: 100 * (s != "QUIET").mean()),
                median_enforcer_share=("enforcer_punish_share", "median"),
                median_exit_rate=("final_exit_rate", "median"),
                median_final_delta=("max_punish", "median"),
            )
            .reset_index()
        )
        # add a dummy pi_reward for the panel loop
        df["pi_reward"] = "all"

    pi_vals = sorted(df["pi_reward"].unique())

    fig, axes = plt.subplots(1, 4, figsize=(14, 3.2), sharey=False)
    panel_labels = ["A", "B", "C", "D"]
    titles = [
        "enforcement activation (%)",
        "enforcer punishment share",
        "exit rate",
        r"final $\delta$ (max punish)",
    ]
    y_cols = [
        "pct_active",
        "median_enforcer_share",
        "median_exit_rate",
        "median_final_delta",
    ]

    # use two palette entries for the two pi_reward levels
    pi_colors = {
        pi_vals[0]: COLORS["MIXED"],       # burnt sienna
    }
    if len(pi_vals) > 1:
        pi_colors[pi_vals[1]] = COLORS["CAPTURE_HIERARCHICAL"]  # deep wine

    for ax, label, title, ycol in zip(axes, panel_labels, titles, y_cols):
        for pi in pi_vals:
            sub = df[df["pi_reward"] == pi].sort_values("sigma")
            ax.plot(
                sub["sigma"], sub[ycol],
                marker="o", markersize=4, linewidth=1.4,
                color=pi_colors.get(pi, COLORS["MIXED"]),
                label=f"$\\pi_r$={pi}",
            )
        ax.set_xlabel(r"$\sigma$")
        ax.set_title(f"{label})  {title}", loc="left", fontsize=10)
        if len(pi_vals) > 1:
            ax.legend(frameon=False, fontsize=8)

    fig.tight_layout(w_pad=2.5)
    save(fig, outdir, "fig1_dose_response")


# ===================================================================
# figure 2 -- phase map (72 cells)
# ===================================================================
def fig2_phase_map(root: Path, outdir: Path) -> None:
    """hierarchical phase map.

    rows = sigma (3), cols = base_opp (4).
    faceted by pi_reward x exit_threshold (3 x 2 = 6 panels).
    cell colour = majority regime.
    """
    sm = pd.read_csv(root / "sweep_summary.csv")

    pi_vals = sorted(sm["pi_reward"].unique())
    exit_vals = sorted(sm["exit_threshold"].unique())
    sigma_vals = sorted(sm["sigma"].unique())
    opp_vals = sorted(sm["base_opp"].unique())

    n_pi = len(pi_vals)
    n_exit = len(exit_vals)

    fig, axes = plt.subplots(
        n_exit, n_pi,
        figsize=(3.0 * n_pi + 0.8, 2.8 * n_exit + 0.6),
        squeeze=False,
    )

    # colour map keyed by regime name
    regime_to_idx = {r: i for i, r in enumerate(REGIME_ORDER)}
    cmap = ListedColormap([COLORS[r] for r in REGIME_ORDER])

    for ei, et in enumerate(exit_vals):
        for pi_i, pi in enumerate(pi_vals):
            ax = axes[ei, pi_i]
            sub = sm[(sm["exit_threshold"] == et) & (sm["pi_reward"] == pi)]

            # build grid: sigma on y, base_opp on x
            grid = np.full((len(sigma_vals), len(opp_vals)), np.nan)
            for _, row in sub.iterrows():
                si = sigma_vals.index(row["sigma"])
                oi = opp_vals.index(row["base_opp"])
                grid[si, oi] = regime_to_idx.get(
                    row["regime_majority_hier"], 0
                )

            ax.imshow(
                grid, cmap=cmap, vmin=0, vmax=len(REGIME_ORDER) - 1,
                aspect="auto", origin="lower",
            )
            ax.set_xticks(range(len(opp_vals)))
            ax.set_xticklabels([f"{v}" for v in opp_vals], fontsize=8)
            ax.set_yticks(range(len(sigma_vals)))
            ax.set_yticklabels([f"{v}" for v in sigma_vals], fontsize=8)
            ax.set_xlabel("base_opp", fontsize=8)
            ax.set_ylabel(r"$\sigma$", fontsize=8)
            ax.set_title(
                f"$\\pi_r$={pi}, exit={et}",
                fontsize=9,
            )

    # shared legend
    patches = [
        Patch(facecolor=COLORS[r], edgecolor="k", linewidth=0.5,
              label=LABELS[r])
        for r in REGIME_ORDER
    ]
    fig.legend(
        handles=patches, loc="lower center",
        ncol=4, frameon=False, fontsize=9,
        bbox_to_anchor=(0.5, -0.04),
    )
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    save(fig, outdir, "fig2_phase_map")


# ===================================================================
# figure 3 -- punishment concentration by regime
# ===================================================================
def fig3_concentration(root: Path, outdir: Path) -> None:
    """box plots of concentration metrics by regime."""
    df = pd.read_csv(root / "sweep_seed_results.csv")

    metrics = [
        ("top5_punishment_share", "top-5 punishment share"),
        ("final_exit_rate",       "exit rate"),
        ("enforcer_punish_share", "enforcer punishment share"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))
    panel_labels = ["A", "B", "C"]

    for ax, (col, nice), lab in zip(axes, metrics, panel_labels):
        data_by_regime = []
        positions = []
        colors_list = []
        tick_labels = []
        for i, regime in enumerate(REGIME_ORDER):
            vals = df.loc[df["regime_hier"] == regime, col].dropna()
            if len(vals) == 0:
                continue
            data_by_regime.append(vals.values)
            positions.append(i)
            colors_list.append(COLORS[regime])
            tick_labels.append(LABELS[regime])

        bp = ax.boxplot(
            data_by_regime, positions=positions, widths=0.55,
            patch_artist=True, showfliers=False,
            medianprops=dict(color="white", linewidth=1.2),
            whiskerprops=dict(linewidth=0.8),
            capprops=dict(linewidth=0.8),
        )
        for patch, c in zip(bp["boxes"], colors_list):
            patch.set_facecolor(c)
            patch.set_edgecolor("k")
            patch.set_linewidth(0.6)

        ax.set_xticks(positions)
        ax.set_xticklabels(tick_labels, fontsize=9)
        ax.set_title(f"{lab})  {nice}", loc="left", fontsize=10)
        ax.set_ylim(-0.02, 1.05)

    fig.tight_layout(w_pad=2.5)
    save(fig, outdir, "fig3_concentration")


# ===================================================================
# figure 4 -- representative trajectories
# ===================================================================
def fig4_trajectories(root: Path, outdir: Path) -> None:
    """time-series for one representative run per regime.

    reads timeseries_regime_hier_*.csv from the confirmatory folder.
    each panel: fund_prevalence, exit_rate, punish_rate vs timestep.
    """
    fig, axes = plt.subplots(2, 2, figsize=(10, 6.5), sharex=True)
    axes_flat = axes.flat
    panel_labels = ["A", "B", "C", "D"]

    line_styles = {
        "fund_prevalence":          ("-",  "fund prevalence"),
        "exit_rate":                ("--", "exit rate"),
        "punish_rate":              (":",  "punish rate"),
    }
    # use charcoal-ish tones for lines within each panel
    line_colors = {
        "fund_prevalence":          COLORS["COLLAPSE"],           # charcoal
        "exit_rate":                COLORS["CAPTURE_HIERARCHICAL"],  # deep wine
        "punish_rate":              COLORS["MIXED"],              # burnt sienna
    }

    for ax, regime, lab in zip(axes_flat, REGIME_ORDER, panel_labels):
        ts_path = root / f"timeseries_regime_hier_{regime}.csv"
        if not ts_path.exists():
            ax.text(0.5, 0.5, "no data", transform=ax.transAxes,
                    ha="center", va="center")
            ax.set_title(f"{lab})  {LABELS[regime]}", loc="left", fontsize=10)
            continue

        ts = pd.read_csv(ts_path)
        # pick first seed available
        first_seed = ts["seed"].iloc[0]
        one = ts[ts["seed"] == first_seed].sort_values("t")

        for metric, (ls, nice) in line_styles.items():
            if metric not in one.columns:
                continue
            ax.plot(
                one["t"], one[metric],
                linestyle=ls, linewidth=1.2,
                color=line_colors[metric],
                label=nice,
            )

        ax.set_title(f"{lab})  {LABELS[regime]}", loc="left", fontsize=10,
                     color=COLORS[regime])
        ax.set_ylim(-0.02, 1.05)
        ax.set_xlabel("timestep")

    # single shared legend
    handles = [
        plt.Line2D([], [], linestyle=ls, color=line_colors[m],
                   linewidth=1.2, label=nice)
        for m, (ls, nice) in line_styles.items()
    ]
    fig.legend(
        handles=handles, loc="lower center", ncol=3,
        frameon=False, fontsize=9, bbox_to_anchor=(0.5, -0.02),
    )
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    save(fig, outdir, "fig4_trajectories")


# ===================================================================
# figure 5 -- retention mechanism (monopoly + quota ablation)
# ===================================================================
def fig5_retention(root: Path, outdir: Path) -> None:
    """retention-mechanism comparison.

    panel A: monopoly ON vs OFF -- concentration metrics (grouped bar)
    panel B: cadre quota sensitivity -- top5_share vs quota fraction
    """
    results_root = root.parent  # results/

    mono_path = results_root / "ablation_monopoly_comparison.csv"
    quota_path = results_root / "ablation_quota" / "summary_by_quota.csv"

    has_mono = mono_path.exists()
    has_quota = quota_path.exists()

    if not has_mono and not has_quota:
        # fallback: simple bar from confirmatory sweep
        print("  [fig5] no ablation data found; skipping figure 5")
        return

    n_panels = int(has_mono) + int(has_quota)
    fig, axes = plt.subplots(1, n_panels, figsize=(5.5 * n_panels, 3.5))
    if n_panels == 1:
        axes = [axes]
    ax_idx = 0

    # -- panel A: monopoly ablation -----------------------------------------
    if has_mono:
        ax = axes[ax_idx]; ax_idx += 1
        mono = pd.read_csv(mono_path)

        # pick one representative (sigma, pi_reward, base_opp) combo
        # show on vs off for median_top5_share, median_enforcer_share, median_exit_rate
        metrics = ["median_top5_share", "median_enforcer_share", "median_exit_rate"]
        nice_names = ["top-5 share", "enforcer share", "exit rate"]

        # aggregate across all param combos
        agg = mono.groupby("condition")[metrics].median().reindex(["off", "on"])

        x = np.arange(len(metrics))
        bar_w = 0.3
        bar_colors = [COLORS["QUIET"], COLORS["CAPTURE_HIERARCHICAL"]]
        for i, cond in enumerate(["off", "on"]):
            vals = agg.loc[cond, metrics].values
            ax.bar(x + i * bar_w, vals, bar_w,
                   color=bar_colors[i], edgecolor="k", linewidth=0.5,
                   label=f"monopoly {cond}")

        ax.set_xticks(x + bar_w / 2)
        ax.set_xticklabels(nice_names, fontsize=9)
        ax.set_ylim(0, 1.05)
        ax.legend(frameon=False, fontsize=8)
        ax.set_title("A)  monopoly ON vs OFF", loc="left", fontsize=10)

    # -- panel B: cadre quota sensitivity -----------------------------------
    if has_quota:
        ax = axes[ax_idx]; ax_idx += 1
        quota = pd.read_csv(quota_path).sort_values("enforcer_quota_frac")

        ax.plot(
            quota["enforcer_quota_frac"], quota["median_top5_share"],
            marker="o", markersize=5, linewidth=1.4,
            color=COLORS["CAPTURE_HIERARCHICAL"], label="top-5 share",
        )
        ax.plot(
            quota["enforcer_quota_frac"], quota["median_enforcer_share"],
            marker="s", markersize=5, linewidth=1.4,
            linestyle="--", color=COLORS["MIXED"], label="enforcer share",
        )
        ax.plot(
            quota["enforcer_quota_frac"], quota["median_exit_rate"],
            marker="^", markersize=5, linewidth=1.4,
            linestyle=":", color=COLORS["COLLAPSE"], label="exit rate",
        )

        ax.set_xlabel("enforcer quota fraction")
        ax.set_ylim(0, 1.05)
        ax.legend(frameon=False, fontsize=8)
        label = "B)" if has_mono else "A)"
        ax.set_title(f"{label}  cadre quota sensitivity", loc="left",
                     fontsize=10)

    fig.tight_layout(w_pad=3)
    save(fig, outdir, "fig5_retention")


# ===================================================================
# main
# ===================================================================
def main() -> None:
    parser = argparse.ArgumentParser(
        description="generate 5 submission figures from confirmatory data"
    )
    parser.add_argument(
        "--data", type=str,
        default="results/v2.5_corrected_three_regime_confirm",
        help="path to confirmatory results directory",
    )
    parser.add_argument(
        "--outdir", type=str,
        default="figures/submission",
        help="output directory for PDFs",
    )
    args = parser.parse_args()

    root = Path(args.data)
    outdir = Path(args.outdir)

    if not root.exists():
        raise FileNotFoundError(f"data directory not found: {root}")

    apply_style()
    print(f"data   : {root.resolve()}")
    print(f"outdir : {outdir.resolve()}")
    print()

    print("figure 1 -- dose-response curves")
    fig1_dose_response(root, outdir)

    print("figure 2 -- phase map")
    fig2_phase_map(root, outdir)

    print("figure 3 -- concentration by regime")
    fig3_concentration(root, outdir)

    print("figure 4 -- trajectories")
    fig4_trajectories(root, outdir)

    print("figure 5 -- retention mechanism")
    fig5_retention(root, outdir)

    print()
    generated = list(outdir.glob("fig*.pdf"))
    print(f"done. {len(generated)} PDF figures in {outdir.resolve()}/")
    for p in sorted(generated):
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
