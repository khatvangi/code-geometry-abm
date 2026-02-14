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


def plot_heatmap(pivot: pd.DataFrame, title: str, out_path: Path, vmin=0.0, vmax=1.0):
    xvals = list(pivot.columns)
    yvals = list(pivot.index)
    arr = pivot.to_numpy(dtype=float)

    fig, ax = plt.subplots(figsize=(8.0, 4.8), dpi=140)
    im = ax.imshow(arr, aspect="auto", origin="lower", vmin=vmin, vmax=vmax, cmap="viridis")
    ax.set_xticks(np.arange(len(xvals)))
    ax.set_yticks(np.arange(len(yvals)))
    ax.set_xticklabels([f"{x:.2f}" for x in xvals])
    ax.set_yticklabels([f"{y:.1f}" for y in yvals])
    ax.set_xlabel("shock_strength")
    ax.set_ylabel("exit_cost")
    ax.set_title(title)

    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            val = arr[i, j]
            if np.isnan(val):
                txt = "nan"
            else:
                txt = f"{val:.2f}"
            ax.text(j, i, txt, ha="center", va="center", color="white", fontsize=8)

    fig.colorbar(im, ax=ax, shrink=0.9)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def main():
    args = parse_args()
    root = Path(args.root).resolve()
    summary_dir = root / "summary"
    plots_dir = summary_dir / "plots"
    summary_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    rows = []
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
        rows.append(
            {
                "exit_cost": float(exit_cost),
                "shock_strength": float(shock),
                "seed": int(seed),
                "metrics_path": str(p),
                "final_exit_rate": float(final.get("exit_rate", np.nan)),
                "final_prevalence": float(final.get("fund_prevalence", np.nan)),
                "max_punish_rate": float(df["punish_rate"].max()) if "punish_rate" in df.columns else np.nan,
                "final_punish_rate": float(final.get("punish_rate", np.nan)),
            }
        )

    if not rows:
        raise RuntimeError(f"No grid metrics found under {root}")

    runs = pd.DataFrame(rows)
    runs = runs.sort_values(["exit_cost", "shock_strength", "seed"]).reset_index(drop=True)
    runs.to_csv(summary_dir / "grid_runs.csv", index=False)

    cell = runs.groupby(["exit_cost", "shock_strength"], as_index=False).agg(
        n_runs=("seed", "count"),
        final_exit_rate_median=("final_exit_rate", "median"),
        final_exit_rate_mean=("final_exit_rate", "mean"),
        final_prevalence_median=("final_prevalence", "median"),
        final_prevalence_mean=("final_prevalence", "mean"),
        max_punish_rate_median=("max_punish_rate", "median"),
        max_punish_rate_mean=("max_punish_rate", "mean"),
        final_punish_rate_median=("final_punish_rate", "median"),
    )
    cell = cell.sort_values(["exit_cost", "shock_strength"]).reset_index(drop=True)
    cell.to_csv(summary_dir / "grid_cell_medians.csv", index=False)

    # Heatmaps
    piv_exit = cell.pivot(index="exit_cost", columns="shock_strength", values="final_exit_rate_median").sort_index().sort_index(axis=1)
    piv_prev = cell.pivot(index="exit_cost", columns="shock_strength", values="final_prevalence_median").sort_index().sort_index(axis=1)
    piv_pun = cell.pivot(index="exit_cost", columns="shock_strength", values="max_punish_rate_median").sort_index().sort_index(axis=1)

    plot_heatmap(piv_exit, "Median Final Exit Rate", plots_dir / "heatmap_exit_rate.png", vmin=0.0, vmax=1.0)
    plot_heatmap(piv_prev, "Median Final Prevalence", plots_dir / "heatmap_prevalence.png", vmin=0.0, vmax=1.0)
    plot_heatmap(piv_pun, "Median Max Punish Rate", plots_dir / "heatmap_max_punish.png", vmin=0.0, vmax=1.0)

    # Boundary and mixed-zone detection
    nearest = cell.copy()
    nearest["dist_exit_05"] = (nearest["final_exit_rate_median"] - 0.5).abs()
    boundary_row = nearest.sort_values("dist_exit_05").iloc[0]

    prev_over = cell[cell["final_prevalence_median"] > 0.5].copy()
    if prev_over.empty:
        prev_boundary = None
    else:
        prev_boundary = prev_over.sort_values(["exit_cost", "shock_strength"]).iloc[0]

    mixed = cell[
        (cell["final_exit_rate_median"] > 0.2)
        & (cell["final_exit_rate_median"] < 0.8)
        & (cell["final_prevalence_median"] > 0.1)
        & (cell["max_punish_rate_median"] > 0.05)
    ].copy()

    memo = []
    memo.append("# RESULTS V2.2 GRID")
    memo.append("")
    memo.append(f"Batch root: `{root}`")
    memo.append("")
    memo.append("## Boundary Estimates")
    memo.append(
        "- nearest cell to median exit_rate=0.5: exit_cost={:.2f}, shock_strength={:.2f}, median_exit_rate={:.3f}.".format(
            float(boundary_row["exit_cost"]), float(boundary_row["shock_strength"]), float(boundary_row["final_exit_rate_median"])
        )
    )
    if prev_boundary is None:
        memo.append("- prevalence>0.5 boundary: not observed in tested grid.")
    else:
        memo.append(
            "- first cell with median prevalence>0.5: exit_cost={:.2f}, shock_strength={:.2f}, median_prevalence={:.3f}.".format(
                float(prev_boundary["exit_cost"]), float(prev_boundary["shock_strength"]), float(prev_boundary["final_prevalence_median"])
            )
        )

    memo.append("")
    memo.append("## Mixed-Regime Zones")
    if mixed.empty:
        memo.append("- no mixed cells found under current criteria.")
    else:
        for _, r in mixed.iterrows():
            memo.append(
                "- exit_cost={:.2f}, shock={:.2f}, exit={:.3f}, prevalence={:.3f}, max_punish={:.3f}.".format(
                    float(r["exit_cost"]),
                    float(r["shock_strength"]),
                    float(r["final_exit_rate_median"]),
                    float(r["final_prevalence_median"]),
                    float(r["max_punish_rate_median"]),
                )
            )

    memo.append("")
    memo.append("## Acceptance")
    has_partial_exit = bool(((cell["final_exit_rate_median"] > 0.2) & (cell["final_exit_rate_median"] < 0.8)).any())
    has_mixed_membership = bool(((cell["final_prevalence_median"] > 0.1) & (cell["final_prevalence_median"] < 0.9)).any())
    memo.append(f"- partial-exit cells present: {'yes' if has_partial_exit else 'no'}")
    memo.append(f"- mixed membership cells present: {'yes' if has_mixed_membership else 'no'}")

    (summary_dir / "RESULTS_V2_2_GRID.md").write_text("\n".join(memo) + "\n", encoding="utf-8")

    print(f"Wrote {summary_dir / 'grid_cell_medians.csv'}")
    print(f"Wrote {summary_dir / 'RESULTS_V2_2_GRID.md'}")
    print(f"Wrote plots into {plots_dir}")


if __name__ == "__main__":
    main()
