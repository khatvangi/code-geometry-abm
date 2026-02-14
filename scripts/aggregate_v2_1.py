#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ORDER = ["S1_prime", "S2_prime", "S4_prime"]


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=str)
    return ap.parse_args()


def parse_seed(name: str):
    m = re.match(r"seed_(\d+)", name)
    return int(m.group(1)) if m else None


def baseline_from_v2():
    baseline_root_file = Path("runs/_meta/last_batch_v2_heresy_apostasy_root.txt")
    if not baseline_root_file.exists():
        return None, None
    root = Path(baseline_root_file.read_text(encoding="utf-8").strip())
    summary_csv = root / "summary" / "scenario_summary.csv"
    if not summary_csv.exists():
        return str(root), None
    df = pd.read_csv(summary_csv)
    return str(root), df


def main():
    args = parse_args()
    root = Path(args.root).resolve()
    summary_dir = root / "summary"
    plots_dir = summary_dir / "plots"
    summary_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    ts_frames = []
    for p in sorted(root.glob("S*_prime/seed_*/metrics.csv")):
        scenario = p.parent.parent.name
        seed = parse_seed(p.parent.name)
        if seed is None:
            continue
        df = pd.read_csv(p)
        if df.empty:
            continue
        final = df.iloc[-1]
        rows.append(
            {
                "scenario": scenario,
                "seed": seed,
                "metrics_path": str(p),
                "final_fund_prevalence": float(final.get("fund_prevalence", np.nan)),
                "final_punish_rate": float(final.get("punish_rate", np.nan)),
                "final_exit_rate": float(final.get("exit_rate", np.nan)),
                "max_punish_rate": float(df["punish_rate"].max()) if "punish_rate" in df.columns else np.nan,
            }
        )

        keep = [c for c in ["t", "exit_rate", "punish_rate", "threat", "pi_reward", "lam_punish"] if c in df.columns]
        dft = df[keep].copy()
        dft["scenario"] = scenario
        dft["seed"] = seed
        ts_frames.append(dft)

    if not rows:
        raise RuntimeError(f"No runs found under {root}")

    run_df = pd.DataFrame(rows)
    run_df["scenario"] = pd.Categorical(run_df["scenario"], categories=ORDER, ordered=True)
    run_df = run_df.sort_values(["scenario", "seed"]).reset_index(drop=True)
    run_df.to_csv(summary_dir / "final_by_run.csv", index=False)

    summary = run_df.groupby("scenario", observed=False).agg(
        n_runs=("seed", "count"),
        final_fund_prevalence_mean=("final_fund_prevalence", "mean"),
        final_fund_prevalence_sd=("final_fund_prevalence", "std"),
        final_exit_rate_mean=("final_exit_rate", "mean"),
        final_exit_rate_sd=("final_exit_rate", "std"),
        max_punish_rate_mean=("max_punish_rate", "mean"),
        max_punish_rate_sd=("max_punish_rate", "std"),
    ).reset_index().sort_values("scenario")
    summary.to_csv(summary_dir / "scenario_summary.csv", index=False)

    ts = pd.concat(ts_frames, ignore_index=True)
    ts_mean = ts.groupby(["scenario", "t"], observed=False).mean(numeric_only=True).reset_index()
    ts_mean["scenario"] = pd.Categorical(ts_mean["scenario"], categories=ORDER, ordered=True)
    ts_mean = ts_mean.sort_values(["scenario", "t"]).reset_index(drop=True)
    ts_mean.to_csv(summary_dir / "timeseries_mean.csv", index=False)

    # Plot exit_rate mean over time for S2' and S4'
    plt.figure(figsize=(8.2, 4.8), dpi=140)
    for sc in ["S2_prime", "S4_prime"]:
        d = ts_mean[ts_mean["scenario"] == sc]
        if d.empty:
            continue
        plt.plot(d["t"], d["exit_rate"], label=sc)
    plt.xlabel("t")
    plt.ylabel("exit_rate")
    plt.title("v2.1 Exit Rate Over Time")
    plt.legend()
    plt.tight_layout()
    plt.savefig(plots_dir / "exit_rate_over_time_S2p_S4p.png", bbox_inches="tight")
    plt.close()

    # Punish rate overlays
    plt.figure(figsize=(8.2, 4.8), dpi=140)
    for sc in ORDER:
        d = ts_mean[ts_mean["scenario"] == sc]
        if d.empty:
            continue
        plt.plot(d["t"], d["punish_rate"], label=sc)
    plt.xlabel("t")
    plt.ylabel("punish_rate")
    plt.title("v2.1 Punish Rate Over Time")
    plt.legend()
    plt.tight_layout()
    plt.savefig(plots_dir / "punish_rate_over_time_overlay.png", bbox_inches="tight")
    plt.close()

    baseline_root, baseline_df = baseline_from_v2()

    def get_summary(scenario, col):
        d = summary[summary["scenario"] == scenario]
        return float(d.iloc[0][col]) if not d.empty else np.nan

    s2_exit = get_summary("S2_prime", "final_exit_rate_mean")
    s2_prev = get_summary("S2_prime", "final_fund_prevalence_mean")
    s2_maxp = get_summary("S2_prime", "max_punish_rate_mean")
    s4_exit = get_summary("S4_prime", "final_exit_rate_mean")
    s4_prev = get_summary("S4_prime", "final_fund_prevalence_mean")
    s4_maxp = get_summary("S4_prime", "max_punish_rate_mean")
    s1_exit = get_summary("S1_prime", "final_exit_rate_mean")

    lines = []
    lines.append("# RESULTS V2.1")
    lines.append("")
    lines.append("- S2' mean final exit_rate={:.3f}, mean final prevalence={:.3f}, mean max punish_rate={:.3f}.".format(s2_exit, s2_prev, s2_maxp))
    lines.append("- S4' mean final exit_rate={:.3f}, mean final prevalence={:.3f}, mean max punish_rate={:.3f}.".format(s4_exit, s4_prev, s4_maxp))
    lines.append("- S1' sanity (exit disabled) mean final exit_rate={:.3f}.".format(s1_exit))

    if baseline_df is not None:
        try:
            b2 = baseline_df[baseline_df["scenario"] == "S2_controller_exit"].iloc[0]
            b4 = baseline_df[baseline_df["scenario"] == "S4_low_legibility_controller"].iloc[0]
            lines.append("- Baseline v2 root: `{}`".format(baseline_root))
            lines.append("- Baseline S2: exit={:.3f}, prevalence={:.3f}, max_punish={:.3f}.".format(
                float(b2.get("exit_rate_final_mean", np.nan)),
                float(b2.get("fund_prevalence_final_mean", np.nan)),
                float(b2.get("max_punish_rate_mean", np.nan)),
            ))
            lines.append("- Baseline S4: exit={:.3f}, prevalence={:.3f}, max_punish={:.3f}.".format(
                float(b4.get("exit_rate_final_mean", np.nan)),
                float(b4.get("fund_prevalence_final_mean", np.nan)),
                float(b4.get("max_punish_rate_mean", np.nan)),
            ))
            lines.append("- Delta S2 exit (v2.1-v2)={:+.3f}; Delta S4 exit (v2.1-v2)={:+.3f}.".format(
                s2_exit - float(b2.get("exit_rate_final_mean", np.nan)),
                s4_exit - float(b4.get("exit_rate_final_mean", np.nan)),
            ))
        except Exception:
            lines.append("- Baseline v2 summary present but could not parse all scenario rows.")
    else:
        lines.append("- Baseline v2 summary unavailable.")

    (summary_dir / "RESULTS_V2_1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {summary_dir / 'scenario_summary.csv'}")
    print(f"Wrote {summary_dir / 'timeseries_mean.csv'}")
    print(f"Wrote {summary_dir / 'RESULTS_V2_1.md'}")
    print(f"Wrote plots into {plots_dir}")


if __name__ == "__main__":
    main()
