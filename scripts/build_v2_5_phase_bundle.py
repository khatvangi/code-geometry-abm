#!/usr/bin/env python3
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
import pandas as pd


REGIME_ORDER_LEGACY = ["QUIET", "MIXED", "CAPTURE", "COLLAPSE"]
REGIME_ORDER_HIER = ["QUIET", "MIXED", "CAPTURE_HIERARCHICAL", "COLLAPSE"]
REGIME_COLORS = {
    "QUIET": "#bdbdbd",
    "MIXED": "#4daf4a",
    "CAPTURE": "#ff7f00",
    "CAPTURE_HIERARCHICAL": "#ff7f00",
    "COLLAPSE": "#377eb8",
}
REGIME_SHORT = {
    "QUIET": "Q",
    "MIXED": "M",
    "CAPTURE": "C",
    "CAPTURE_HIERARCHICAL": "CH",
    "COLLAPSE": "X",
}


def plot_panel_grid(df: pd.DataFrame, regime_col: str, title: str, outpath: Path, regime_order: list):
    pis = sorted(df["pi_reward"].dropna().unique())
    exits = sorted(df["exit_threshold"].dropna().unique())
    sigmas = sorted(df["sigma"].dropna().unique())
    opps = sorted(df["base_opp"].dropna().unique())
    if not pis or not exits or not sigmas or not opps:
        return

    nrows = len(exits)
    ncols = len(pis)
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.0 * ncols, 3.6 * nrows), dpi=160, squeeze=False)
    cmap = ListedColormap([REGIME_COLORS[r] for r in regime_order])
    norm = BoundaryNorm(np.arange(-0.5, len(regime_order) + 0.5, 1), cmap.N)
    code = {r: i for i, r in enumerate(regime_order)}

    for r, exv in enumerate(exits):
        for c, piv in enumerate(pis):
            ax = axes[r][c]
            sub = df[(df["exit_threshold"] == exv) & (df["pi_reward"] == piv)]
            grid = np.full((len(sigmas), len(opps)), np.nan)
            labels = [["" for _ in opps] for _ in sigmas]
            for _, row in sub.iterrows():
                yi = sigmas.index(float(row["sigma"]))
                xi = opps.index(float(row["base_opp"]))
                reg = str(row[regime_col])
                if reg not in code:
                    continue
                grid[yi, xi] = code[reg]
                labels[yi][xi] = REGIME_SHORT.get(reg, reg)
            ax.imshow(grid, origin="lower", aspect="auto", cmap=cmap, norm=norm)
            ax.set_xticks(np.arange(len(opps)), [f"{x:.2f}" for x in opps], rotation=45, ha="right")
            ax.set_yticks(np.arange(len(sigmas)), [f"{y:.2f}" for y in sigmas])
            ax.set_title(f"pi={piv:.2f}, exit_th={exv:.2f}", fontsize=9)
            ax.set_xlabel("base_opp")
            ax.set_ylabel("sigma")
            for yi in range(len(sigmas)):
                for xi in range(len(opps)):
                    lab = labels[yi][xi]
                    if lab:
                        ax.text(xi, yi, lab, ha="center", va="center", fontsize=7, fontweight="bold")

    fig.suptitle(title, fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(outpath)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Sweep result root containing sweep_summary.csv")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    summary_path = root / "sweep_summary.csv"
    seeds_path = root / "sweep_seed_results.csv"
    if not summary_path.exists() or not seeds_path.exists():
        raise SystemExit(f"Missing summary files under {root}")

    summary = pd.read_csv(summary_path)
    seeds = pd.read_csv(seeds_path)

    outdir = root / "phase_bundle"
    outdir.mkdir(parents=True, exist_ok=True)

    keep_cols = [
        "sigma",
        "pi_reward",
        "base_opp",
        "exit_threshold",
        "n_seeds",
        "regime_majority_legacy",
        "regime_majority_hier",
        "n_collapse_legacy",
        "n_capture_legacy",
        "n_mixed_legacy",
        "n_quiet_legacy",
        "n_collapse_hier",
        "n_capture_hier",
        "n_mixed_hier",
        "n_quiet_hier",
        "median_fund_prevalence",
        "median_exit_rate",
        "median_max_punish",
        "median_enforcer_punish_share",
        "median_top5_share",
    ]
    phase_table = summary[[c for c in keep_cols if c in summary.columns]].copy()
    phase_table.to_csv(outdir / "phase_table.csv", index=False)

    legacy_counts = summary["regime_majority_legacy"].value_counts().rename_axis("regime").reset_index(name="n_cells")
    legacy_counts["schema"] = "legacy"
    hier_counts = summary["regime_majority_hier"].value_counts().rename_axis("regime").reset_index(name="n_cells")
    hier_counts["schema"] = "hierarchical"
    regime_counts = pd.concat([legacy_counts, hier_counts], ignore_index=True)
    regime_counts.to_csv(outdir / "regime_counts.csv", index=False)

    seed_legacy = seeds["regime_legacy"].value_counts().rename_axis("regime").reset_index(name="n_seed_runs")
    seed_legacy["schema"] = "legacy"
    seed_hier = seeds["regime_hier"].value_counts().rename_axis("regime").reset_index(name="n_seed_runs")
    seed_hier["schema"] = "hierarchical"
    seed_counts = pd.concat([seed_legacy, seed_hier], ignore_index=True)
    seed_counts.to_csv(outdir / "seed_regime_counts.csv", index=False)

    plot_panel_grid(
        summary,
        regime_col="regime_majority_legacy",
        title="v2.5 Corrected Sweep: Legacy Regime Majority",
        outpath=outdir / "phase_map_legacy.png",
        regime_order=REGIME_ORDER_LEGACY,
    )
    plot_panel_grid(
        summary,
        regime_col="regime_majority_hier",
        title="v2.5 Corrected Sweep: Hierarchical Regime Majority",
        outpath=outdir / "phase_map_hierarchical.png",
        regime_order=REGIME_ORDER_HIER,
    )

    legacy_found = sorted(summary["regime_majority_legacy"].dropna().unique())
    hier_found = sorted(summary["regime_majority_hier"].dropna().unique())
    has_three_legacy = all(x in legacy_found for x in ["COLLAPSE", "MIXED", "CAPTURE"])
    has_three_hier = all(x in hier_found for x in ["COLLAPSE", "MIXED", "CAPTURE_HIERARCHICAL"])

    report_lines = []
    report_lines.append("# RESULTS_V2_5_PHASE_BUNDLE")
    report_lines.append("")
    report_lines.append(f"- root: `{root}`")
    report_lines.append(f"- n_cells: {len(summary)}")
    report_lines.append(f"- n_seed_runs: {len(seeds)}")
    report_lines.append(f"- legacy_regimes_found: {legacy_found}")
    report_lines.append(f"- hierarchical_regimes_found: {hier_found}")
    report_lines.append(f"- three_regimes_legacy: {has_three_legacy}")
    report_lines.append(f"- three_regimes_hierarchical: {has_three_hier}")
    report_lines.append("")
    report_lines.append("## Files")
    report_lines.append(f"- `{outdir / 'phase_table.csv'}`")
    report_lines.append(f"- `{outdir / 'regime_counts.csv'}`")
    report_lines.append(f"- `{outdir / 'seed_regime_counts.csv'}`")
    report_lines.append(f"- `{outdir / 'phase_map_legacy.png'}`")
    report_lines.append(f"- `{outdir / 'phase_map_hierarchical.png'}`")
    (outdir / "RESULTS_V2_5_PHASE_BUNDLE.md").write_text("\n".join(report_lines), encoding="utf-8")

    print(f"Wrote {outdir / 'phase_table.csv'}")
    print(f"Wrote {outdir / 'regime_counts.csv'}")
    print(f"Wrote {outdir / 'seed_regime_counts.csv'}")
    print(f"Wrote {outdir / 'phase_map_legacy.png'}")
    print(f"Wrote {outdir / 'phase_map_hierarchical.png'}")
    print(f"Wrote {outdir / 'RESULTS_V2_5_PHASE_BUNDLE.md'}")


if __name__ == "__main__":
    main()
