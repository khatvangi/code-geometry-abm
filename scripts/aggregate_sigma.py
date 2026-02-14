#!/usr/bin/env python3
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def parse_sigma_from_path(path: Path) -> float | None:
    for part in path.parts:
        if part.startswith("sigma_"):
            try:
                return float(part.split("_", 1)[1])
            except ValueError:
                continue
    return None


def detect_activation_band(curve: pd.DataFrame, threshold: float = 0.2) -> tuple[float, float] | None:
    if curve.empty:
        return None
    c = curve.sort_values("sigma").reset_index(drop=True)
    above = c["fund_prevalence_mean"] > threshold
    if not above.any():
        return None

    idx_high = int(np.argmax(above.to_numpy()))
    sigma_high = float(c.loc[idx_high, "sigma"])
    if idx_high == 0:
        sigma_low = max(0.0, sigma_high - 0.05)
    else:
        sigma_low = float(c.loc[idx_high - 1, "sigma"])

    if sigma_low > sigma_high:
        sigma_low, sigma_high = sigma_high, sigma_low
    return sigma_low, sigma_high


def first_sigma_over(curve: pd.DataFrame, threshold: float) -> float | None:
    if curve.empty:
        return None
    c = curve.sort_values("sigma")
    m = c["fund_prevalence_mean"] > threshold
    if not m.any():
        return None
    return float(c.loc[m, "sigma"].iloc[0])


def fmt_or_na(v: float | None) -> str:
    return "n/a" if v is None else f"{v:.2f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="batch root path")
    ap.add_argument("--suite", default="sigma_sweep", help="suite folder under root")
    ap.add_argument("--out-prefix", default="sigma", help="prefix for output files")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    suite_dir = root / args.suite
    if not suite_dir.exists():
        raise FileNotFoundError(f"Suite directory not found: {suite_dir}")

    records = []
    for metrics_path in sorted(suite_dir.rglob("metrics.csv")):
        sigma = parse_sigma_from_path(metrics_path)
        if sigma is None:
            continue
        df = pd.read_csv(metrics_path)
        if df.empty:
            continue

        final = df.iloc[-1]
        act = df.loc[df["fund_prevalence"] > 0.2, "t"]
        t_activation = float(act.iloc[0]) if not act.empty else np.nan
        records.append(
            {
                "sigma": sigma,
                "fund_prevalence": float(final["fund_prevalence"]),
                "punish_rate": float(final["punish_rate"]),
                "t_activation": t_activation,
                "metrics_path": str(metrics_path),
            }
        )

    if not records:
        raise RuntimeError(f"No metrics found under {suite_dir}")

    runs_df = pd.DataFrame(records)
    curve = (
        runs_df.groupby("sigma", as_index=False)
        .agg(
            n_runs=("fund_prevalence", "size"),
            fund_prevalence_mean=("fund_prevalence", "mean"),
            fund_prevalence_sd=("fund_prevalence", "std"),
            punish_rate_mean=("punish_rate", "mean"),
            punish_rate_sd=("punish_rate", "std"),
            t_activation_mean=("t_activation", "mean"),
            t_activation_sd=("t_activation", "std"),
        )
        .sort_values("sigma")
    )

    summary_dir = root / "summary"
    plots_dir = summary_dir / "plots"
    summary_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    runs_path = summary_dir / f"{args.out_prefix}_runs.csv"
    curve_path = summary_dir / f"{args.out_prefix}_curve.csv"
    runs_df.to_csv(runs_path, index=False)
    curve.to_csv(curve_path, index=False)

    # Requested canonical names for coarse sweep.
    if args.out_prefix == "sigma":
        curve.to_csv(summary_dir / "sigma_curve.csv", index=False)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.errorbar(
        curve["sigma"],
        curve["fund_prevalence_mean"],
        yerr=curve["fund_prevalence_sd"].fillna(0.0),
        marker="o",
        linewidth=1.2,
        capsize=2,
    )
    ax.set_xlabel("sigma")
    ax.set_ylabel("final fund_prevalence (mean +/- sd)")
    ax.set_title(f"Sigma vs Fundamentalism ({args.suite})")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(plots_dir / f"{args.out_prefix}_vs_prevalence.png", dpi=170)
    if args.out_prefix == "sigma":
        fig.savefig(plots_dir / "sigma_vs_prevalence.png", dpi=170)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.errorbar(
        curve["sigma"],
        curve["punish_rate_mean"],
        yerr=curve["punish_rate_sd"].fillna(0.0),
        marker="o",
        linewidth=1.2,
        capsize=2,
    )
    ax.set_xlabel("sigma")
    ax.set_ylabel("final punish_rate (mean +/- sd)")
    ax.set_title(f"Sigma vs Punishment Rate ({args.suite})")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(plots_dir / f"{args.out_prefix}_vs_punishrate.png", dpi=170)
    if args.out_prefix == "sigma":
        fig.savefig(plots_dir / "sigma_vs_punishrate.png", dpi=170)
    plt.close(fig)

    sigma_star_02 = first_sigma_over(curve, 0.2)
    sigma_star_05 = first_sigma_over(curve, 0.5)
    band = detect_activation_band(curve, 0.2)

    band_path = summary_dir / "sigma_activation_band.txt"
    with open(band_path, "w", encoding="utf-8") as f:
        f.write(f"suite={args.suite}\n")
        f.write(f"out_prefix={args.out_prefix}\n")
        f.write(f"sigma_star_02={fmt_or_na(sigma_star_02)}\n")
        f.write(f"sigma_star_05={fmt_or_na(sigma_star_05)}\n")
        if band is None:
            f.write("sigma_low=n/a\n")
            f.write("sigma_high=n/a\n")
        else:
            f.write(f"sigma_low={band[0]:.2f}\n")
            f.write(f"sigma_high={band[1]:.2f}\n")

    print(f"Wrote {runs_path}")
    print(f"Wrote {curve_path}")
    print(f"Wrote plots into {plots_dir}")
    print(f"Wrote activation band file {band_path}")


if __name__ == "__main__":
    main()
