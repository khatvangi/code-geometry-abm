#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
import pandas as pd


REGIME_ORDER = ["QUIET", "MIXED", "CAPTURE", "COLLAPSE"]
REGIME_CODE = {r: i for i, r in enumerate(REGIME_ORDER)}
REGIME_COLOR = {
    "QUIET": "#bdbdbd",
    "MIXED": "#4daf4a",
    "CAPTURE": "#e41a1c",
    "COLLAPSE": "#377eb8",
}


def classify_regime(exit_rate: float, prevalence: float, max_punish: float) -> str:
    if exit_rate >= 0.90:
        return "COLLAPSE"
    if prevalence >= 0.90 and exit_rate <= 0.20:
        return "CAPTURE"
    if max_punish >= 0.10:
        return "MIXED"
    return "QUIET"


def parse_seed(parts):
    for p in parts:
        if p.startswith("seed_"):
            return int(p.split("_", 1)[1])
    return -1


def collect_sweep_runs(root: Path, sweep_name: str) -> pd.DataFrame:
    rows = []
    sweep_root = root / sweep_name
    if not sweep_root.exists():
        return pd.DataFrame()

    for metrics_path in sweep_root.rglob("metrics.csv"):
        rel_parts = metrics_path.relative_to(root).parts
        run_dir = metrics_path.parent
        df = pd.read_csv(metrics_path)
        if df.empty:
            continue
        final = df.iloc[-1]
        seed = parse_seed(rel_parts)

        if sweep_name == "sweep1":
            coeff = None
            shock = None
            for p in rel_parts:
                m = re.match(r"^threatCoeff_(.+)$", p)
                if m:
                    coeff = float(m.group(1))
                m = re.match(r"^shock_(.+)$", p)
                if m:
                    shock = float(m.group(1))
            if coeff is None or shock is None:
                continue
            rows.append(
                {
                    "run_dir": str(run_dir),
                    "seed": seed,
                    "threat_coeff": coeff,
                    "shock_strength": shock,
                    "final_exit_rate": float(final.get("exit_rate", np.nan)),
                    "final_prevalence": float(final.get("fund_prevalence", np.nan)),
                    "max_punish_rate": float(df["punish_rate"].max()) if "punish_rate" in df.columns else np.nan,
                }
            )
        elif sweep_name == "sweep2":
            mbt = None
            oppb = None
            for p in rel_parts:
                m = re.match(r"^mbt_(.+)$", p)
                if m:
                    mbt = float(m.group(1))
                m = re.match(r"^oppBase_(.+)$", p)
                if m:
                    oppb = float(m.group(1))
            if mbt is None or oppb is None:
                continue
            rows.append(
                {
                    "run_dir": str(run_dir),
                    "seed": seed,
                    "membership_benefit_threat": mbt,
                    "exit_opportunity_base": oppb,
                    "final_exit_rate": float(final.get("exit_rate", np.nan)),
                    "final_prevalence": float(final.get("fund_prevalence", np.nan)),
                    "max_punish_rate": float(df["punish_rate"].max()) if "punish_rate" in df.columns else np.nan,
                }
            )

    return pd.DataFrame(rows)


def aggregate_cells(df: pd.DataFrame, keys):
    if df.empty:
        return pd.DataFrame()
    agg = (
        df.groupby(keys, as_index=False)
        .agg(
            n_runs=("seed", "count"),
            final_exit_rate_median=("final_exit_rate", "median"),
            final_prevalence_median=("final_prevalence", "median"),
            max_punish_rate_median=("max_punish_rate", "median"),
            final_exit_rate_mean=("final_exit_rate", "mean"),
            final_prevalence_mean=("final_prevalence", "mean"),
            max_punish_rate_mean=("max_punish_rate", "mean"),
        )
        .sort_values(keys)
    )
    agg["regime"] = agg.apply(
        lambda r: classify_regime(
            float(r["final_exit_rate_median"]),
            float(r["final_prevalence_median"]),
            float(r["max_punish_rate_median"]),
        ),
        axis=1,
    )
    agg["regime_code"] = agg["regime"].map(REGIME_CODE).astype(int)
    return agg


def heatmap_numeric(df: pd.DataFrame, xcol: str, ycol: str, val_col: str, title: str, out_path: Path):
    if df.empty:
        return
    xvals = sorted(df[xcol].unique())
    yvals = sorted(df[ycol].unique())
    grid = np.full((len(yvals), len(xvals)), np.nan)
    for _, r in df.iterrows():
        xi = xvals.index(r[xcol])
        yi = yvals.index(r[ycol])
        grid[yi, xi] = r[val_col]

    plt.figure(figsize=(7, 5), dpi=140)
    im = plt.imshow(grid, origin="lower", aspect="auto")
    plt.xticks(np.arange(len(xvals)), [f"{x:.2f}" for x in xvals])
    plt.yticks(np.arange(len(yvals)), [f"{y:.2f}" for y in yvals])
    plt.xlabel(xcol)
    plt.ylabel(ycol)
    plt.title(title)
    plt.colorbar(im, label=val_col)
    for yi in range(len(yvals)):
        for xi in range(len(xvals)):
            val = grid[yi, xi]
            if np.isfinite(val):
                plt.text(xi, yi, f"{val:.2f}", ha="center", va="center", fontsize=7, color="black")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def heatmap_regime(df: pd.DataFrame, xcol: str, ycol: str, title: str, out_path: Path):
    if df.empty:
        return
    xvals = sorted(df[xcol].unique())
    yvals = sorted(df[ycol].unique())
    grid = np.full((len(yvals), len(xvals)), np.nan)
    label_grid = [["" for _ in xvals] for _ in yvals]
    for _, r in df.iterrows():
        xi = xvals.index(r[xcol])
        yi = yvals.index(r[ycol])
        grid[yi, xi] = r["regime_code"]
        label_grid[yi][xi] = r["regime"]

    cmap = ListedColormap([REGIME_COLOR[r] for r in REGIME_ORDER])
    norm = BoundaryNorm(np.arange(-0.5, len(REGIME_ORDER) + 0.5, 1), cmap.N)

    plt.figure(figsize=(7, 5), dpi=140)
    plt.imshow(grid, origin="lower", aspect="auto", cmap=cmap, norm=norm)
    plt.xticks(np.arange(len(xvals)), [f"{x:.2f}" for x in xvals])
    plt.yticks(np.arange(len(yvals)), [f"{y:.2f}" for y in yvals])
    plt.xlabel(xcol)
    plt.ylabel(ycol)
    plt.title(title)

    for yi in range(len(yvals)):
        for xi in range(len(xvals)):
            label = label_grid[yi][xi]
            if label:
                short = {"QUIET": "Q", "MIXED": "M", "CAPTURE": "C", "COLLAPSE": "X"}[label]
                plt.text(xi, yi, short, ha="center", va="center", fontsize=9, color="black", fontweight="bold")

    cbar = plt.colorbar(ticks=np.arange(len(REGIME_ORDER)))
    cbar.ax.set_yticklabels(REGIME_ORDER)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def boundary_note(df: pd.DataFrame, sweep_name: str, xcol: str, ycol: str):
    if df.empty:
        return f"{sweep_name}: no data"
    counts = df["regime"].value_counts().to_dict()
    lines = [f"{sweep_name} regime counts: {counts}"]

    cap = df[df["regime"] == "CAPTURE"]
    col = df[df["regime"] == "COLLAPSE"]
    mix = df[df["regime"] == "MIXED"]

    if not cap.empty:
        lines.append(
            f"capture appears for {xcol}>={cap[xcol].min():.2f}, {ycol}>={cap[ycol].min():.2f}"
        )
    if not col.empty:
        lines.append(
            f"collapse appears for {xcol}>={col[xcol].min():.2f}, {ycol}>={col[ycol].min():.2f}"
        )
    if not mix.empty:
        lines.append(
            f"mixed spans {xcol} in [{mix[xcol].min():.2f}, {mix[xcol].max():.2f}] and {ycol} in [{mix[ycol].min():.2f}, {mix[ycol].max():.2f}]"
        )
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=str)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    summary_dir = root / "summary"
    plots_dir = summary_dir / "plots"
    summary_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    sweep1_runs = collect_sweep_runs(root, "sweep1")
    sweep2_runs = collect_sweep_runs(root, "sweep2")

    sweep1_cell = aggregate_cells(sweep1_runs, ["threat_coeff", "shock_strength"])
    sweep2_cell = aggregate_cells(sweep2_runs, ["membership_benefit_threat", "exit_opportunity_base"])

    sweep1_csv = summary_dir / "sweep1_cell_medians.csv"
    sweep2_csv = summary_dir / "sweep2_cell_medians.csv"
    sweep1_cell.to_csv(sweep1_csv, index=False)
    sweep2_cell.to_csv(sweep2_csv, index=False)

    if not sweep1_cell.empty:
        heatmap_regime(
            sweep1_cell,
            xcol="threat_coeff",
            ycol="shock_strength",
            title="Sweep1 Regime Map",
            out_path=plots_dir / "sweep1_regime_map.png",
        )
        heatmap_numeric(
            sweep1_cell,
            xcol="threat_coeff",
            ycol="shock_strength",
            val_col="final_exit_rate_median",
            title="Sweep1 Final Exit Rate (median)",
            out_path=plots_dir / "sweep1_exit_rate.png",
        )
        heatmap_numeric(
            sweep1_cell,
            xcol="threat_coeff",
            ycol="shock_strength",
            val_col="final_prevalence_median",
            title="Sweep1 Final Prevalence (median)",
            out_path=plots_dir / "sweep1_prevalence.png",
        )
        heatmap_numeric(
            sweep1_cell,
            xcol="threat_coeff",
            ycol="shock_strength",
            val_col="max_punish_rate_median",
            title="Sweep1 Max Punish Rate (median)",
            out_path=plots_dir / "sweep1_max_punish.png",
        )

    if not sweep2_cell.empty:
        heatmap_regime(
            sweep2_cell,
            xcol="membership_benefit_threat",
            ycol="exit_opportunity_base",
            title="Sweep2 Regime Map",
            out_path=plots_dir / "sweep2_regime_map.png",
        )
        heatmap_numeric(
            sweep2_cell,
            xcol="membership_benefit_threat",
            ycol="exit_opportunity_base",
            val_col="final_exit_rate_median",
            title="Sweep2 Final Exit Rate (median)",
            out_path=plots_dir / "sweep2_exit_rate.png",
        )
        heatmap_numeric(
            sweep2_cell,
            xcol="membership_benefit_threat",
            ycol="exit_opportunity_base",
            val_col="final_prevalence_median",
            title="Sweep2 Final Prevalence (median)",
            out_path=plots_dir / "sweep2_prevalence.png",
        )
        heatmap_numeric(
            sweep2_cell,
            xcol="membership_benefit_threat",
            ycol="exit_opportunity_base",
            val_col="max_punish_rate_median",
            title="Sweep2 Max Punish Rate (median)",
            out_path=plots_dir / "sweep2_max_punish.png",
        )

    memo = []
    memo.append("# RESULTS BOUNDARIES\n")
    memo.append(f"Root: `{root}`")
    memo.append("")
    memo.append(boundary_note(sweep1_cell, "sweep1", "threat_coeff", "shock_strength"))
    memo.append("")
    memo.append(boundary_note(sweep2_cell, "sweep2", "membership_benefit_threat", "exit_opportunity_base"))
    memo.append("")

    for name, df in [("sweep1", sweep1_cell), ("sweep2", sweep2_cell)]:
        if df.empty:
            continue
        counts = df["regime"].value_counts().reindex(REGIME_ORDER, fill_value=0)
        memo.append(f"## {name} counts")
        for regime in REGIME_ORDER:
            memo.append(f"- {regime}: {int(counts[regime])}")
        memo.append("")

    (summary_dir / "RESULTS_BOUNDARIES.md").write_text("\n".join(memo), encoding="utf-8")

    print(f"Wrote {sweep1_csv}")
    print(f"Wrote {sweep2_csv}")
    print(f"Wrote {summary_dir / 'RESULTS_BOUNDARIES.md'}")
    print(f"Wrote plots into {plots_dir}")


if __name__ == "__main__":
    main()
