#!/usr/bin/env python3
"""Full factorial-ablation confirmatory sweep for the consolidated v3.1 model.

Crosses the three mechanism legs (2^3 = 8 configs) with the legibility x reward x
exit core grid, at manuscript scale (n=350, steps=450), 5 seeds per cell.

  leg P (patronage):    selective enforcement benefit on (cap_gain_per_punish>0)
                        vs off (flat membership perk mu instead) -- tests whether
                        conditional reward is what concentrates, not flat benefit.
  leg S (exit sealing): endogenous outside-option degradation on vs off.
  leg A (acquiescence): self-policing channel on vs off.

Regime labels are read from each run's self-emitted run_summary.csv (produced by
regime_classifier via the v3.1 model) -- there is NO inline classifier here, by
design. Aggregation records BOTH the overt and acquiescence-aware regime and the
cross-seed invariance of enforcement concentration.

The sweep is idempotent/resumable: a cell with an existing run_summary.csv is
skipped, so it can be re-launched to finish a partial run.

usage:
    .venv/bin/python scripts/run_v3_1_factorial_sweep.py            # full sweep
    .venv/bin/python scripts/run_v3_1_factorial_sweep.py --aggregate-only
"""
import argparse
import itertools
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MODEL = ROOT / "src" / "religion_fundamentalism_abm_v3_1.py"
PY = ROOT / ".venv" / "bin" / "python"
if not PY.exists():
    PY = Path(sys.executable)
OUTROOT = ROOT / "results" / "v3_1_factorial_sweep"

STEPS = 450
N = 350

# core grid: the three axes that define the enforcement boundary.
SIGMAS = [0.25, 0.55, 0.75, 0.95]          # code legibility
PI_REWARDS = [0.05, 0.25, 0.50]            # selective reward magnitude
BASE_OPPS = [0.15, 0.35, 0.60]             # outside-option ease (inverse exit cost)
SEEDS = [1, 2, 3, 4, 5]


def legParams(patronage: bool, seal: bool, acq: bool) -> dict:
    """map the three on/off legs to explicit CLI overrides."""
    p = {}
    if patronage:                          # selective, enforcement-conditional benefit
        p["cap_gain_per_punish"] = 0.15
        p["mu_membership_reward"] = 0.0
    else:                                  # flat membership perk instead (the control)
        p["cap_gain_per_punish"] = 0.0
        p["mu_membership_reward"] = 0.10
    if seal:                               # endogenous exit sealing
        p["delta_outside_degrade"] = 0.25
        p["eta_delta_drift"] = 0.12
    else:
        p["delta_outside_degrade"] = 0.0
        p["eta_delta_drift"] = 0.0
    if acq:                                # self-policing channel
        p["omega_x"], p["omega_delta"], p["omega_e"], p["omega_t"] = 0.02, 0.06, 0.04, 0.02
    else:
        p["omega_x"], p["omega_delta"], p["omega_e"], p["omega_t"] = 0.0, 0.0, 0.0, 0.0
    return p


def configName(patronage: bool, seal: bool, acq: bool) -> str:
    return f"P{int(patronage)}S{int(seal)}A{int(acq)}"


def buildJobs():
    jobs = []
    for patronage, seal, acq in itertools.product([True, False], repeat=3):
        cfg = configName(patronage, seal, acq)
        legs = legParams(patronage, seal, acq)
        for sigma, pi, opp, seed in itertools.product(SIGMAS, PI_REWARDS, BASE_OPPS, SEEDS):
            run_dir = OUTROOT / cfg / f"sig_{sigma}" / f"pi_{pi}" / f"opp_{opp}" / f"seed_{seed}"
            jobs.append(dict(cfg=cfg, legs=legs, sigma=sigma, pi=pi, opp=opp,
                             seed=seed, run_dir=run_dir))
    return jobs


def runOne(job) -> str:
    run_dir = job["run_dir"]
    if (run_dir / "run_summary.csv").exists():
        return "skip"
    run_dir.mkdir(parents=True, exist_ok=True)
    cmd = [str(PY), str(MODEL), "--outdir", str(run_dir),
           "--steps", str(STEPS), "--n", str(N), "--graph", "scale_free",
           "--seed", str(job["seed"]), "--sigma", str(job["sigma"]),
           "--pi_reward", str(job["pi"]), "--exit_opportunity_base", str(job["opp"]),
           "--no_movie"]
    for k, v in job["legs"].items():
        cmd += [f"--{k}", str(v)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return "done"


def writeReport(jobs, workers):
    """record every sweep-time parameter at launch (project discipline)."""
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                capture_output=True, text=True).stdout.strip()
    except Exception:
        commit = "unknown"
    OUTROOT.mkdir(parents=True, exist_ok=True)
    lines = [
        "v3.1 factorial-ablation confirmatory sweep",
        f"git_commit: {commit}",
        f"model: {MODEL.relative_to(ROOT)}",
        f"steps: {STEPS}  n: {N}  graph: scale_free  workers: {workers}",
        f"total_jobs: {len(jobs)}  (8 ablation configs x 36 cells x {len(SEEDS)} seeds)",
        f"sigmas: {SIGMAS}",
        f"pi_rewards: {PI_REWARDS}",
        f"base_opps: {BASE_OPPS}",
        f"seeds: {SEEDS}",
        "",
        "ablation legs (config name P{patronage}S{seal}A{acq}):",
        "  P1: cap_gain_per_punish=0.15, mu=0.0   | P0: cap_gain_per_punish=0.0, mu=0.10",
        "  S1: delta_outside_degrade=0.25, eta_delta_drift=0.12 | S0: both 0.0",
        "  A1: omega_x/delta/e/t=0.02/0.06/0.04/0.02 | A0: all omega=0",
        "",
        "classification: read from each run's self-emitted run_summary.csv",
        "  (regime_classifier hierarchical schema; overt AND acquiescence-aware).",
    ]
    (OUTROOT / "sweep_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def aggregate():
    rows = []
    for summ in OUTROOT.rglob("run_summary.csv"):
        try:
            r = pd.read_csv(summ).iloc[0].to_dict()
        except Exception:
            continue
        # config is the top-level dir under OUTROOT.
        r["config"] = summ.relative_to(OUTROOT).parts[0]
        rows.append(r)
    if not rows:
        print("no run_summary.csv found yet.")
        return
    df = pd.DataFrame(rows)
    df.to_csv(OUTROOT / "sweep_seed_results.csv", index=False)

    # cell = (config, sigma, pi_reward, exit_opportunity_base); aggregate across seeds.
    keys = ["config", "sigma", "pi_reward", "exit_opportunity_base"]
    def modeRegime(s):
        m = s.mode()
        return m.iloc[0] if len(m) else "NA"
    cell = df.groupby(keys).agg(
        n_seeds=("seed", "count"),
        regime_overt_majority=("regime_overt", modeRegime),
        regime_aware_majority=("regime_acquiescence_aware", modeRegime),
        enforcer_share_mean=("final_enforcer_share", "mean"),
        enforcer_share_std=("final_enforcer_share", "std"),   # cross-seed invariance
        self_policing_mean=("final_q_above_threshold", "mean"),
        belief_mean=("final_fund_prevalence", "mean"),
        exit_mean=("final_exit_rate", "mean"),
        n_mislabeled=("mislabeled_fear_capture", "sum"),
    ).reset_index()
    cell.to_csv(OUTROOT / "sweep_summary.csv", index=False)

    print(f"\naggregated {len(df)} runs into {len(cell)} cells.")
    print("\n=== regime counts by config (acquiescence-aware, cell-majority) ===")
    print(pd.crosstab(cell["config"], cell["regime_aware_majority"]).to_string())
    print("\n=== overt vs acquiescence-aware disagreement (runs mislabeled QUIET by overt view) ===")
    print(f"  total runs flagged mislabeled_fear_capture: {int(df['mislabeled_fear_capture'].sum())}")
    inv = cell[cell["regime_aware_majority"] == "CAPTURE"]["enforcer_share_std"].median()
    print(f"\n=== structural invariance in CAPTURE cells ===")
    print(f"  median cross-seed enforcer-share std: {inv:.3f}  (small => actor-independent)")
    print(f"\nwrote: {OUTROOT/'sweep_seed_results.csv'}\n       {OUTROOT/'sweep_summary.csv'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=48)
    ap.add_argument("--aggregate-only", action="store_true")
    args = ap.parse_args()

    if args.aggregate_only:
        aggregate()
        return

    jobs = buildJobs()
    writeReport(jobs, args.workers)
    print(f"launching {len(jobs)} jobs on {args.workers} workers ...", flush=True)
    done = skipped = failed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(runOne, j): j for j in jobs}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                res = fut.result()
                if res == "skip":
                    skipped += 1
                else:
                    done += 1
            except Exception as e:
                failed += 1
                j = futs[fut]
                print(f"FAIL {j['cfg']} sig{j['sigma']} pi{j['pi']} opp{j['opp']} s{j['seed']}: {e}",
                      flush=True)
            if i % 100 == 0:
                print(f"  progress {i}/{len(jobs)} (done={done} skip={skipped} fail={failed})",
                      flush=True)
    print(f"sweep finished: done={done} skipped={skipped} failed={failed}", flush=True)
    aggregate()


if __name__ == "__main__":
    main()
