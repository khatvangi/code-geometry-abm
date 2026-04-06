#!/usr/bin/env python3
"""experiment 3: intensity gate (punish_floor) sensitivity.

uses the v2.7 endogenous delta model to vary punish_floor and test
whether the drift-to-capture result is robust to the gate threshold.
"""
import math
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

# v2.7 model has eta_delta_drift and punish_floor
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

# drift specification from the prompt
SIGMA = 0.95
PI_REWARD = 0.25
ETA = 0.10
DELTA0 = 0.2

FLOOR_VALUES = [0.04, 0.06, 0.08, 0.10, 0.12, 0.15]
N_SEEDS = 30
N_STEPS = 450
N_AGENTS = 350
WORKERS = 20


def run_one(run_dir, seed, punish_floor):
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
        "--sigma", f"{SIGMA:.2f}",
        "--pi_reward", f"{PI_REWARD:.2f}",
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
        # v2.7-specific: drift parameters
        "--eta_delta_drift", f"{ETA:.2f}",
        "--punish_floor", f"{punish_floor:.2f}",
        "--delta_outside_degrade", f"{DELTA0:.2f}",
        "--no_movie",
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def collect_rows(root):
    rows = []
    for mpath in sorted(root.rglob("metrics.csv")):
        seed_dir = mpath.parent
        agent_path = seed_dir / "agent_summary.csv"
        if not agent_path.exists():
            continue

        parts = mpath.relative_to(root).parts
        try:
            floor_val = float(parts[0].split("_", 1)[1])
            seed = int(parts[1].split("_", 1)[1])
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
            punish_floor=floor_val, seed=seed,
            regime_hier=regime,
            final_delta=final_delta,
            median_exit_rate=exit_rate,
            final_fund_prevalence=prev,
            max_punish=max_punish,
        ))
    return pd.DataFrame(rows)


def main():
    results_root = Path(__file__).resolve().parent.parent / "results" / "ablation_gate"
    results_root.mkdir(parents=True, exist_ok=True)

    tasks = []
    for floor_val in FLOOR_VALUES:
        for seed in range(1, N_SEEDS + 1):
            run_dir = results_root / f"floor_{floor_val:.2f}" / f"seed_{seed:02d}"
            tasks.append((run_dir, seed, floor_val))

    print(f"running {len(tasks)} simulations (workers={WORKERS})")
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(run_one, rd, s, f) for rd, s, f in tasks]
        for fut in as_completed(futs):
            fut.result()
            done += 1
            if done % 10 == 0 or done == len(tasks):
                print(f"  {done}/{len(tasks)}")

    df = collect_rows(results_root)
    df.to_csv(results_root / "summary.csv", index=False)

    # summary table by floor
    summary_rows = []
    for floor_val, g in df.groupby("punish_floor"):
        summary_rows.append(dict(
            punish_floor=floor_val,
            n_seeds=len(g),
            n_collapse=(g["regime_hier"] == "COLLAPSE").sum(),
            n_capture=(g["regime_hier"] == "CAPTURE").sum(),
            n_mixed=(g["regime_hier"] == "MIXED").sum(),
            n_quiet=(g["regime_hier"] == "QUIET").sum(),
            median_final_delta=g["final_delta"].median(),
            median_exit_rate=g["median_exit_rate"].median(),
            median_fund_prevalence=g["final_fund_prevalence"].median(),
        ))
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(results_root / "summary_by_floor.csv", index=False)
    print(f"\nwrote {results_root / 'summary_by_floor.csv'}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
