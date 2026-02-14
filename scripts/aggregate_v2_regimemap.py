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


def parse_seed(part: str):
    m = re.match(r"seed_(\d+)", part)
    return int(m.group(1)) if m else None


def parse_value(prefix: str, part: str):
    m = re.match(rf"{re.escape(prefix)}_(\d+\.\d+)", part)
    return float(m.group(1)) if m else None


def read_runs(root: Path):
    rows = []
    for p in sorted(root.rglob("metrics.csv")):
        parts = p.parts
        sweep = None
        param_value = None
        seed = None
        for part in parts:
            if part == "exit_cost_sweep":
                sweep = "exit_cost"
            elif part == "heresy_weight_sweep":
                sweep = "w_heresy"
            elif part.startswith("exit_cost_"):
                param_value = parse_value("exit_cost", part)
            elif part.startswith("w_heresy_"):
                param_value = parse_value("w_heresy", part)
            elif part.startswith("seed_"):
                seed = parse_seed(part)

        if sweep is None or param_value is None or seed is None:
            continue

        df = pd.read_csv(p)
        if df.empty:
            continue
        final = df.iloc[-1]
        max_pun_idx = int(df["punish_rate"].idxmax()) if "punish_rate" in df.columns else 0
        rows.append(
            {
                "sweep": sweep,
                "param_value": float(param_value),
                "seed": int(seed),
                "metrics_path": str(p),
                "final_fund_prevalence": float(final.get("fund_prevalence", np.nan)),
                "final_punish_rate": float(final.get("punish_rate", np.nan)),
                "final_exit_rate": float(final.get("exit_rate", np.nan)),
                "max_punish_rate": float(df["punish_rate"].max()) if "punish_rate" in df.columns else np.nan,
                "t_at_max_punish": float(df.loc[max_pun_idx, "t"]) if "t" in df.columns else np.nan,
                "final_y0": float(final.get("y0", np.nan)),
                "final_mean_y": float(final.get("mean_y", np.nan)),
                "y0_drift": float(final.get("y0", np.nan) - 0.50) if "y0" in df.columns else np.nan,
            }
        )
    return pd.DataFrame(rows)


def agg_curve(df: pd.DataFrame):
    grouped = df.groupby("param_value", as_index=False)
    out = grouped.agg(
        n_runs=("seed", "count"),
        final_fund_prevalence_mean=("final_fund_prevalence", "mean"),
        final_fund_prevalence_median=("final_fund_prevalence", "median"),
        final_fund_prevalence_sd=("final_fund_prevalence", "std"),
        final_punish_rate_mean=("final_punish_rate", "mean"),
        final_punish_rate_median=("final_punish_rate", "median"),
        final_exit_rate_mean=("final_exit_rate", "mean"),
        final_exit_rate_median=("final_exit_rate", "median"),
        max_punish_rate_mean=("max_punish_rate", "mean"),
        max_punish_rate_median=("max_punish_rate", "median"),
        t_at_max_punish_mean=("t_at_max_punish", "mean"),
        final_y0_mean=("final_y0", "mean"),
        final_mean_y_mean=("final_mean_y", "mean"),
        y0_drift_mean=("y0_drift", "mean"),
    )
    return out.sort_values("param_value").reset_index(drop=True)


def first_value_where(df: pd.DataFrame, col: str, cond):
    for _, row in df.iterrows():
        v = row[col]
        if cond(v):
            return float(row["param_value"])
    return None


def fmt(x):
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return "n/a"
    return f"{x:.3f}"


def main():
    args = parse_args()
    root = Path(args.root).resolve()
    summary_dir = root / "summary"
    plots_dir = summary_dir / "plots"
    summary_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    runs = read_runs(root)
    if runs.empty:
        raise RuntimeError(f"No sweep metrics found under {root}")

    runs.to_csv(summary_dir / "regimemap_runs.csv", index=False)

    exit_runs = runs[runs["sweep"] == "exit_cost"].copy()
    w_runs = runs[runs["sweep"] == "w_heresy"].copy()

    exit_curve = agg_curve(exit_runs)
    w_curve = agg_curve(w_runs)

    exit_curve.to_csv(summary_dir / "exit_cost_curve.csv", index=False)
    w_curve.to_csv(summary_dir / "w_heresy_curve.csv", index=False)

    # Plots for exit_cost sweep
    plt.figure(figsize=(7.2, 4.6), dpi=140)
    plt.plot(exit_curve["param_value"], exit_curve["final_exit_rate_median"], marker="o")
    plt.xlabel("exit_cost")
    plt.ylabel("median final exit_rate")
    plt.title("Exit Cost vs Final Exit Rate")
    plt.tight_layout()
    plt.savefig(plots_dir / "exit_cost_vs_exit_rate.png", bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(7.2, 4.6), dpi=140)
    plt.plot(exit_curve["param_value"], exit_curve["final_fund_prevalence_median"], marker="o")
    plt.xlabel("exit_cost")
    plt.ylabel("median final prevalence")
    plt.title("Exit Cost vs Final Prevalence")
    plt.tight_layout()
    plt.savefig(plots_dir / "exit_cost_vs_prevalence.png", bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(7.2, 4.6), dpi=140)
    plt.plot(exit_curve["param_value"], exit_curve["max_punish_rate_median"], marker="o")
    plt.xlabel("exit_cost")
    plt.ylabel("median max punish_rate")
    plt.title("Exit Cost vs Max Punish Rate")
    plt.tight_layout()
    plt.savefig(plots_dir / "exit_cost_vs_max_punish.png", bbox_inches="tight")
    plt.close()

    # Plots for heresy weight sweep
    plt.figure(figsize=(7.2, 4.6), dpi=140)
    plt.plot(w_curve["param_value"], w_curve["max_punish_rate_median"], marker="o")
    plt.xlabel("w_heresy")
    plt.ylabel("median max punish_rate")
    plt.title("Heresy Weight vs Max Punish")
    plt.tight_layout()
    plt.savefig(plots_dir / "w_heresy_vs_max_punish.png", bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(7.2, 4.6), dpi=140)
    plt.plot(w_curve["param_value"], w_curve["y0_drift_mean"], marker="o")
    plt.xlabel("w_heresy")
    plt.ylabel("mean y0 drift (final y0 - 0.5)")
    plt.title("Heresy Weight vs Orthodoxy Drift")
    plt.tight_layout()
    plt.savefig(plots_dir / "w_heresy_vs_y0_drift.png", bbox_inches="tight")
    plt.close()

    # Thresholds and memo
    exit_cost_half_exit = first_value_where(exit_curve, "final_exit_rate_median", lambda x: x < 0.5)
    exit_cost_capture = first_value_where(exit_curve, "final_fund_prevalence_median", lambda x: x > 0.5)

    w0 = w_curve[np.isclose(w_curve["param_value"], 0.0)]
    w1 = w_curve[np.isclose(w_curve["param_value"], 1.0)]
    amp_ratio = None
    amp_slope = None
    if not w0.empty and not w1.empty:
        y0 = float(w0.iloc[0]["max_punish_rate_median"])
        y1 = float(w1.iloc[0]["max_punish_rate_median"])
        amp_ratio = (y1 / y0) if y0 > 0 else np.nan
        amp_slope = (y1 - y0) / 1.0

    memo = []
    memo.append("# RESULTS REGIMEMAP")
    memo.append("")
    memo.append(f"Batch root: `{root}`")
    memo.append("")
    memo.append("## Exit-Cost Thresholds")
    memo.append(f"- exit_cost* (median final exit_rate < 0.5): {fmt(exit_cost_half_exit)}")
    memo.append(f"- exit_cost* (median final prevalence > 0.5): {fmt(exit_cost_capture)}")
    memo.append("")
    memo.append("## Heresy Amplification")
    memo.append(f"- max-punish ratio at w_heresy=1.0 vs 0.0 (median): {fmt(amp_ratio)}")
    memo.append(f"- max-punish slope across w_heresy span (median difference): {fmt(amp_slope)}")
    memo.append("")
    memo.append("## Artifacts")
    memo.append("- summary/exit_cost_curve.csv")
    memo.append("- summary/w_heresy_curve.csv")
    memo.append("- summary/plots/exit_cost_vs_exit_rate.png")
    memo.append("- summary/plots/exit_cost_vs_prevalence.png")
    memo.append("- summary/plots/exit_cost_vs_max_punish.png")
    memo.append("- summary/plots/w_heresy_vs_max_punish.png")
    memo.append("- summary/plots/w_heresy_vs_y0_drift.png")

    (summary_dir / "RESULTS_REGIMEMAP.md").write_text("\n".join(memo) + "\n", encoding="utf-8")

    print(f"Wrote {summary_dir / 'exit_cost_curve.csv'}")
    print(f"Wrote {summary_dir / 'w_heresy_curve.csv'}")
    print(f"Wrote {summary_dir / 'RESULTS_REGIMEMAP.md'}")
    print(f"Wrote plots into {plots_dir}")


if __name__ == "__main__":
    main()
