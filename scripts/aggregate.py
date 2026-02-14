#!/usr/bin/env python3
import argparse
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def parse_prefixed(value: str, prefix: str) -> float | int | None:
    if not value.startswith(prefix):
        return None
    raw = value[len(prefix):]
    try:
        if raw.isdigit():
            return int(raw)
        return float(raw)
    except ValueError:
        return None


def parse_context(root: Path, metrics_path: Path) -> dict[str, Any]:
    rel = metrics_path.relative_to(root)
    parts = rel.parts

    row: dict[str, Any] = {
        "suite": parts[0] if len(parts) > 0 else None,
        "condition": None,
        "seed": None,
        "sigma": None,
        "pi_reward": None,
        "graph": None,
        "metrics_path": str(metrics_path),
    }

    if len(parts) < 2:
        return row

    if parts[0] == "seed_sweep" and len(parts) >= 4:
        row["condition"] = parts[1]
        row["seed"] = parse_prefixed(parts[2], "seed_")
    elif parts[0] == "sigma_sweep" and len(parts) >= 3:
        row["sigma"] = parse_prefixed(parts[1], "sigma_")
    elif parts[0] == "pi_sweep" and len(parts) >= 3:
        row["pi_reward"] = parse_prefixed(parts[1], "pi_")
    elif parts[0] == "topology" and len(parts) >= 3:
        row["graph"] = parts[1]

    return row


def save_plot(fig: plt.Figure, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def fmt_or_na(value: Any) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    if isinstance(value, (int,)):
        return str(value)
    return f"{float(value):.3f}"


def threshold(subset: pd.DataFrame, x_col: str, y_col: str, cut: float) -> float | None:
    if subset.empty:
        return None
    s = subset.sort_values(x_col)
    m = s[y_col] > cut
    if not m.any():
        return None
    return float(s.loc[m, x_col].iloc[0])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Batch run root directory, e.g., runs/batch_YYYYMMDD_HHMMSS")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Root path does not exist: {root}")

    metrics_files = sorted(root.rglob("metrics.csv"))
    if not metrics_files:
        raise RuntimeError(f"No metrics.csv files found under {root}")

    rows: list[dict[str, Any]] = []
    for mpath in metrics_files:
        df = pd.read_csv(mpath)
        if df.empty:
            continue

        row = parse_context(root, mpath)
        row.update(df.iloc[-1].to_dict())
        rows.append(row)

    final_df = pd.DataFrame(rows)
    if final_df.empty:
        raise RuntimeError("No final rows were collected from metrics files")

    summary_dir = root / "summary"
    plots_dir = summary_dir / "plots"
    summary_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    final_csv = summary_dir / "final_rows.csv"
    final_parquet = summary_dir / "final_rows.parquet"
    final_df.to_csv(final_csv, index=False)
    final_df.to_parquet(final_parquet, index=False)

    # Plot 1: Seed sweep comparison
    seed_df = final_df[final_df["suite"] == "seed_sweep"].copy()
    if not seed_df.empty:
        for metric in ["fund_prevalence", "punish_rate"]:
            conds = [c for c in ["high_sigma", "low_sigma"] if c in set(seed_df["condition"].dropna().tolist())]
            data = [seed_df.loc[seed_df["condition"] == c, metric].dropna().to_numpy() for c in conds]
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.boxplot(data, labels=conds, showmeans=True)
            ax.set_title(f"Seed Sweep: {metric}")
            ax.set_ylabel(metric)
            save_plot(fig, plots_dir / f"seed_sweep_{metric}_box.png")

    # Plot 2: Sigma sweep
    sigma_df = final_df[final_df["suite"] == "sigma_sweep"].copy()
    if not sigma_df.empty:
        sigma_df = sigma_df.sort_values("sigma")
        for metric in ["fund_prevalence", "punish_rate"]:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot(sigma_df["sigma"], sigma_df[metric], marker="o")
            ax.set_title(f"Sigma Sweep: {metric}")
            ax.set_xlabel("sigma")
            ax.set_ylabel(metric)
            ax.grid(alpha=0.3)
            save_plot(fig, plots_dir / f"sigma_sweep_{metric}.png")

    # Plot 3: Pi sweep
    pi_df = final_df[final_df["suite"] == "pi_sweep"].copy()
    if not pi_df.empty:
        pi_df = pi_df.sort_values("pi_reward")
        for metric in ["fund_prevalence", "punish_rate"]:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot(pi_df["pi_reward"], pi_df[metric], marker="o")
            ax.set_title(f"Pi Sweep: {metric}")
            ax.set_xlabel("pi_reward")
            ax.set_ylabel(metric)
            ax.grid(alpha=0.3)
            save_plot(fig, plots_dir / f"pi_sweep_{metric}.png")

    # Plot 4: Topology bars
    topo_df = final_df[final_df["suite"] == "topology"].copy()
    if not topo_df.empty:
        topo_df = topo_df.sort_values("graph")
        for metric in ["fund_prevalence", "punish_rate"]:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.bar(topo_df["graph"], topo_df[metric])
            ax.set_title(f"Topology: {metric}")
            ax.set_xlabel("graph")
            ax.set_ylabel(metric)
            ax.grid(axis="y", alpha=0.3)
            save_plot(fig, plots_dir / f"topology_{metric}.png")

    # Memo stats
    seed_stats = None
    if not seed_df.empty:
        seed_stats = (
            seed_df.groupby("condition")[["fund_prevalence", "punish_rate"]]
            .agg(["mean", "std", lambda s: s.quantile(0.25), "median", lambda s: s.quantile(0.75)])
        )

    sigma_thr_02 = threshold(sigma_df, "sigma", "fund_prevalence", 0.2) if not sigma_df.empty else None
    sigma_thr_05 = threshold(sigma_df, "sigma", "fund_prevalence", 0.5) if not sigma_df.empty else None
    pi_thr_02 = threshold(pi_df, "pi_reward", "fund_prevalence", 0.2) if not pi_df.empty else None
    pi_thr_05 = threshold(pi_df, "pi_reward", "fund_prevalence", 0.5) if not pi_df.empty else None

    topo_rank_f = []
    topo_rank_p = []
    if not topo_df.empty:
        topo_rank_f = topo_df.sort_values("fund_prevalence", ascending=False)[["graph", "fund_prevalence"]].values.tolist()
        topo_rank_p = topo_df.sort_values("punish_rate", ascending=False)[["graph", "punish_rate"]].values.tolist()

    baseline_high = None
    baseline_low = None
    high_path = Path("runs/high_sigma/metrics.csv")
    low_path = Path("runs/low_sigma/metrics.csv")
    if high_path.exists():
        baseline_high = pd.read_csv(high_path).iloc[-1].to_dict()
    if low_path.exists():
        baseline_low = pd.read_csv(low_path).iloc[-1].to_dict()

    lines: list[str] = []
    lines.append("# Results Memo")
    lines.append("")
    lines.append(f"Batch root: `{root}`")
    lines.append("")
    lines.append("## Executed Grids")
    lines.append("- Suite A (seed sweep): conditions `high_sigma` and `low_sigma`, seeds 1..30, steps=450, n=350, graph=scale_free.")
    lines.append("- Suite B (sigma sweep): sigma from 0.00 to 1.00 in 0.05 increments, seed=1, fixed v_obs=0.95, a_obs=0.03, pi_reward=0.24, lam_punish=0.28.")
    lines.append("- Suite C (pi sweep): pi_reward from 0.00 to 0.30 in 0.02 increments, seed=1, fixed sigma=0.80, v_obs=0.95, a_obs=0.03, lam_punish=0.28.")
    lines.append("- Suite D (topology): graph in {scale_free, small_world, erdos_renyi}, seed=1, fixed sigma=0.80, v_obs=0.95, a_obs=0.03, pi_reward=0.24, lam_punish=0.28.")
    lines.append("")

    lines.append("## Main Statements")
    if seed_stats is not None:
        for cond in ["high_sigma", "low_sigma"]:
            if cond in seed_stats.index:
                row = seed_stats.loc[cond]
                fp_mean = row[("fund_prevalence", "mean")]
                fp_std = row[("fund_prevalence", "std")]
                fp_q25 = row[("fund_prevalence", "<lambda_0>")]
                fp_q50 = row[("fund_prevalence", "median")]
                fp_q75 = row[("fund_prevalence", "<lambda_1>")]
                pr_mean = row[("punish_rate", "mean")]
                pr_std = row[("punish_rate", "std")]
                pr_q25 = row[("punish_rate", "<lambda_0>")]
                pr_q50 = row[("punish_rate", "median")]
                pr_q75 = row[("punish_rate", "<lambda_1>")]
                lines.append(
                    f"- Seed sweep `{cond}`: fund_prevalence mean={fp_mean:.3f}, std={fp_std:.3f}, q25/median/q75={fp_q25:.3f}/{fp_q50:.3f}/{fp_q75:.3f}; "
                    f"punish_rate mean={pr_mean:.3f}, std={pr_std:.3f}, q25/median/q75={pr_q25:.3f}/{pr_q50:.3f}/{pr_q75:.3f}."
                )

    lines.append(
        f"- Sigma threshold estimates (fund_prevalence): smallest sigma with >0.2 is {fmt_or_na(sigma_thr_02)}; with >0.5 is {fmt_or_na(sigma_thr_05)}."
    )
    lines.append(
        f"- Pi threshold estimates (fund_prevalence): smallest pi_reward with >0.2 is {fmt_or_na(pi_thr_02)}; with >0.5 is {fmt_or_na(pi_thr_05)}."
    )

    if topo_rank_f:
        rank_f = ", ".join([f"{g} ({v:.3f})" for g, v in topo_rank_f])
        rank_p = ", ".join([f"{g} ({v:.3f})" for g, v in topo_rank_p])
        lines.append(f"- Topology ranking by fund_prevalence: {rank_f}.")
        lines.append(f"- Topology ranking by punish_rate: {rank_p}.")

    lines.append("")
    lines.append("## Sanity Check Anchor")
    if baseline_high is not None and baseline_low is not None:
        lines.append(
            f"- Previous baseline high_sigma final row: fund_prevalence={baseline_high.get('fund_prevalence', float('nan')):.3f}, "
            f"punish_rate={baseline_high.get('punish_rate', float('nan')):.3f}."
        )
        lines.append(
            f"- Previous baseline low_sigma final row: fund_prevalence={baseline_low.get('fund_prevalence', float('nan')):.3f}, "
            f"punish_rate={baseline_low.get('punish_rate', float('nan')):.3f}."
        )
    else:
        lines.append("- Baseline files `runs/high_sigma/metrics.csv` and/or `runs/low_sigma/metrics.csv` not found.")

    results_md = summary_dir / "RESULTS.md"
    results_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote: {final_csv}")
    print(f"Wrote: {final_parquet}")
    print(f"Wrote plots in: {plots_dir}")
    print(f"Wrote memo: {results_md}")


if __name__ == "__main__":
    main()
