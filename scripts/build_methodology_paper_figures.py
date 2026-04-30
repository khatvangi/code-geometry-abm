#!/usr/bin/env python3
"""build_methodology_paper_figures.py

reads from results/v2.5_methodology_paper_canonical/ and produces the
methodology paper's figures and table:
  figures/submission/fig2_phase_map.pdf       manuscript Figure 2 (phase map)
  figures/submission/fig3_concentration.pdf   manuscript Figure 3 (concentration)
  figures/submission/fig6_regime_counts.pdf   manuscript Figure 6 (NEW, regime counts)
  figures/submission/table6_regime_metrics.tex  manuscript Table 6 (regime metrics)
  figures/figure4_trajectories.pdf            build artifact (per-regime mean trajectories);
                                              not referenced by manuscript.tex

manuscript Figures 1, 4, 5 come from other pipelines (dose-response sweep,
drift sweep, retention sweep) and are not regenerated here.

choice of plotting library: matplotlib only. the project's pinned requirements.txt
does not include seaborn, and adding a dep here would change the reproducibility
graph. matches the existing scripts/build_v2_5_publication_figures.py convention.

run from repo root: python scripts/build_methodology_paper_figures.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL = REPO_ROOT / "results" / "v2.5_methodology_paper_canonical"
FIG_DIR = REPO_ROOT / "figures"  # build-artifact-only outputs (not referenced by manuscript)
SUBMISSION_DIR = REPO_ROOT / "figures" / "submission"  # manuscript-referenced outputs

REGIME_ORDER_HIER = ["QUIET", "MIXED", "COLLAPSE", "CAPTURE_HIERARCHICAL"]
REGIME_COLORS = {
    "QUIET": "#bdbdbd",
    "MIXED": "#4daf4a",
    "COLLAPSE": "#377eb8",
    "CAPTURE_HIERARCHICAL": "#ff7f00",
}
REGIME_SHORT = {
    "QUIET": "Q",
    "MIXED": "M",
    "COLLAPSE": "X",
    "CAPTURE_HIERARCHICAL": "CH",
}
DISPLAY_LABEL = {
    "QUIET": "QUIET",
    "MIXED": "MIXED",
    "COLLAPSE": "COLLAPSE",
    "CAPTURE_HIERARCHICAL": "CAPTURE",
}


def savePdf(fig, name: str, submission: bool = True):
    """save a figure as PDF.

    submission=True writes to figures/submission/ (manuscript-referenced path).
    submission=False writes to figures/ (build artifact only, not in manuscript).
    """
    target = SUBMISSION_DIR if submission else FIG_DIR
    target.mkdir(parents=True, exist_ok=True)
    outpath = target / name
    fig.savefig(outpath, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {outpath.relative_to(REPO_ROOT)}")


def plotPhaseMap(phase_table: pd.DataFrame):
    """6-panel phase map: 3 pi_reward (cols) x 2 exit_threshold (rows).
    each panel: sigma (rows) x base_opp (cols) heatmap, regime as color, label per cell."""
    pis = sorted(phase_table["pi_reward"].unique())
    exits = sorted(phase_table["exit_threshold"].unique())
    sigmas = sorted(phase_table["sigma"].unique())
    opps = sorted(phase_table["base_opp"].unique())

    nrows = len(exits)
    ncols = len(pis)
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(3.6 * ncols, 3.0 * nrows), squeeze=False
    )

    cmap = ListedColormap([REGIME_COLORS[r] for r in REGIME_ORDER_HIER])
    norm = BoundaryNorm(np.arange(-0.5, len(REGIME_ORDER_HIER) + 0.5, 1), cmap.N)
    code = {r: i for i, r in enumerate(REGIME_ORDER_HIER)}

    for r, exv in enumerate(exits):
        for c, piv in enumerate(pis):
            ax = axes[r][c]
            sub = phase_table[
                (phase_table["exit_threshold"] == exv)
                & (phase_table["pi_reward"] == piv)
            ]
            grid = np.full((len(sigmas), len(opps)), np.nan)
            labels = [["" for _ in opps] for _ in sigmas]
            for _, row in sub.iterrows():
                yi = sigmas.index(float(row["sigma"]))
                xi = opps.index(float(row["base_opp"]))
                reg = str(row["regime_majority_hier"])
                if reg in code:
                    grid[yi, xi] = code[reg]
                    labels[yi][xi] = REGIME_SHORT.get(reg, reg)
            ax.imshow(grid, origin="lower", aspect="auto", cmap=cmap, norm=norm)
            ax.set_xticks(np.arange(len(opps)), [f"{x:.2f}" for x in opps], fontsize=8)
            ax.set_yticks(np.arange(len(sigmas)), [f"{y:.2f}" for y in sigmas], fontsize=8)
            ax.set_title(rf"$\pi$={piv:.2f}, exit={exv:.1f}", fontsize=10)
            if r == nrows - 1:
                ax.set_xlabel("base_opp", fontsize=9)
            if c == 0:
                ax.set_ylabel(r"$\sigma$ (legibility)", fontsize=9)
            for yi in range(len(sigmas)):
                for xi in range(len(opps)):
                    lab = labels[yi][xi]
                    if lab:
                        ax.text(
                            xi, yi, lab, ha="center", va="center",
                            fontsize=8, fontweight="bold", color="white",
                        )

    # legend across the bottom
    handles = [
        Patch(facecolor=REGIME_COLORS[r], label=DISPLAY_LABEL[r])
        for r in REGIME_ORDER_HIER
    ]
    fig.legend(
        handles=handles, ncol=len(handles), loc="lower center",
        frameon=False, bbox_to_anchor=(0.5, -0.02),
    )
    fig.suptitle(
        "Phase map: hierarchical regime majority across the 72-cell confirmatory grid",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0.03, 1, 0.97])
    savePdf(fig, "fig2_phase_map.pdf")  # manuscript Figure 2


def plotRegimeCounts(phase_table: pd.DataFrame, seed_df: pd.DataFrame):
    """side-by-side bar chart: cell-level + seed-level counts per regime."""
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.4))

    # cell-level (left)
    cell_counts = {r: int((phase_table["regime_majority_hier"] == r).sum()) for r in REGIME_ORDER_HIER}
    seed_counts = {r: int((seed_df["regime_hier"] == r).sum()) for r in REGIME_ORDER_HIER}
    labels_x = [DISPLAY_LABEL[r] for r in REGIME_ORDER_HIER]
    colors = [REGIME_COLORS[r] for r in REGIME_ORDER_HIER]

    for ax, counts, title, total in (
        (axes[0], cell_counts, "Cell-level majority (n=72 cells)", 72),
        (axes[1], seed_counts, "Seed-level (n=360 seed runs)", 360),
    ):
        vals = [counts[r] for r in REGIME_ORDER_HIER]
        bars = ax.bar(labels_x, vals, color=colors, edgecolor="black", linewidth=0.5)
        ax.set_title(title, fontsize=10)
        ax.set_ylabel("count")
        ax.set_ylim(0, total * 1.12)
        for bar, v in zip(bars, vals):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                v + total * 0.02,
                str(v),
                ha="center", va="bottom", fontsize=9, fontweight="bold",
            )

    fig.suptitle(
        "Regime distribution under hierarchical schema (cap=0.20, active-rate)",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    savePdf(fig, "fig6_regime_counts.pdf")  # manuscript Figure 6 (NEW)


def plotConcentration(seed_df: pd.DataFrame):
    """boxplot of top-5% punishment share by regime, with within-cell concentration finding."""
    present = [r for r in REGIME_ORDER_HIER if (seed_df["regime_hier"] == r).any()]
    data = [seed_df.loc[seed_df["regime_hier"] == r, "top5_punishment_share"].to_numpy() for r in present]

    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    bp = ax.boxplot(
        data,
        tick_labels=[DISPLAY_LABEL[r] for r in present],
        showfliers=True,
        patch_artist=True,
        widths=0.55,
    )
    for patch, regime in zip(bp["boxes"], present):
        patch.set_facecolor(REGIME_COLORS[regime])
        patch.set_alpha(0.85)
    for median in bp["medians"]:
        median.set_color("black")
        median.set_linewidth(1.5)

    ax.axhline(0.80, color="#d62728", lw=1.2, ls="--", alpha=0.7, label="80% threshold")
    ax.set_ylabel("Top-5% share of punishments")
    ax.set_ylim(0.0, 1.05)
    ax.set_title(
        "Within-cell enforcement concentration by regime\n"
        "(top 5% of agents executing >80% of punishments in MIXED cells)",
        fontsize=10,
    )
    ax.legend(loc="lower right", fontsize=9, frameon=False)
    fig.tight_layout()
    savePdf(fig, "fig3_concentration.pdf")  # manuscript Figure 3


def plotTrajectories():
    """per-regime mean trajectories with ±1 SEM band; 4 panels, one per regime
    (CAPTURE panel is left blank with explanatory text since 0 seeds)."""
    fig, axes = plt.subplots(2, 2, figsize=(11.0, 7.0), sharex=True, sharey=True)
    axes = axes.ravel()

    line_specs = [
        ("fund_prevalence", "#0072B2", "Fund. prevalence"),
        ("exit_rate", "#D55E00", "Exit rate"),
        ("active_punish_rate", "#009E73", "Active punish rate"),
        ("enforcer_punish_share_step", "#CC79A7", "Enforcer share"),
    ]

    for ax, regime in zip(axes, REGIME_ORDER_HIER):
        path = CANONICAL / f"timeseries_regime_hier_{regime}.csv"
        if not path.exists() or path.stat().st_size <= 200:
            ax.text(
                0.5, 0.5,
                f"{DISPLAY_LABEL[regime]}\n(0 seed runs in this regime)",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=11, color="#888",
            )
            ax.set_title(DISPLAY_LABEL[regime], fontsize=10)
            ax.set_facecolor("#f7f7f7")
            continue
        df = pd.read_csv(path)
        if df.empty:
            ax.text(
                0.5, 0.5,
                f"{DISPLAY_LABEL[regime]}\n(0 seed runs in this regime)",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=11, color="#888",
            )
            ax.set_title(DISPLAY_LABEL[regime], fontsize=10)
            ax.set_facecolor("#f7f7f7")
            continue

        for col, color, label in line_specs:
            if col not in df.columns:
                continue
            grouped = df.groupby("t")[col].agg(["mean", "std", "count"])
            sem = grouped["std"] / np.sqrt(grouped["count"].clip(lower=1))
            ax.plot(grouped.index, grouped["mean"], color=color, lw=1.6, label=label)
            ax.fill_between(
                grouped.index,
                grouped["mean"] - sem,
                grouped["mean"] + sem,
                color=color, alpha=0.18, linewidth=0,
            )

        n_seeds = df["seed"].nunique()
        ax.set_title(f"{DISPLAY_LABEL[regime]} (n={n_seeds} seeds)", fontsize=10)
        ax.set_ylim(0.0, 1.02)

    for ax in axes:
        ax.set_xlabel("Time step")
        ax.set_ylabel("Rate / share")

    handles, labels = axes[1].get_legend_handles_labels()
    if handles:
        fig.legend(
            handles, labels, ncol=len(handles), loc="lower center",
            frameon=False, bbox_to_anchor=(0.5, -0.02), fontsize=9,
        )
    fig.suptitle(
        "Mean per-regime trajectories (canonical hierarchical schema)",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0.03, 1, 0.96])
    savePdf(fig, "figure4_trajectories.pdf", submission=False)  # build artifact, not in manuscript


def cohensD(a: np.ndarray, b: np.ndarray) -> float:
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    s1 = np.std(a, ddof=1)
    s2 = np.std(b, ddof=1)
    denom = len(a) + len(b) - 2
    if denom <= 0:
        return float("nan")
    sp = np.sqrt(((len(a) - 1) * s1 * s1 + (len(b) - 1) * s2 * s2) / denom)
    if sp <= 0:
        return float("nan")
    return float((np.mean(a) - np.mean(b)) / sp)


def buildRegimeMetricsTable(seed_df: pd.DataFrame, phase_table: pd.DataFrame):
    """produces table5_regime_metrics.tex with median metrics + pooled Cohen's d (L) per regime."""
    rows = []
    for r in REGIME_ORDER_HIER:
        seed_sub = seed_df[seed_df["regime_hier"] == r]
        cell_n = int((phase_table["regime_majority_hier"] == r).sum())
        seed_n = len(seed_sub)
        if seed_n == 0:
            rows.append(
                {
                    "regime": DISPLAY_LABEL[r],
                    "n_cells": cell_n,
                    "n_seeds": seed_n,
                    "med_prev": "—",
                    "med_exit": "—",
                    "med_actpr": "—",
                    "med_enf": "—",
                    "med_top5": "—",
                    "cohens_d": "—",
                }
            )
            continue

        # pooled Cohen's d for L over enforcers vs others, across all seeds in this regime
        pooled_enf, pooled_other = [], []
        for _, row in seed_sub.iterrows():
            run_dir = REPO_ROOT / row["run_dir"]
            apath = run_dir / "agent_summary.csv"
            if not apath.exists():
                continue
            adf = pd.read_csv(apath, usecols=["L", "is_enforcer"])
            is_enf = adf["is_enforcer"]
            if is_enf.dtype == object:
                is_enf = is_enf.astype(str).str.lower().map(
                    {"true": True, "false": False, "1": True, "0": False}
                )
            is_enf = is_enf.fillna(False).astype(bool)
            pooled_enf.append(adf.loc[is_enf, "L"].to_numpy())
            pooled_other.append(adf.loc[~is_enf, "L"].to_numpy())
        d = (
            cohensD(np.concatenate(pooled_enf), np.concatenate(pooled_other))
            if pooled_enf
            else float("nan")
        )

        rows.append(
            {
                "regime": DISPLAY_LABEL[r],
                "n_cells": cell_n,
                "n_seeds": seed_n,
                "med_prev": f"{float(seed_sub['final_fund_prevalence'].median()):.3f}",
                "med_exit": f"{float(seed_sub['final_exit_rate'].median()):.3f}",
                "med_actpr": f"{float(seed_sub['max_active_punish'].median()):.3f}",
                "med_enf": f"{float(seed_sub['enforcer_punish_share'].median()):.3f}",
                "med_top5": f"{float(seed_sub['top5_punishment_share'].median()):.3f}",
                "cohens_d": (f"{d:.2f}" if np.isfinite(d) else "—"),
            }
        )

    lines = [
        r"% generated by scripts/build_methodology_paper_figures.py",
        r"\begin{table}[ht]",
        r"\centering",
        r"\caption{Per-regime median metrics from the v2.5 confirmatory sweep "
        r"(canonical hierarchical schema: capture-exit-cap = 0.20, active-rate corrected). "
        r"Cohen's $d$ for $L$ (literalism) compares per-agent values between enforcers and non-enforcers, pooled across all seeds in the regime category.}",
        r"\label{tab:6}",
        r"\begin{tabular}{lcccccccc}",
        r"\toprule",
        r"Regime & Cells & Seeds & "
        r"Med.\ Fund.\ prev. & Med.\ Exit & "
        r"Med.\ Active punish & Med.\ Enforcer share & "
        r"Med.\ Top-5\% & Cohen's $d$ ($L$) \\",
        r"\midrule",
    ]
    for r in rows:
        lines.append(
            f"{r['regime']} & {r['n_cells']} & {r['n_seeds']} & "
            f"{r['med_prev']} & {r['med_exit']} & "
            f"{r['med_actpr']} & {r['med_enf']} & "
            f"{r['med_top5']} & {r['cohens_d']} \\\\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
        ]
    )

    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
    outpath = SUBMISSION_DIR / "table6_regime_metrics.tex"
    outpath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {outpath.relative_to(REPO_ROOT)}")


def main():
    if not CANONICAL.exists():
        raise SystemExit(
            f"canonical dir not found: {CANONICAL}\n"
            "run scripts/build_methodology_paper_canonical.py first"
        )

    phase_table = pd.read_csv(CANONICAL / "phase_bundle" / "phase_table.csv")
    seed_df = pd.read_csv(CANONICAL / "sweep_seed_results.csv")

    plotPhaseMap(phase_table)
    plotRegimeCounts(phase_table, seed_df)
    plotConcentration(seed_df)
    plotTrajectories()
    buildRegimeMetricsTable(seed_df, phase_table)
    print("done")


if __name__ == "__main__":
    main()
