#!/usr/bin/env python3
"""sigma dose-response sweep: fine-grained legibility vs enforcement dynamics.

sweeps sigma (code legibility) across 10 values, 2 pi_reward levels,
drift-on vs drift-off, 30 seeds each = 1200 total runs.
uses the v2.7 endogenous delta model.
"""
import math
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

MODEL = Path(__file__).resolve().parent.parent / "src" / "religion_fundamentalism_abm_v2_7.py"

BEST = dict(
    shock_strength=0.25,
    membership_benefit=0.03,
    membership_benefit_threat=0.10,
    exit_opportunity_threat_coeff=1.5,
    exit_block_exponent=2.5,
    exit_commit_steps=8,
    exit_cost=0.4,
)

SIGMA_VALUES = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95]
PI_VALUES = [0.25, 0.50]

# two drift conditions
DRIFT_CONDITIONS = {
    "drift_on":  dict(eta_delta_drift=0.10, delta_outside_degrade=0.10, punish_floor=0.08),
    "drift_off": dict(eta_delta_drift=0.00, delta_outside_degrade=0.10, punish_floor=0.08),
}

N_SEEDS = 30
N_STEPS = 450
N_AGENTS = 350
WORKERS = 20


def top_share(values, frac):
    x = np.asarray(values, dtype=float)
    total = float(np.sum(x))
    if x.size == 0 or total <= 0:
        return 0.0
    k = max(1, int(math.ceil(frac * x.size)))
    return float(np.sum(np.sort(x)[::-1][:k]) / total)


def run_one(run_dir, seed, sigma, pi_reward, drift_params):
    metrics_path = run_dir / "metrics.csv"
    agent_path = run_dir / "agent_summary.csv"
    if metrics_path.exists() and agent_path.exists():
        return

    run_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, str(MODEL),
        "--outdir", str(run_dir),
        "--steps", str(N_STEPS),
        "--n", str(N_AGENTS),
        "--graph", "scale_free",
        "--seed", str(seed),
        "--sigma", f"{sigma:.2f}",
        "--pi_reward", f"{pi_reward:.2f}",
        "--exit_opportunity_base", "0.30",
        "--exit_threshold", "-1.0",
        "--shock_schedule", "100,220,320",
        "--shock_strength", str(BEST["shock_strength"]),
        "--membership_benefit", str(BEST["membership_benefit"]),
        "--membership_benefit_threat", str(BEST["membership_benefit_threat"]),
        "--exit_opportunity_threat_coeff", str(BEST["exit_opportunity_threat_coeff"]),
        "--exit_block_exponent", str(BEST["exit_block_exponent"]),
        "--exit_commit_steps", str(BEST["exit_commit_steps"]),
        "--exit_cost", str(BEST["exit_cost"]),
        "--enforcer_quota_frac", "0.08",
        "--A_gain_threat", "2.0",
        "--A_enforcer_monopoly", "0.35",
        "--budget_base", "0.15",
        "--budget_threat_gain", "0.60",
        "--cap_decay", "0.005",
        "--cap_gain_per_punish", "0.15",
        "--cap_to_enforcer", "0.25",
        "--cap_max", "2.0",
        "--service_decay", "0.02",
        "--non_enforcer_punish_mult", "0.25",
        "--non_enforcer_punish_eps", "0.02",
        "--enforcer_punish_mult", "1.5",
        "--kappa_cap_discount", "0.20",
        "--enforcer_backlash_mult", "0.25",
        "--enforcer_kappa_mult", "0.30",
        # v2.7 drift parameters
        "--eta_delta_drift", f"{drift_params['eta_delta_drift']:.2f}",
        "--punish_floor", f"{drift_params['punish_floor']:.2f}",
        "--delta_outside_degrade", f"{drift_params['delta_outside_degrade']:.2f}",
        "--no_movie",
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def collect_rows(root):
    """walk results tree: drift_cond/sigma_X/pi_Y/seed_ZZ/"""
    rows = []
    for mpath in sorted(root.rglob("metrics.csv")):
        seed_dir = mpath.parent
        agent_path = seed_dir / "agent_summary.csv"
        if not agent_path.exists():
            continue

        parts = mpath.relative_to(root).parts
        try:
            drift_cond = parts[0]                          # drift_on / drift_off
            sigma = float(parts[1].split("_", 1)[1])      # sigma_0.10
            pi = float(parts[2].split("_", 1)[1])         # pi_0.25
            seed = int(parts[3].split("_", 1)[1])         # seed_01
        except Exception:
            continue

        mdf = pd.read_csv(mpath)
        adf = pd.read_csv(agent_path)
        if mdf.empty:
            continue

        final = mdf.iloc[-1]
        prev = float(final.get("fund_prevalence", np.nan))
        exit_rate = float(final.get("exit_rate", np.nan))
        max_punish = float(mdf["punish_rate"].max()) if "punish_rate" in mdf.columns else np.nan
        final_delta = float(final.get("current_delta", np.nan))

        # punishment concentration
        punish = pd.to_numeric(adf.get("punish_issued", pd.Series(dtype=float)), errors="coerce").fillna(0).values
        is_enf = adf.get("is_enforcer", pd.Series(dtype=bool)).astype(bool).values

        enforcer_total = float(punish[is_enf].sum()) if is_enf.any() else 0.0
        all_total = float(punish.sum())
        enforcer_punish_share = enforcer_total / all_total if all_total > 0 else 0.0

        # regime classification
        if exit_rate >= 0.90:
            regime = "COLLAPSE"
        elif prev >= 0.90 and exit_rate <= 0.20:
            regime = "CAPTURE"
        elif max_punish >= 0.10:
            regime = "MIXED"
        else:
            regime = "QUIET"

        rows.append(dict(
            drift_condition=drift_cond, sigma=sigma, pi_reward=pi, seed=seed,
            final_fund_prevalence=prev,
            final_exit_rate=exit_rate,
            max_punish=max_punish,
            final_delta=final_delta,
            top5_punishment_share=top_share(punish, 0.05),
            top10_punishment_share=top_share(punish, 0.10),
            enforcer_punish_share=enforcer_punish_share,
            regime_hier=regime,
        ))
    return pd.DataFrame(rows)


def build_summary(df):
    """aggregate per (sigma, pi_reward, drift_condition)."""
    gcols = ["sigma", "pi_reward", "drift_condition"]
    summary_rows = []
    for key, g in df.groupby(gcols):
        sigma, pi, drift = key
        n_mixed = int((g["regime_hier"] == "MIXED").sum())
        n_capture = int((g["regime_hier"] == "CAPTURE").sum())
        n_seeds = len(g)
        pct_active = (n_mixed + n_capture) / n_seeds * 100 if n_seeds > 0 else 0.0

        summary_rows.append(dict(
            sigma=sigma,
            pi_reward=pi,
            drift_condition=drift,
            n_seeds=n_seeds,
            median_top5_share=g["top5_punishment_share"].median(),
            median_top10_share=g["top10_punishment_share"].median(),
            median_enforcer_share=g["enforcer_punish_share"].median(),
            median_max_punish=g["max_punish"].median(),
            median_fund_prevalence=g["final_fund_prevalence"].median(),
            median_exit_rate=g["final_exit_rate"].median(),
            median_final_delta=g["final_delta"].median(),
            n_quiet=int((g["regime_hier"] == "QUIET").sum()),
            n_mixed=n_mixed,
            n_collapse=int((g["regime_hier"] == "COLLAPSE").sum()),
            n_capture=n_capture,
            pct_active=round(pct_active, 1),
        ))
    return pd.DataFrame(summary_rows)


def build_text_table(summary_df, results_root):
    """produce a readable text table for quick inspection."""
    lines = []
    for drift in ["drift_on", "drift_off"]:
        sub = summary_df[summary_df["drift_condition"] == drift]
        lines.append(f"=== {drift.upper()} ===")
        lines.append(f"{'sigma':>6}  {'pi':>5}  {'%act':>5}  {'med_t5':>7}  {'med_enf':>8}  {'med_delt':>9}")
        lines.append("-" * 55)
        for _, row in sub.sort_values(["pi_reward", "sigma"]).iterrows():
            # for active-only medians, filter and recompute
            active_mask = summary_df  # not needed here, already aggregated
            lines.append(
                f"{row['sigma']:6.2f}  {row['pi_reward']:5.2f}  "
                f"{row['pct_active']:5.1f}  "
                f"{row['median_top5_share']:7.3f}  "
                f"{row['median_enforcer_share']:8.3f}  "
                f"{row['median_final_delta']:9.4f}"
            )
        lines.append("")

    out = "\n".join(lines)
    out_path = results_root / "dose_response_plot.txt"
    out_path.write_text(out)
    return out


def main():
    results_root = Path(__file__).resolve().parent.parent / "results" / "dose_response"
    results_root.mkdir(parents=True, exist_ok=True)

    # build task list
    tasks = []
    for drift_label, drift_params in DRIFT_CONDITIONS.items():
        for sigma in SIGMA_VALUES:
            for pi in PI_VALUES:
                for seed in range(1, N_SEEDS + 1):
                    run_dir = results_root / drift_label / f"sigma_{sigma:.2f}" / f"pi_{pi:.2f}" / f"seed_{seed:02d}"
                    tasks.append((run_dir, seed, sigma, pi, drift_params))

    print(f"running {len(tasks)} simulations (workers={WORKERS})")
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(run_one, rd, s, sig, pi, dp) for rd, s, sig, pi, dp in tasks]
        for fut in as_completed(futs):
            fut.result()
            done += 1
            if done % 50 == 0 or done == len(tasks):
                print(f"  {done}/{len(tasks)}")

    # collect and summarize
    print("collecting results...")
    df = collect_rows(results_root)
    df.to_csv(results_root / "all_runs.csv", index=False)

    summary = build_summary(df)
    summary.to_csv(results_root / "summary.csv", index=False)
    print(f"\nwrote {results_root / 'summary.csv'} ({len(summary)} rows)")

    txt = build_text_table(summary, results_root)
    print(f"wrote {results_root / 'dose_response_plot.txt'}")
    print("\n" + txt)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
