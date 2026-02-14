#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=str)
    return ap.parse_args()


def parse_value(prefix: str, text: str):
    m = re.match(rf"{re.escape(prefix)}_(\d+(?:\.\d+)?)", text)
    return float(m.group(1)) if m else None


def parse_seed(text: str):
    m = re.match(r"seed_(\d+)", text)
    return int(m.group(1)) if m else None


def heatmap(pivot: pd.DataFrame, title: str, out: Path):
    arr = pivot.to_numpy(dtype=float)
    xvals = list(pivot.columns)
    yvals = list(pivot.index)
    fig, ax = plt.subplots(figsize=(6.6, 4.6), dpi=140)
    im = ax.imshow(arr, origin="lower", aspect="auto", cmap="viridis", vmin=0.0, vmax=1.0)
    ax.set_xticks(np.arange(len(xvals)))
    ax.set_yticks(np.arange(len(yvals)))
    ax.set_xticklabels([f"{x:.2f}" for x in xvals])
    ax.set_yticklabels([f"{y:.2f}" for y in yvals])
    ax.set_xlabel("shock_strength")
    ax.set_ylabel("exit_cost")
    ax.set_title(title)
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            v = arr[i, j]
            ax.text(j, i, f"{v:.2f}" if np.isfinite(v) else "nan", ha="center", va="center", color="white", fontsize=8)
    fig.colorbar(im, ax=ax, shrink=0.9)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def main():
    args = parse_args()
    root = Path(args.root).resolve()
    summary_dir = root / "summary"
    plots_dir = summary_dir / "plots"
    summary_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    ts_rows = []
    for p in sorted((root / "grid").rglob("metrics.csv")):
        exit_cost = None
        shock = None
        seed = None
        for part in p.parts:
            if part.startswith("exit_"):
                exit_cost = parse_value("exit", part)
            elif part.startswith("shock_"):
                shock = parse_value("shock", part)
            elif part.startswith("seed_"):
                seed = parse_seed(part)
        if exit_cost is None or shock is None or seed is None:
            continue

        df = pd.read_csv(p)
        if df.empty:
            continue
        final = df.iloc[-1]
        rows.append({
            "exit_cost": float(exit_cost),
            "shock_strength": float(shock),
            "seed": int(seed),
            "final_exit_rate": float(final.get("exit_rate", np.nan)),
            "final_prevalence": float(final.get("fund_prevalence", np.nan)),
            "max_punish_rate": float(df["punish_rate"].max()) if "punish_rate" in df.columns else np.nan,
        })

        keep = [c for c in ["t", "exit_rate", "punish_rate"] if c in df.columns]
        if keep:
            dft = df[keep].copy()
            dft["exit_cost"] = float(exit_cost)
            dft["shock_strength"] = float(shock)
            dft["seed"] = int(seed)
            ts_rows.append(dft)

    if not rows:
        raise RuntimeError(f"No confirm runs found under {root}")

    run_df = pd.DataFrame(rows).sort_values(["exit_cost", "shock_strength", "seed"]).reset_index(drop=True)
    run_df.to_csv(summary_dir / "confirm_runs.csv", index=False)

    cell = run_df.groupby(["exit_cost", "shock_strength"], as_index=False).agg(
        n_runs=("seed", "count"),
        final_exit_rate_median=("final_exit_rate", "median"),
        final_prevalence_median=("final_prevalence", "median"),
        max_punish_rate_median=("max_punish_rate", "median"),
        final_exit_rate_mean=("final_exit_rate", "mean"),
        final_prevalence_mean=("final_prevalence", "mean"),
        max_punish_rate_mean=("max_punish_rate", "mean"),
    ).sort_values(["exit_cost", "shock_strength"]).reset_index(drop=True)
    cell.to_csv(summary_dir / "confirm_cell_medians.csv", index=False)

    piv_e = cell.pivot(index="exit_cost", columns="shock_strength", values="final_exit_rate_median").sort_index().sort_index(axis=1)
    piv_p = cell.pivot(index="exit_cost", columns="shock_strength", values="final_prevalence_median").sort_index().sort_index(axis=1)
    piv_m = cell.pivot(index="exit_cost", columns="shock_strength", values="max_punish_rate_median").sort_index().sort_index(axis=1)
    heatmap(piv_e, "Confirm: Median Final Exit Rate", plots_dir / "confirm_heatmap_exit_rate.png")
    heatmap(piv_p, "Confirm: Median Final Prevalence", plots_dir / "confirm_heatmap_prevalence.png")
    heatmap(piv_m, "Confirm: Median Max Punish", plots_dir / "confirm_heatmap_max_punish.png")

    # Time-series overlays aggregated across all cells
    if ts_rows:
        ts = pd.concat(ts_rows, ignore_index=True)
        ts_mean = ts.groupby("t", as_index=False).mean(numeric_only=True)
        ts_mean.to_csv(summary_dir / "confirm_timeseries_mean.csv", index=False)

        plt.figure(figsize=(7.2, 4.5), dpi=140)
        plt.plot(ts_mean["t"], ts_mean["exit_rate"], label="mean exit_rate")
        plt.plot(ts_mean["t"], ts_mean["punish_rate"], label="mean punish_rate")
        plt.xlabel("t")
        plt.ylabel("rate")
        plt.title("Confirm Grid Mean Rates Over Time")
        plt.legend()
        plt.tight_layout()
        plt.savefig(plots_dir / "confirm_mean_rates_over_time.png", bbox_inches="tight")
        plt.close()

    partial = cell[(cell["final_exit_rate_median"] >= 0.2) & (cell["final_exit_rate_median"] <= 0.8)]
    nontrivial = cell[cell["max_punish_rate_median"] >= 0.1]
    both = cell[(cell["final_exit_rate_median"] >= 0.2) & (cell["final_exit_rate_median"] <= 0.8) & (cell["max_punish_rate_median"] >= 0.1)]

    lines = []
    lines.append("# RESULTS V2.3 CONFIRM")
    lines.append("")
    lines.append(f"Batch root: `{root}`")
    lines.append(f"- cells with partial exit [0.2,0.8]: {len(partial)}")
    lines.append(f"- cells with max_punish >= 0.1: {len(nontrivial)}")
    lines.append(f"- cells satisfying both: {len(both)}")
    if not both.empty:
        lines.append("- qualifying cells:")
        for _, r in both.iterrows():
            lines.append(
                "  exit_cost={:.2f}, shock={:.2f}, exit={:.3f}, prevalence={:.3f}, max_punish={:.3f}".format(
                    float(r["exit_cost"]), float(r["shock_strength"]), float(r["final_exit_rate_median"]),
                    float(r["final_prevalence_median"]), float(r["max_punish_rate_median"])
                )
            )

    (summary_dir / "RESULTS_V2_3_CONFIRM.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {summary_dir / 'confirm_cell_medians.csv'}")
    print(f"Wrote {summary_dir / 'RESULTS_V2_3_CONFIRM.md'}")
    print(f"Wrote plots into {plots_dir}")


if __name__ == "__main__":
    main()
