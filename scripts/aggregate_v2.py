#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


SCENARIO_ORDER = [
    "S0_no_controller_no_exit",
    "S1_controller_no_exit",
    "S2_controller_exit",
    "S3_high_heresy",
    "S4_low_legibility_controller",
]


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=str)
    return ap.parse_args()


def parse_seed(text: str):
    m = re.search(r"seed_(\d+)", text)
    return int(m.group(1)) if m else None


def build_results(final_summary: pd.DataFrame, ts_mean: pd.DataFrame, out_md: Path):
    s = final_summary.set_index("scenario")

    def getv(sc, col, default=np.nan):
        if sc not in s.index or col not in s.columns:
            return default
        return float(s.loc[sc, col])

    s0_prev = getv("S0_no_controller_no_exit", "fund_prevalence_final_mean")
    s1_prev = getv("S1_controller_no_exit", "fund_prevalence_final_mean")
    s2_prev = getv("S2_controller_exit", "fund_prevalence_final_mean")
    s3_prev = getv("S3_high_heresy", "fund_prevalence_final_mean")
    s4_prev = getv("S4_low_legibility_controller", "fund_prevalence_final_mean")

    s1_pun_final = getv("S1_controller_no_exit", "punish_rate_final_mean")
    s2_pun_final = getv("S2_controller_exit", "punish_rate_final_mean")
    s3_pun_final = getv("S3_high_heresy", "punish_rate_final_mean")
    s1_pun_time = getv("S1_controller_no_exit", "mean_punish_rate_time_mean")
    s2_pun_time = getv("S2_controller_exit", "mean_punish_rate_time_mean")
    s3_pun_time = getv("S3_high_heresy", "mean_punish_rate_time_mean")

    s1_exit = getv("S1_controller_no_exit", "exit_rate_final_mean")
    s2_exit = getv("S2_controller_exit", "exit_rate_final_mean")
    s4_exit = getv("S4_low_legibility_controller", "exit_rate_final_mean")

    s1_max_pun = getv("S1_controller_no_exit", "max_punish_rate_mean")
    s2_max_pun = getv("S2_controller_exit", "max_punish_rate_mean")
    s0_max_pun = getv("S0_no_controller_no_exit", "max_punish_rate_mean")

    # Cycle check: post-shock punish in S1 and post-shock exit in S2.
    cycle_lines = []
    spikes = 0
    if not ts_mean.empty:
        s1_ts = ts_mean[ts_mean["scenario"] == "S1_controller_no_exit"].copy()
        s2_ts = ts_mean[ts_mean["scenario"] == "S2_controller_exit"].copy()
        shocks = [100, 220, 320]
        for sh in shocks:
            pre_p = s1_ts[(s1_ts["t"] >= sh - 15) & (s1_ts["t"] < sh)]["punish_rate"].mean()
            post_p = s1_ts[(s1_ts["t"] >= sh) & (s1_ts["t"] < sh + 15)]["punish_rate"].mean()
            d_p = float(post_p - pre_p) if pd.notna(pre_p) and pd.notna(post_p) else np.nan

            pre_e = s2_ts[(s2_ts["t"] >= sh - 15) & (s2_ts["t"] < sh)]["exit_rate"].mean()
            post_e = s2_ts[(s2_ts["t"] >= sh) & (s2_ts["t"] < sh + 15)]["exit_rate"].mean()
            d_e = float(post_e - pre_e) if pd.notna(pre_e) and pd.notna(post_e) else np.nan

            if (pd.notna(d_p) and d_p > 0.005) or (pd.notna(d_e) and d_e > 0.01):
                spikes += 1
            cycle_lines.append((sh, pre_p, post_p, d_p, pre_e, post_e, d_e))

    s3_vs_s1 = s3_pun_time - s1_pun_time if pd.notna(s3_pun_time) and pd.notna(s1_pun_time) else np.nan
    s2_exit_gain = s2_exit - s1_exit if pd.notna(s2_exit) and pd.notna(s1_exit) else np.nan
    s2_spike_attenuation = s1_max_pun - s2_max_pun if pd.notna(s1_max_pun) and pd.notna(s2_max_pun) else np.nan

    accept_heresy = pd.notna(s3_vs_s1) and (s3_vs_s1 > 0)
    accept_apostasy = pd.notna(s2_exit_gain) and pd.notna(s2_spike_attenuation) and (s2_exit_gain > 0) and (s2_spike_attenuation > 0)
    accept_cycle = (spikes >= 1) and pd.notna(s1_max_pun) and pd.notna(s0_max_pun) and (s1_max_pun > s0_max_pun)
    accept_sigma_gate = pd.notna(s4_prev) and (s4_prev < 0.5)

    lines = []
    lines.append("# RESULTS V2")
    lines.append("")
    lines.append("- S0 baseline final prevalence={:.3f}, punish={:.3f}.".format(s0_prev, getv("S0_no_controller_no_exit", "punish_rate_final_mean")))
    lines.append("- S1 controller-only final prevalence={:.3f}, final punish={:.3f}, mean punish over time={:.3f}, max punish={:.3f}.".format(s1_prev, s1_pun_final, s1_pun_time, s1_max_pun))
    lines.append("- S2 controller+exit final prevalence={:.3f}, final punish={:.3f}, mean punish over time={:.3f}, exit={:.3f}, max punish={:.3f}.".format(s2_prev, s2_pun_final, s2_pun_time, s2_exit, s2_max_pun))
    lines.append("- S3 high-heresy final prevalence={:.3f}, final punish={:.3f}, mean punish over time={:.3f}; delta mean punish vs S1={:+.3f}.".format(s3_prev, s3_pun_final, s3_pun_time, s3_vs_s1))
    lines.append("- S4 low-legibility+controller final prevalence={:.3f}, punish={:.3f}, exit={:.3f}.".format(s4_prev, getv("S4_low_legibility_controller", "punish_rate_final_mean"), s4_exit))
    lines.append("- Apostasy attenuation check (S2 vs S1): exit delta={:+.3f}, max-punish delta={:+.3f}.".format(s2_exit_gain, s2_spike_attenuation))

    if cycle_lines:
        for sh, pre_p, post_p, d_p, pre_e, post_e, d_e in cycle_lines:
            lines.append("- Shock t={} punish pre/post: {:.3f}->{:.3f} (d={:+.3f}); exit pre/post: {:.3f}->{:.3f} (d={:+.3f}).".format(
                sh, pre_p, post_p, d_p, pre_e, post_e, d_e
            ))

    lines.append("- Acceptance: heresy_effect={} apostasy_effect={} controller_cycle={} sigma_gate={}.".format(
        "PASS" if accept_heresy else "FAIL",
        "PASS" if accept_apostasy else "FAIL",
        "PASS" if accept_cycle else "FAIL",
        "PASS" if accept_sigma_gate else "FAIL",
    ))

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    args = parse_args()
    root = Path(args.root).resolve()
    summary_dir = root / "summary"
    plots_dir = summary_dir / "plots"
    summary_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    run_rows = []
    ts_rows = []

    for metrics_path in sorted(root.glob("S*/seed_*/metrics.csv")):
        scenario = metrics_path.parent.parent.name
        seed = parse_seed(metrics_path.parent.name)
        if seed is None:
            continue

        df = pd.read_csv(metrics_path)
        if df.empty:
            continue
        final = df.iloc[-1].to_dict()
        row = {
            "scenario": scenario,
            "seed": seed,
            "metrics_path": str(metrics_path),
            "fund_prevalence_final": float(final.get("fund_prevalence", np.nan)),
            "punish_rate_final": float(final.get("punish_rate", np.nan)),
            "exit_rate_final": float(final.get("exit_rate", np.nan)),
            "max_punish_rate": float(df["punish_rate"].max()) if "punish_rate" in df.columns else np.nan,
            "max_exit_rate": float(df["exit_rate"].max()) if "exit_rate" in df.columns else np.nan,
            "mean_punish_rate_time": float(df["punish_rate"].mean()) if "punish_rate" in df.columns else np.nan,
            "mean_exit_rate_time": float(df["exit_rate"].mean()) if "exit_rate" in df.columns else np.nan,
        }
        run_rows.append(row)

        keep_cols = [c for c in ["t", "threat", "pi_reward", "lam_punish", "y0", "exit_rate", "punish_rate", "fund_prevalence"] if c in df.columns]
        if keep_cols:
            dft = df[keep_cols].copy()
            dft["scenario"] = scenario
            dft["seed"] = seed
            ts_rows.append(dft)

    if not run_rows:
        raise RuntimeError(f"No metrics.csv files found under {root}")

    runs = pd.DataFrame(run_rows)
    runs["scenario"] = pd.Categorical(runs["scenario"], categories=SCENARIO_ORDER, ordered=True)
    runs = runs.sort_values(["scenario", "seed"]).reset_index(drop=True)
    runs.to_csv(summary_dir / "final_by_run.csv", index=False)

    grouped = runs.groupby("scenario", observed=False)
    summary = grouped.agg(
        n_runs=("seed", "count"),
        fund_prevalence_final_mean=("fund_prevalence_final", "mean"),
        fund_prevalence_final_sd=("fund_prevalence_final", "std"),
        punish_rate_final_mean=("punish_rate_final", "mean"),
        punish_rate_final_sd=("punish_rate_final", "std"),
        exit_rate_final_mean=("exit_rate_final", "mean"),
        exit_rate_final_sd=("exit_rate_final", "std"),
        max_punish_rate_mean=("max_punish_rate", "mean"),
        max_punish_rate_sd=("max_punish_rate", "std"),
        mean_punish_rate_time_mean=("mean_punish_rate_time", "mean"),
        mean_punish_rate_time_sd=("mean_punish_rate_time", "std"),
        mean_exit_rate_time_mean=("mean_exit_rate_time", "mean"),
        mean_exit_rate_time_sd=("mean_exit_rate_time", "std"),
    ).reset_index()
    summary = summary.sort_values("scenario")
    summary.to_csv(summary_dir / "scenario_summary.csv", index=False)

    if ts_rows:
        ts = pd.concat(ts_rows, ignore_index=True)
        ts_mean = ts.groupby(["scenario", "t"], observed=False).mean(numeric_only=True).reset_index()
        ts_mean["scenario"] = pd.Categorical(ts_mean["scenario"], categories=SCENARIO_ORDER, ordered=True)
        ts_mean = ts_mean.sort_values(["scenario", "t"]).reset_index(drop=True)
        ts_mean.to_csv(summary_dir / "timeseries_mean.csv", index=False)
    else:
        ts_mean = pd.DataFrame()

    # Plot: scenario comparison bars.
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), dpi=140)
    bar_cols = [
        ("fund_prevalence_final_mean", "Final Fund Prevalence"),
        ("punish_rate_final_mean", "Final Punish Rate"),
        ("exit_rate_final_mean", "Final Exit Rate"),
        ("max_punish_rate_mean", "Max Punish Rate"),
    ]
    for ax, (col, title) in zip(axes.ravel(), bar_cols):
        vals = summary[col].astype(float)
        ax.bar(summary["scenario"].astype(str), vals)
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(plots_dir / "scenario_comparison_bars.png", bbox_inches="tight")
    plt.close(fig)

    # Plot: threat vs punish overlay per scenario.
    if not ts_mean.empty:
        fig, axes = plt.subplots(3, 2, figsize=(12, 10), dpi=140, sharex=True)
        axes = axes.ravel()
        for i, sc in enumerate(SCENARIO_ORDER):
            ax = axes[i]
            d = ts_mean[ts_mean["scenario"] == sc]
            if d.empty:
                ax.set_visible(False)
                continue
            x = d["t"].to_numpy()
            ax.plot(x, d.get("punish_rate", pd.Series(index=d.index, dtype=float)).to_numpy(), label="punish_rate", color="#1f77b4")
            if "threat" in d.columns:
                ax2 = ax.twinx()
                ax2.plot(x, d["threat"].to_numpy(), label="threat", color="#d62728", alpha=0.75)
                ax2.set_ylabel("threat", color="#d62728")
            ax.set_title(sc)
            ax.set_ylabel("punish_rate")
        axes[-1].set_visible(False)
        fig.tight_layout()
        fig.savefig(plots_dir / "threat_vs_punish_overlay.png", bbox_inches="tight")
        plt.close(fig)

        # Plot: y0 drift
        plt.figure(figsize=(10, 4.5), dpi=140)
        for sc in SCENARIO_ORDER:
            d = ts_mean[ts_mean["scenario"] == sc]
            if d.empty or "y0" not in d.columns:
                continue
            plt.plot(d["t"], d["y0"], label=sc)
        plt.xlabel("t")
        plt.ylabel("y0")
        plt.title("Orthodoxy Center Drift (y0)")
        plt.legend(fontsize=7, ncol=2)
        plt.tight_layout()
        plt.savefig(plots_dir / "y0_over_time.png", bbox_inches="tight")
        plt.close()

        # Plot: exit rate over time
        plt.figure(figsize=(10, 4.5), dpi=140)
        for sc in SCENARIO_ORDER:
            d = ts_mean[ts_mean["scenario"] == sc]
            if d.empty or "exit_rate" not in d.columns:
                continue
            plt.plot(d["t"], d["exit_rate"], label=sc)
        plt.xlabel("t")
        plt.ylabel("exit_rate")
        plt.title("Exit Rate Over Time")
        plt.legend(fontsize=7, ncol=2)
        plt.tight_layout()
        plt.savefig(plots_dir / "exit_rate_over_time.png", bbox_inches="tight")
        plt.close()

        # Plot: controller outputs over time
        plt.figure(figsize=(10, 4.5), dpi=140)
        for sc in SCENARIO_ORDER:
            d = ts_mean[ts_mean["scenario"] == sc]
            if d.empty or "pi_reward" not in d.columns:
                continue
            plt.plot(d["t"], d["pi_reward"], label=f"{sc}: pi")
        plt.xlabel("t")
        plt.ylabel("pi_reward")
        plt.title("Controller Reward Signal Over Time")
        plt.legend(fontsize=7, ncol=2)
        plt.tight_layout()
        plt.savefig(plots_dir / "pi_reward_over_time.png", bbox_inches="tight")
        plt.close()

    build_results(summary, ts_mean, summary_dir / "RESULTS_V2.md")

    print(f"Wrote {summary_dir / 'final_by_run.csv'}")
    print(f"Wrote {summary_dir / 'scenario_summary.csv'}")
    if not ts_mean.empty:
        print(f"Wrote {summary_dir / 'timeseries_mean.csv'}")
    print(f"Wrote {summary_dir / 'RESULTS_V2.md'}")
    print(f"Wrote plots into {plots_dir}")


if __name__ == "__main__":
    main()
