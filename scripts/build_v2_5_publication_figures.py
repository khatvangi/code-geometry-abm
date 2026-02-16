#!/usr/bin/env python3
"""Build publication-ready v2.5 confirmatory figures and captions."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch


REGIME_ORDER = ["QUIET", "MIXED", "COLLAPSE", "CAPTURE_HIERARCHICAL"]
REGIME_COLORS = {
    "QUIET": "#9AA0A6",
    "MIXED": "#0072B2",
    "COLLAPSE": "#D55E00",
    "CAPTURE_HIERARCHICAL": "#009E73",
}
REGIME_TO_CODE = {name: i for i, name in enumerate(REGIME_ORDER)}


def apply_publication_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "figure.titlesize": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": False,
            "savefig.dpi": 300,
        }
    )


def _save(fig: plt.Figure, outdir: Path, stem: str) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    fig.savefig(outdir / f"{stem}.png", bbox_inches="tight", dpi=300)
    fig.savefig(outdir / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_phase_map(phase_table: pd.DataFrame, outdir: Path) -> None:
    sigmas = sorted(phase_table["sigma"].unique())
    base_opps = sorted(phase_table["base_opp"].unique())
    exits = sorted(phase_table["exit_threshold"].unique())
    pis = sorted(phase_table["pi_reward"].unique())

    nrows = len(exits)
    ncols = len(pis)
    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=(3.9 * ncols, 3.2 * nrows),
        squeeze=False,
    )

    cmap = ListedColormap([REGIME_COLORS[k] for k in REGIME_ORDER])

    for r, ex in enumerate(exits):
        for c, pi in enumerate(pis):
            ax = axes[r, c]
            sub = phase_table[
                (phase_table["exit_threshold"] == ex) & (phase_table["pi_reward"] == pi)
            ].copy()
            if sub.empty:
                ax.axis("off")
                continue

            mat = np.full((len(sigmas), len(base_opps)), np.nan)
            for i, s in enumerate(sigmas):
                for j, b in enumerate(base_opps):
                    row = sub[(sub["sigma"] == s) & (sub["base_opp"] == b)]
                    if row.empty:
                        continue
                    regime = row.iloc[0]["regime_majority_hier"]
                    mat[i, j] = REGIME_TO_CODE[regime]

            im = ax.imshow(mat, cmap=cmap, vmin=-0.5, vmax=len(REGIME_ORDER) - 0.5, aspect="auto")
            ax.set_xticks(range(len(base_opps)))
            ax.set_xticklabels([f"{x:g}" for x in base_opps])
            ax.set_yticks(range(len(sigmas)))
            ax.set_yticklabels([f"{x:g}" for x in sigmas])
            ax.set_xlabel("Base Exit Opportunity")
            ax.set_ylabel("Sigma (Legibility)")
            ax.set_title(f"pi_reward={pi:g}, exit_threshold={ex:g}")

            for i in range(len(sigmas)):
                for j in range(len(base_opps)):
                    if np.isnan(mat[i, j]):
                        continue
                    regime = REGIME_ORDER[int(mat[i, j])]
                    label = regime.replace("_HIERARCHICAL", "\nHIER")
                    ax.text(j, i, label, ha="center", va="center", fontsize=6.4, color="black")

    fig.suptitle("v2.5 Confirmatory Hierarchical Phase Map (72 cells, 5 seeds/cell)", y=1.01)
    handles = [Patch(facecolor=REGIME_COLORS[r], edgecolor="none", label=r) for r in REGIME_ORDER]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.02))
    _save(fig, outdir, "fig1_phase_map_hierarchical")


def plot_regime_counts(
    regime_counts: pd.DataFrame, seed_counts: pd.DataFrame, outdir: Path
) -> Dict[str, int]:
    cell_counts = (
        regime_counts[regime_counts["schema"] == "hierarchical"]
        .set_index("regime")["n_cells"]
        .reindex(REGIME_ORDER)
        .fillna(0)
        .astype(int)
    )
    seed_counts_h = (
        seed_counts[seed_counts["schema"] == "hierarchical"]
        .set_index("regime")["n_seed_runs"]
        .reindex(REGIME_ORDER)
        .fillna(0)
        .astype(int)
    )

    fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.3))
    x = np.arange(len(REGIME_ORDER))
    colors = [REGIME_COLORS[r] for r in REGIME_ORDER]

    axes[0].bar(x, cell_counts.values, color=colors)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(REGIME_ORDER, rotation=20, ha="right")
    axes[0].set_ylabel("Count")
    axes[0].set_title("Cell-majority counts (n=72)")
    for xi, yi in zip(x, cell_counts.values):
        axes[0].text(xi, yi + 0.6, f"{yi}", ha="center", va="bottom", fontsize=8)

    axes[1].bar(x, seed_counts_h.values, color=colors)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(REGIME_ORDER, rotation=20, ha="right")
    axes[1].set_ylabel("Count")
    axes[1].set_title("Seed-level counts (n=360)")
    for xi, yi in zip(x, seed_counts_h.values):
        axes[1].text(xi, yi + 2.0, f"{yi}", ha="center", va="bottom", fontsize=8)

    fig.suptitle("Regime Frequency: Cell-majority vs Seed-level")
    fig.tight_layout()
    _save(fig, outdir, "fig2_regime_counts")

    out = {f"cell_{k.lower()}": int(v) for k, v in cell_counts.to_dict().items()}
    out.update({f"seed_{k.lower()}": int(v) for k, v in seed_counts_h.to_dict().items()})
    return out


def plot_concentration(seed_df: pd.DataFrame, outdir: Path) -> Dict[str, float]:
    metrics = [
        ("top5_punishment_share", "Top-5 Punishment Share"),
        ("top10_punishment_share", "Top-10 Punishment Share"),
        ("enforcer_punish_share", "Enforcer Punishment Share"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(11.2, 3.4))
    reg_order_present = [r for r in REGIME_ORDER if r in seed_df["regime_hier"].unique()]
    palette = [REGIME_COLORS[r] for r in reg_order_present]

    for ax, (col, title) in zip(axes, metrics):
        data = [seed_df.loc[seed_df["regime_hier"] == r, col].to_numpy() for r in reg_order_present]
        bp = ax.boxplot(data, tick_labels=reg_order_present, showfliers=False, patch_artist=True)
        for patch, color in zip(bp["boxes"], palette):
            patch.set_facecolor(color)
            patch.set_alpha(0.8)
        ax.set_title(title)
        ax.set_ylim(0, 1.02)
        ax.tick_params(axis="x", rotation=20)

    fig.suptitle("Punishment Concentration Across Hierarchical Regimes (seed-level)")
    fig.tight_layout()
    _save(fig, outdir, "fig3_concentration_by_regime")

    return {
        "med_top5": float(seed_df["top5_punishment_share"].median()),
        "med_top10": float(seed_df["top10_punishment_share"].median()),
        "med_enfshare": float(seed_df["enforcer_punish_share"].median()),
    }


def plot_timeseries(root: Path, outdir: Path) -> None:
    files = {
        "QUIET": root / "timeseries_regime_hier_QUIET.csv",
        "MIXED": root / "timeseries_regime_hier_MIXED.csv",
        "COLLAPSE": root / "timeseries_regime_hier_COLLAPSE.csv",
        "CAPTURE_HIERARCHICAL": root / "timeseries_regime_hier_CAPTURE_HIERARCHICAL.csv",
    }
    fig, axes = plt.subplots(2, 2, figsize=(11.0, 6.8), sharex=True, sharey=True)
    axes = axes.ravel()
    line_colors = {"exit_rate": "#D55E00", "fund_prevalence": "#0072B2", "punish_rate": "#009E73"}

    for ax, regime in zip(axes, files):
        path = files[regime]
        if not path.exists():
            ax.axis("off")
            continue
        df = pd.read_csv(path)
        ax.plot(df["t"], df["exit_rate"], color=line_colors["exit_rate"], lw=1.8, label="Exit rate")
        ax.plot(
            df["t"],
            df["fund_prevalence"],
            color=line_colors["fund_prevalence"],
            lw=1.8,
            label="Fund. prevalence",
        )
        ax.plot(df["t"], df["punish_rate"], color=line_colors["punish_rate"], lw=1.5, label="Punish rate")
        ax.set_title(regime)
        ax.set_ylim(0.0, 1.02)
        ax.set_xlabel("Time step")
        ax.set_ylabel("Rate")

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=3, loc="lower center", frameon=False, bbox_to_anchor=(0.5, -0.01))
    fig.suptitle("Representative Regime Trajectories (hierarchical classification)")
    fig.tight_layout()
    _save(fig, outdir, "fig4_regime_timeseries")


def _cohens_d(enf: np.ndarray, other: np.ndarray) -> float:
    enf = enf[np.isfinite(enf)]
    other = other[np.isfinite(other)]
    if len(enf) < 2 or len(other) < 2:
        return float("nan")
    s1 = np.std(enf, ddof=1)
    s2 = np.std(other, ddof=1)
    denom = len(enf) + len(other) - 2
    if denom <= 0:
        return float("nan")
    sp = np.sqrt(((len(enf) - 1) * s1 * s1 + (len(other) - 1) * s2 * s2) / denom)
    if sp <= 0:
        return float("nan")
    return float((np.mean(enf) - np.mean(other)) / sp)


def plot_literalism_enrichment(seed_df: pd.DataFrame, outdir: Path) -> Dict[str, float]:
    rows = []
    pooled_frames = []
    for _, row in seed_df.iterrows():
        run_dir = Path(row["run_dir"])
        p = run_dir / "agent_summary.csv"
        if not p.exists():
            continue
        a = pd.read_csv(p, usecols=["L", "is_enforcer"])
        is_enf = a["is_enforcer"]
        if is_enf.dtype == object:
            is_enf = (
                is_enf.astype(str)
                .str.lower()
                .map({"true": True, "false": False, "1": True, "0": False})
            )
        is_enf = is_enf.fillna(False).astype(bool)
        a["is_enforcer"] = is_enf
        pooled_frames.append(a)
        d = _cohens_d(a.loc[is_enf, "L"].to_numpy(), a.loc[~is_enf, "L"].to_numpy())
        rows.append({"regime_hier": row["regime_hier"], "cohens_d": d})

    ddf = pd.DataFrame(rows)
    reg_order_present = [r for r in REGIME_ORDER if r in ddf["regime_hier"].unique()]
    data = [ddf.loc[ddf["regime_hier"] == r, "cohens_d"].dropna().to_numpy() for r in reg_order_present]
    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    bp = ax.boxplot(data, tick_labels=reg_order_present, showfliers=False, patch_artist=True)
    for patch, reg in zip(bp["boxes"], reg_order_present):
        patch.set_facecolor(REGIME_COLORS[reg])
        patch.set_alpha(0.85)
    ax.axhline(0, color="black", lw=1.0, alpha=0.7)
    ax.set_ylabel("Cohen's d for L (enforcers vs others)")
    ax.set_title("Literalism Enrichment by Regime (run-level effect sizes)")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    _save(fig, outdir, "fig5_literalism_enrichment")

    all_agents = pd.concat(pooled_frames, ignore_index=True)
    pooled_d_all = _cohens_d(
        all_agents.loc[all_agents["is_enforcer"], "L"].to_numpy(),
        all_agents.loc[~all_agents["is_enforcer"], "L"].to_numpy(),
    )
    mixed_agents = []
    for (_, row), a in zip(seed_df.iterrows(), pooled_frames):
        if row["regime_hier"] == "MIXED":
            mixed_agents.append(a)
    pooled_d_mixed = float("nan")
    if mixed_agents:
        ma = pd.concat(mixed_agents, ignore_index=True)
        pooled_d_mixed = _cohens_d(
            ma.loc[ma["is_enforcer"], "L"].to_numpy(),
            ma.loc[~ma["is_enforcer"], "L"].to_numpy(),
        )

    return {"pooled_d_all": pooled_d_all, "pooled_d_mixed": pooled_d_mixed}


def write_captions(
    outdir: Path,
    counts: Dict[str, int],
    concentration: Dict[str, float],
    dvals: Dict[str, float],
) -> None:
    lines = [
        "# Figure Captions (v2.5 Confirmatory)",
        "",
        "## Figure 1. Hierarchical phase map across confirmatory grid.",
        (
            "Cell-majority regime assignment across 72 parameter cells "
            "(5 stochastic seeds per cell). Axes vary legibility (`sigma`) and "
            "outside opportunity (`base_opp`) within panels; panel facets vary "
            "`pi_reward` and `exit_threshold`. Regime counts are: "
            f"QUIET={counts['cell_quiet']}, MIXED={counts['cell_mixed']}, "
            f"COLLAPSE={counts['cell_collapse']}, CAPTURE_HIERARCHICAL={counts['cell_capture_hierarchical']}."
        ),
        "",
        "## Figure 2. Regime frequencies at cell-majority and seed level.",
        (
            "Left panel shows cell-majority counts (n=72 cells); right panel shows "
            "seed-level counts (n=360 runs). Seed-level hierarchical counts are: "
            f"QUIET={counts['seed_quiet']}, MIXED={counts['seed_mixed']}, "
            f"COLLAPSE={counts['seed_collapse']}, CAPTURE_HIERARCHICAL={counts['seed_capture_hierarchical']}."
        ),
        "",
        "## Figure 3. Punishment concentration by regime.",
        (
            "Seed-level distributions of top-5 punishment share, top-10 punishment share, "
            "and enforcer punishment share under hierarchical classification. Across all "
            "360 confirmatory runs, medians are: "
            f"top-5={concentration['med_top5']:.6f}, "
            f"top-10={concentration['med_top10']:.6f}, "
            f"enforcer share={concentration['med_enfshare']:.6f}, indicating durable "
            "minority enforcement concentration."
        ),
        "",
        "## Figure 4. Representative trajectories for each hierarchical regime.",
        (
            "Time-series profiles (one representative run per regime) for exit rate, "
            "fundamentalist prevalence, and punishment rate. The panels illustrate regime-specific "
            "dynamics: low-activity QUIET, persistent enforcement MIXED, high-exit COLLAPSE, "
            "and high-enforcer-share CAPTURE_HIERARCHICAL."
        ),
        "",
        "## Figure 5. Literalism enrichment among enforcers.",
        (
            "Run-level Cohen's d distributions comparing literalism trait L in enforcers versus "
            "non-enforcers, stratified by hierarchical regime. Pooled effect sizes from confirmatory "
            f"data are d={dvals['pooled_d_all']:.6f} across all runs and "
            f"d={dvals['pooled_d_mixed']:.6f} within MIXED runs, showing strong enforcer enrichment in L."
        ),
        "",
        "## Figure Files",
        "- `fig1_phase_map_hierarchical.png`",
        "- `fig2_regime_counts.png`",
        "- `fig3_concentration_by_regime.png`",
        "- `fig4_regime_timeseries.png`",
        "- `fig5_literalism_enrichment.png`",
    ]
    (outdir / "FIGURE_CAPTIONS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Build publication-ready v2.5 confirmatory figures.")
    ap.add_argument(
        "--root",
        type=Path,
        default=Path(
            "/storage/social-science/religion-code-geometry-abm/results/v2.5_corrected_three_regime_confirm"
        ),
    )
    ap.add_argument("--outdir", type=Path, default=None)
    args = ap.parse_args()

    root = args.root.resolve()
    outdir = args.outdir or (root / "figures_publication")
    outdir = outdir.resolve()

    phase_table = pd.read_csv(root / "phase_bundle" / "phase_table.csv")
    regime_counts = pd.read_csv(root / "phase_bundle" / "regime_counts.csv")
    seed_counts = pd.read_csv(root / "phase_bundle" / "seed_regime_counts.csv")
    seed_df = pd.read_csv(root / "sweep_seed_results.csv")

    apply_publication_style()
    plot_phase_map(phase_table, outdir)
    counts = plot_regime_counts(regime_counts, seed_counts, outdir)
    concentration = plot_concentration(seed_df, outdir)
    plot_timeseries(root, outdir)
    dvals = plot_literalism_enrichment(seed_df, outdir)
    write_captions(outdir, counts, concentration, dvals)

    print(f"Wrote figures and captions to: {outdir}")


if __name__ == "__main__":
    main()
