#!/usr/bin/env python3
"""experiment 2: cadre quota sensitivity.

varies enforcer_quota_frac at a fixed parameter point to show
concentration is not an artifact of the specific 0.08 quota.
"""
import math
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

MODEL = Path(__file__).resolve().parent.parent / "src" / "religion_fundamentalism_abm_v2_5.py"

BEST = dict(
    shock_strength=0.25,
    membership_benefit=0.03,
    membership_benefit_threat=0.10,
    exit_opportunity_threat_coeff=1.5,
    exit_block_exponent=2.5,
    exit_commit_steps=8,
    exit_cost=0.4,
)

# fixed parameter point
SIGMA = 0.75
PI_REWARD = 0.25
BASE_OPP = 0.30
EXIT_THRESHOLD = -1.0

QUOTA_VALUES = [0.04, 0.08, 0.12, 0.16, 0.20, 0.25]
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


def run_one(run_dir, seed, quota):
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
        "--exit_opportunity_base", f"{BASE_OPP:.2f}",
        "--exit_threshold", f"{EXIT_THRESHOLD:.1f}",
        "--shock_schedule", "100,220,320",
        "--shock_strength", str(BEST["shock_strength"]),
        "--membership_benefit", str(BEST["membership_benefit"]),
        "--membership_benefit_threat", str(BEST["membership_benefit_threat"]),
        "--exit_opportunity_threat_coeff", str(BEST["exit_opportunity_threat_coeff"]),
        "--exit_block_exponent", str(BEST["exit_block_exponent"]),
        "--exit_commit_steps", str(BEST["exit_commit_steps"]),
        "--exit_cost", str(BEST["exit_cost"]),
        "--enforcer_quota_frac", f"{quota:.2f}",
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
            quota = float(parts[0].split("_", 1)[1])
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

        punish = pd.to_numeric(adf.get("punish_issued", pd.Series(dtype=float)), errors="coerce").fillna(0).values
        is_enf = adf.get("is_enforcer", pd.Series(dtype=bool)).astype(bool).values

        enforcer_total = float(punish[is_enf].sum()) if is_enf.any() else 0.0
        all_total = float(punish.sum())
        enforcer_punish_share = enforcer_total / all_total if all_total > 0 else 0.0

        if exit_rate >= 0.90:
            regime = "COLLAPSE"
        elif prev >= 0.90 and exit_rate <= 0.20:
            regime = "CAPTURE"
        elif max_punish >= 0.10:
            regime = "MIXED"
        else:
            regime = "QUIET"

        rows.append(dict(
            enforcer_quota_frac=quota, seed=seed,
            final_fund_prevalence=prev,
            final_exit_rate=exit_rate,
            max_punish=max_punish,
            top5_punishment_share=top_share(punish, 0.05),
            top10_punishment_share=top_share(punish, 0.10),
            enforcer_punish_share=enforcer_punish_share,
            regime_hier=regime,
        ))
    return pd.DataFrame(rows)


def main():
    results_root = Path(__file__).resolve().parent.parent / "results" / "ablation_quota"
    results_root.mkdir(parents=True, exist_ok=True)

    tasks = []
    for quota in QUOTA_VALUES:
        for seed in range(1, N_SEEDS + 1):
            run_dir = results_root / f"quota_{quota:.2f}" / f"seed_{seed:02d}"
            tasks.append((run_dir, seed, quota))

    print(f"running {len(tasks)} simulations (workers={WORKERS})")
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(run_one, rd, s, q) for rd, s, q in tasks]
        for fut in as_completed(futs):
            fut.result()
            done += 1
            if done % 10 == 0 or done == len(tasks):
                print(f"  {done}/{len(tasks)}")

    df = collect_rows(results_root)
    df.to_csv(results_root / "summary.csv", index=False)

    # summary table by quota
    summary_rows = []
    for quota, g in df.groupby("enforcer_quota_frac"):
        summary_rows.append(dict(
            enforcer_quota_frac=quota,
            n_seeds=len(g),
            median_top5_share=g["top5_punishment_share"].median(),
            median_top10_share=g["top10_punishment_share"].median(),
            median_enforcer_share=g["enforcer_punish_share"].median(),
            median_max_punish=g["max_punish"].median(),
            median_fund_prevalence=g["final_fund_prevalence"].median(),
            median_exit_rate=g["final_exit_rate"].median(),
            n_collapse=(g["regime_hier"] == "COLLAPSE").sum(),
            n_capture=(g["regime_hier"] == "CAPTURE").sum(),
            n_mixed=(g["regime_hier"] == "MIXED").sum(),
            n_quiet=(g["regime_hier"] == "QUIET").sum(),
        ))
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(results_root / "summary_by_quota.csv", index=False)
    print(f"\nwrote {results_root / 'summary_by_quota.csv'}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
