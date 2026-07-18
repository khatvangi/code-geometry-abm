#!/usr/bin/env python3
"""Foolproof validation for the v3.x consolidated + episodic models.

Three checks, each fails loudly (non-zero exit) so a broken invariant cannot pass
silently -- the discipline the earlier misclassifications lacked:

  A  regime_classifier self-check (incl. the acquiescence-aware capture path).
  B  v3.2 with the episode module OFF is byte-identical to v3.1 (the additive
     guarantee: episodic dynamics never perturb the base model).
  C  v3.2 with the episode module ON exhibits genuine recurrence (>=2 episodes)
     and no stuck-on episode (no single episode spanning the whole horizon).

usage:
    .venv/bin/python scripts/validate_v3.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PY = ROOT / ".venv" / "bin" / "python"
if not PY.exists():
    PY = Path(sys.executable)
V31 = ROOT / "src" / "religion_fundamentalism_abm_v3_1.py"
V32 = ROOT / "src" / "religion_fundamentalism_abm_v3_2.py"
CLS = ROOT / "src" / "regime_classifier.py"
TMP = ROOT / ".validate_v3_tmp"

# a sealed, legible, rewarded config -> deterministic CAPTURE for the identity check.
SEALED = ["--sigma", "0.95", "--pi_reward", "0.50", "--delta_outside_degrade", "0.25",
          "--eta_delta_drift", "0.12", "--omega_delta", "0.06", "--exit_opportunity_base", "0.15"]


def run(model, outdir, extra):
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [str(PY), str(model), "--outdir", str(outdir), "--n", "150", "--graph",
           "scale_free", "--seed", "1", "--no_movie"] + extra
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def main():
    if TMP.exists():
        shutil.rmtree(TMP)
    fails = []

    # A: classifier self-check
    r = subprocess.run([str(PY), str(CLS)], capture_output=True, text=True)
    if r.returncode != 0 or "OK" not in r.stdout:
        fails.append(f"A: regime_classifier self-check failed: {r.stdout}{r.stderr}")
    else:
        print("A  regime_classifier self-check: PASS")

    # B: v3.2 module OFF == v3.1 (byte-identical run_summary)
    run(V31, TMP / "v31", ["--steps", "150"] + SEALED)
    run(V32, TMP / "v32_off", ["--steps", "150"] + SEALED)  # episode_module defaults off
    a = (TMP / "v31" / "run_summary.csv").read_text()
    b = (TMP / "v32_off" / "run_summary.csv").read_text()
    if a != b:
        fails.append("B: v3.2 module-OFF run_summary differs from v3.1 (not additive)")
    else:
        print("B  v3.2 module OFF == v3.1 (byte-identical): PASS")

    # C: v3.2 module ON -> genuine recurrence, no stuck episode
    steps = 1200
    run(V32, TMP / "v32_on", ["--steps", str(steps), "--episode_module"] + SEALED)
    ep = pd.read_csv(TMP / "v32_on" / "episode_summary.csv").iloc[0]
    mx = pd.read_csv(TMP / "v32_on" / "metrics.csv")
    # longest contiguous active run:
    act = mx["episode_active"].tolist()
    longest = cur = 0
    for v in act:
        cur = cur + 1 if v else 0
        longest = max(longest, cur)
    if ep["n_episodes"] < 2:
        fails.append(f"C: expected >=2 episodes, got {int(ep['n_episodes'])}")
    elif longest >= 0.9 * steps:
        fails.append(f"C: stuck-on episode ({longest}/{steps} steps active)")
    else:
        print(f"C  v3.2 recurrence: PASS ({int(ep['n_episodes'])} episodes, "
              f"longest={longest}/{steps} steps)")

    shutil.rmtree(TMP, ignore_errors=True)
    print()
    if fails:
        for f in fails:
            print(f"FAIL: {f}")
        sys.exit(1)
    print("all v3.x validation checks PASS")


if __name__ == "__main__":
    main()
