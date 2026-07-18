#!/usr/bin/env python3
"""Sweep the pushback blend (elite_pushback_weight) for the v3.2 episode module.

w = 0  pure mass revolt  -> episodes end when grievance crosses the threshold:
       DETERMINISTIC ending => regular durations, high grievance-at-toppling.
w = 1  pure elite coup    -> episodes end via a constant per-step hazard:
       MEMORYLESS ending => irregular durations, grievance often below threshold.

Runs each weight across seeds at a long horizon and reports the episode
statistics that discriminate the two regimes. Real runs only.

usage:
    .venv/bin/python scripts/run_v3_2_weight_sweep.py
"""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "src" / "religion_fundamentalism_abm_v3_2.py"
PY = ROOT / ".venv" / "bin" / "python"
if not PY.exists():
    PY = Path(sys.executable)
OUTROOT = ROOT / "runs" / "v3_2_weight_sweep"   # runs/ is gitignored

WEIGHTS = [0.0, 0.25, 0.5, 0.75, 1.0]
SEEDS = [1, 2, 3, 4, 5]
STEPS = 2000
N = 200
# fixed episode config (the book), same across all weights.
BASE = dict(sigma=0.95, pi_reward=0.50, delta_outside_degrade=0.0, eta_delta_drift=0.12,
            omega_delta=0.06, exit_opportunity_base=0.15)


def runOne(w, seed):
    outdir = OUTROOT / f"w_{w}" / f"seed_{seed}"
    if (outdir / "episode_summary.csv").exists():
        row = pd.read_csv(outdir / "episode_summary.csv").iloc[0].to_dict()
        row.update(weight=w, seed=seed)
        return row
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [str(PY), str(MODEL), "--outdir", str(outdir), "--steps", str(STEPS),
           "--n", str(N), "--graph", "scale_free", "--seed", str(seed),
           "--episode_module", "--elite_pushback_weight", str(w), "--no_movie"]
    for k, v in BASE.items():
        cmd += [f"--{k}", str(v)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    row = pd.read_csv(outdir / "episode_summary.csv").iloc[0].to_dict()
    row.update(weight=w, seed=seed)
    return row


def main():
    jobs = [(w, s) for w in WEIGHTS for s in SEEDS]
    print(f"running {len(jobs)} runs ({len(WEIGHTS)} weights x {len(SEEDS)} seeds) ...", flush=True)
    rows = []
    with ThreadPoolExecutor(max_workers=min(16, len(jobs))) as ex:
        futs = {ex.submit(runOne, w, s): (w, s) for (w, s) in jobs}
        for fut in as_completed(futs):
            rows.append(fut.result())
    df = pd.DataFrame(rows)
    OUTROOT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTROOT / "weight_sweep_seed_results.csv", index=False)

    agg = df.groupby("weight").agg(
        n_episodes=("n_episodes", "mean"),
        mean_duration=("mean_duration", "mean"),
        duration_cv=("duration_cv", "mean"),       # regularity of episode length
        peak_grievance=("mean_peak_grievance", "mean"),  # how "ripe" grievance was at toppling
        gap_cv=("interval_cv", "mean"),            # regularity of the quiet gaps
        distinct_leaders=("distinct_leaders", "mean"),
    ).reset_index()
    agg.to_csv(OUTROOT / "weight_sweep_summary.csv", index=False)

    print("\n=== pushback regime by elite weight (mean over 5 seeds, 2000 steps) ===")
    print("  w=0 mass revolt  ......  w=1 elite coup")
    print(agg.round(3).to_string(index=False))
    print("\ninterpretation:")
    print("  duration_cv rises  and  peak_grievance falls  as w -> 1")
    print("  (mass = regular, grievance-ripe endings; elite = memoryless, premature coups)")
    print(f"\nwrote: {OUTROOT/'weight_sweep_summary.csv'}")


if __name__ == "__main__":
    main()
