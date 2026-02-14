#!/usr/bin/env python3
import argparse
import json
import random
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=60)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--steps", type=int, default=450)
    ap.add_argument("--n", type=int, default=350)
    ap.add_argument("--graph", type=str, default="scale_free")
    ap.add_argument("--root", type=str, default="")
    ap.add_argument("--rng_seed", type=int, default=42)
    return ap.parse_args()


def sample_params(rng: random.Random):
    return {
        "membership_benefit": rng.uniform(0.00, 0.08),
        "membership_benefit_threat": rng.uniform(0.00, 0.25),
        "exit_opportunity_base": rng.uniform(0.20, 0.80),
        "exit_opportunity_threat_coeff": rng.uniform(1.0, 6.0),
        "exit_block_exponent": rng.uniform(1.0, 6.0),
        "exit_commit_steps": rng.choice([4, 8, 12, 16]),
        "exit_cost": rng.choice([1.0, 2.0, 4.0, 8.0]),
        "shock_strength": rng.choice([0.10, 0.20, 0.30, 0.40]),
    }


def run_one(abm: str, outdir: Path, seed: int, steps: int, n: int, graph: str, params: dict):
    cmd = [
        "python", abm,
        "--outdir", str(outdir),
        "--steps", str(steps),
        "--n", str(n),
        "--graph", graph,
        "--seed", str(seed),
        "--sigma", "0.80",
        "--v_obs", "0.95",
        "--a_obs", "0.03",
        "--h_obs", "0.15",
        "--w_heresy", "0.60",
        "--d0", "0.18",
        "--pi_reward", "0.24",
        "--kappa_cost", "0.08",
        "--lam_punish", "0.28",
        "--backlash_base", "0.25",
        "--backlash_cost", "0.30",
        "--backlash_sensitivity", "1.0",
        "--exit_cost", f"{params['exit_cost']}",
        "--exit_threshold", "-1.0",
        "--exit_prob_slope", "3.0",
        "--exit_rewire_fraction", "0.90",
        "--exit_degree_coeff", "0.03",
        "--exit_epc_lockin_coeff", "0.25",
        "--exit_min_cost", "0.0",
        "--exit_opportunity_base", f"{params['exit_opportunity_base']}",
        "--exit_opportunity_deg_coeff", "0.03",
        "--exit_opportunity_threat_coeff", f"{params['exit_opportunity_threat_coeff']}",
        "--exit_block_exponent", f"{params['exit_block_exponent']}",
        "--exit_block_floor", "0.02",
        "--exit_commit_steps", str(params["exit_commit_steps"]),
        "--exit_cooldown", "0",
        "--membership_benefit", f"{params['membership_benefit']}",
        "--membership_benefit_sigma", "0.08",
        "--membership_benefit_threat", f"{params['membership_benefit_threat']}",
        "--shock_schedule", "100,220,320",
        "--shock_strength", f"{params['shock_strength']}",
        "--tighten_gain_pi", "0.20",
        "--tighten_gain_lam", "0.20",
        "--tighten_gain_d0", "0.08",
        "--relax_rate", "0.03",
        "--baseline_pi", "0.24",
        "--baseline_lam", "0.28",
        "--baseline_d0", "0.18",
        "--no_movie",
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    args = parse_args()
    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    run_root = Path(args.root) if args.root else Path(f"runs/batch_v2_3_search_{ts}")
    summary_dir = run_root / "summary"
    trials_dir = run_root / "trials"
    summary_dir.mkdir(parents=True, exist_ok=True)
    trials_dir.mkdir(parents=True, exist_ok=True)

    abm = "src/religion_fundamentalism_abm_v2_3.py"
    rng = random.Random(args.rng_seed)
    trial_rows = []

    for trial in range(1, args.trials + 1):
        params = sample_params(rng)
        run_rows = []
        trial_dir = trials_dir / f"trial_{trial:03d}"
        trial_dir.mkdir(parents=True, exist_ok=True)

        for seed in range(1, args.seeds + 1):
            outdir = trial_dir / f"seed_{seed:02d}"
            outdir.mkdir(parents=True, exist_ok=True)
            run_one(abm, outdir, seed, args.steps, args.n, args.graph, params)

            m = pd.read_csv(outdir / "metrics.csv")
            final = m.iloc[-1]
            run_rows.append(
                {
                    "seed": seed,
                    "final_exit_rate": float(final.get("exit_rate", np.nan)),
                    "final_prevalence": float(final.get("fund_prevalence", np.nan)),
                    "max_punish_rate": float(m["punish_rate"].max()) if "punish_rate" in m.columns else np.nan,
                }
            )

        df = pd.DataFrame(run_rows)
        med_exit = float(df["final_exit_rate"].median())
        med_prev = float(df["final_prevalence"].median())
        med_pun = float(df["max_punish_rate"].median())
        hit = (0.20 <= med_exit <= 0.80) and (0.20 <= med_prev <= 0.90) and (med_pun >= 0.10)

        row = {
            "trial": trial,
            **params,
            "median_final_exit_rate": med_exit,
            "median_final_prevalence": med_prev,
            "median_max_punish_rate": med_pun,
            "hit": bool(hit),
        }
        trial_rows.append(row)
        print(
            f"[trial {trial:03d}/{args.trials}] "
            f"exit={med_exit:.3f} prev={med_prev:.3f} max_pun={med_pun:.3f} hit={hit}",
            flush=True,
        )

    trials_df = pd.DataFrame(trial_rows)
    trials_df.to_csv(summary_dir / "trials.csv", index=False)

    hits = trials_df[trials_df["hit"]].copy().sort_values("median_max_punish_rate", ascending=False)
    hits.to_csv(summary_dir / "hits.csv", index=False)

    best_path = summary_dir / "BEST_PARAMS.json"
    if hits.empty:
        best = {
            "found_hit": False,
            "message": "No mixed-regime hit found in sampled trials.",
        }
    else:
        b = hits.iloc[0].to_dict()
        best = {
            "found_hit": True,
            "trial": int(b["trial"]),
            "params": {
                "membership_benefit": float(b["membership_benefit"]),
                "membership_benefit_threat": float(b["membership_benefit_threat"]),
                "exit_opportunity_base": float(b["exit_opportunity_base"]),
                "exit_opportunity_threat_coeff": float(b["exit_opportunity_threat_coeff"]),
                "exit_block_exponent": float(b["exit_block_exponent"]),
                "exit_commit_steps": int(b["exit_commit_steps"]),
                "exit_cost": float(b["exit_cost"]),
                "shock_strength": float(b["shock_strength"]),
            },
            "metrics": {
                "median_final_exit_rate": float(b["median_final_exit_rate"]),
                "median_final_prevalence": float(b["median_final_prevalence"]),
                "median_max_punish_rate": float(b["median_max_punish_rate"]),
            },
        }

    best_path.write_text(json.dumps(best, indent=2), encoding="utf-8")
    print(run_root)
    print(summary_dir / "trials.csv")
    print(summary_dir / "hits.csv")
    print(best_path)


if __name__ == "__main__":
    main()
