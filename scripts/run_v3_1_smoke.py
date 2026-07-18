#!/usr/bin/env python3
"""Foolproof smoke sweep for the consolidated v3.1 model.

Runs two contrasting conditions across seeds and checks the consolidated thesis
on real runs (no synthetic data):

  PRESENT  legible code + selective reward + sealed exit + acquiescence on
           -> enforcement concentrates in a cadre and the pattern RECURS across
              seeds (different actors, same structure); functional capture forms.
  ABSENT   illegible code + weak reward + cheap exit
           -> no cadre, no capture (QUIET or COLLAPSE).

This is a *prototype* (small n, short horizon, 3 seeds) meant to validate the
mechanism and the guardrails quickly, not to produce publishable numbers. It
FAILS LOUDLY (non-zero exit) if the qualitative expectations do not hold -- that
loud failure is the point: a silent "looks fine" is how the project's earlier
misclassifications slipped through.

usage:
    .venv/bin/python scripts/run_v3_1_smoke.py
"""
import os
import sys
import subprocess
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODEL = os.path.join(ROOT, "src", "religion_fundamentalism_abm_v3_1.py")
PY = os.path.join(ROOT, ".venv", "bin", "python")
if not os.path.exists(PY):
    PY = sys.executable
OUTROOT = os.path.join(ROOT, "runs", "v3_1_smoke")  # runs/ is gitignored

SEEDS = [1, 2, 3]
STEPS = 200
N = 150

# each condition is a dict of CLI overrides; everything else uses model defaults.
CONDITIONS = {
    "PRESENT": dict(
        sigma=0.95,               # legible code
        pi_reward=0.50,           # selective reward for enforcing
        delta_outside_degrade=0.25,  # exit sealing
        eta_delta_drift=0.12,
        omega_delta=0.06,         # entrapment -> acquiescence
        exit_opportunity_base=0.15,  # costly exit
    ),
    "ABSENT": dict(
        sigma=0.25,               # illegible code
        pi_reward=0.05,           # negligible reward
        delta_outside_degrade=0.0,   # exit stays open
        exit_opportunity_base=0.60,  # cheap exit
    ),
}


def runOne(cond_name, overrides, seed):
    """run a single v3.1 simulation and return its parsed run_summary row."""
    outdir = os.path.join(OUTROOT, cond_name.lower(), f"seed_{seed}")
    os.makedirs(outdir, exist_ok=True)
    cmd = [PY, MODEL, "--outdir", outdir, "--steps", str(STEPS), "--n", str(N),
           "--graph", "scale_free", "--seed", str(seed), "--no_movie"]
    for k, v in overrides.items():
        cmd += [f"--{k}", str(v)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    row = pd.read_csv(os.path.join(outdir, "run_summary.csv")).iloc[0].to_dict()
    row["condition"] = cond_name
    return row


def main():
    rows = []
    for cond_name, overrides in CONDITIONS.items():
        for seed in SEEDS:
            print(f"running {cond_name} seed={seed} ...", flush=True)
            rows.append(runOne(cond_name, overrides, seed))
    df = pd.DataFrame(rows)

    cols = ["condition", "seed", "regime_overt", "regime_acquiescence_aware",
            "final_enforcer_share", "final_q_above_threshold",
            "final_fund_prevalence", "final_exit_rate", "mislabeled_fear_capture"]
    print("\n=== per-run summary ===")
    print(df[cols].to_string(index=False))

    present = df[df.condition == "PRESENT"]
    absent = df[df.condition == "ABSENT"]

    # invariance: across seeds (= different actors), does concentration recur?
    inv_std = float(present["final_enforcer_share"].std())
    print("\n=== structural invariance (PRESENT, across seeds) ===")
    print(f"  enforcer-share mean={present['final_enforcer_share'].mean():.3f} "
          f"std={inv_std:.3f}  (small std => same structure, different actors)")
    print(f"  belief prevalence mean={present['final_fund_prevalence'].mean():.3f} "
          f"(thin belief under concentrated enforcement)")

    # foolproof assertions -- fail loudly if the mechanism does not behave.
    problems = []
    if (present["regime_overt"] == "QUIET").any():
        problems.append("PRESENT produced a QUIET run (mechanism failed to ignite)")
    if present["final_enforcer_share"].mean() < 0.70:
        problems.append("PRESENT enforcement not concentrated (share < 0.70)")
    if inv_std > 0.20:
        problems.append(f"PRESENT concentration not invariant across seeds (std={inv_std:.2f})")
    if (absent["regime_acquiescence_aware"] == "CAPTURE").any():
        problems.append("ABSENT produced CAPTURE (mechanism appeared without its conditions)")

    print("\n=== verdict ===")
    if problems:
        for p in problems:
            print(f"  FAIL: {p}")
        sys.exit(1)
    print("  PASS: mechanism present -> concentrated + invariant; absent -> no capture.")


if __name__ == "__main__":
    main()
