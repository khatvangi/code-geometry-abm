#!/usr/bin/env python3
"""v3.3 endogenous exit-capacity experiment driver (reproducible by construction).

This is the committed driver that regenerates the v3.3 endogenous-capacity
results. It exists because the old committed CSVs in
results/v3_3_endogenous_capacity/ are STALE: they predate the econ-decay-sign
fix, the renewal floor, and the LogNormal per-agent heterogeneity now baked into
src/religion_fundamentalism_abm_v3_3.py, and no committed script produced them.

The whole point of this driver is provenance: for EVERY single run it writes a
run_config.json recording every model parameter actually passed on the command
line, the model file's sha256 code fingerprint, and a UTC timestamp. That closes
the under-recording gap that made the old CSVs impossible to reproduce.

Arms (all use exit_capacity_mode=endogenous, n=300, steps=450, scale_free):

  erosion       turnover off, mu=0                          seeds 1-5
  closure       turnover off, crowdout in {5e-4,2e-3,8e-3}  seeds 1-5
  generational  turnover on, born_inside_frac in {0.8,0.0}  seeds 1-5
  live_econ     turnover on, mu in {0.6,0.8} x crowdout in
                {0.002,0.008} x born_inside_frac in {0.8,0.0} seeds 1-10
  panel         turnover on, mu=0.6, seed 1, per-step panel enabled

Usage:
  python scripts/run_v3_3_experiments.py --arm erosion --dry-run
  python scripts/run_v3_3_experiments.py --arm all --workers 40
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from multiprocessing import Pool

# --- locations -------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_FILE = os.path.join(REPO_ROOT, "src", "religion_fundamentalism_abm_v3_3.py")
MODEL_REL = os.path.relpath(MODEL_FILE, REPO_ROOT)

# --- fixed run geometry shared by every arm --------------------------------
# n=300 / steps=450 / scale_free are the settings that reproduce the historic
# erosion row (n_active=178 at cum_exit~0.40 => n=300; ec reported at step 449
# => steps=450). These are model defaults except steps (default 350).
COMMON = {
    "exit_capacity_mode": "endogenous",
    "n": 300,
    "steps": 450,
    "graph": "scale_free",
    # endogenous-capacity kinetics (model defaults, recorded explicitly so the
    # run_config is self-describing and cannot silently drift)
    "ec_tie_decay": 0.01,
    "ec_tie_renewal_base": 0.006,
    "ec_tie_renewal": 0.004,
    "ec_tenure_crowdout": 0.002,
    "ec_econ_recovery_base": 0.004,
    "ec_econ_recovery": 0.002,
    "ec_dependence_rate": 0.01,
    "ec_hetero_sd": 0.25,
    "mu_membership_reward": 0.0,
    # turnover defaults (arms override turnover_mode / born_inside_frac)
    "turnover_mode": "off",
    "born_inside_frac": 0.8,
}

# bare (store_true) flags every run carries. --no_movie: we never render frames.
# --ec_init_random is the model default (True) so it is NOT passed; it is
# recorded in run_config for completeness instead.
COMMON_FLAGS = ["--no_movie"]

CODE_SHA256 = None  # filled at runtime by codeFingerprint()


def codeFingerprint():
    """sha256 of the model source, so a run_config pins the exact code that
    produced it. git-independent on purpose (the .git here is read-only)."""
    global CODE_SHA256
    if CODE_SHA256 is None:
        with open(MODEL_FILE, "rb") as fh:
            CODE_SHA256 = hashlib.sha256(fh.read()).hexdigest()
    return CODE_SHA256


def seedTag(seed):
    return f"seed_{seed:02d}"


def buildSpecs(arm):
    """return the list of run specs for an arm. each spec is a dict with:
      arm     -- arm name
      subdir  -- run directory relative to the arm's output root
      params  -- {flag: value} model parameters actually passed on the CLI
    the COMMON baseline is merged in and then overridden per arm, so params is
    the complete, faithful record of what the model receives.
    """
    specs = []

    def addRun(subdir, overrides, extra_flags=None):
        params = dict(COMMON)
        params.update(overrides)
        specs.append(dict(
            arm=arm,
            subdir=subdir,
            params=params,
            flags=list(COMMON_FLAGS) + list(extra_flags or []),
        ))

    if arm == "erosion":
        # baseline erosion: capacity decays with no turnover, econ channel inert
        for seed in range(1, 6):
            addRun(os.path.join("erosion", seedTag(seed)),
                   {"seed": seed, "turnover_mode": "off",
                    "mu_membership_reward": 0.0})

    elif arm == "closure":
        # crowd-out threshold sweep: does tenure crowd-out drive ties to closure?
        for crowd in (0.0005, 0.002, 0.008):
            for seed in range(1, 6):
                addRun(os.path.join("closure_sweep", f"crowdout_{crowd:g}",
                                    seedTag(seed)),
                       {"seed": seed, "turnover_mode": "off",
                        "ec_tenure_crowdout": crowd})

    elif arm == "generational":
        # cohort turnover: born-inside members enter with zero outside ties
        for born in (0.8, 0.0):
            for seed in range(1, 6):
                addRun(os.path.join("generational", f"born_{born:g}",
                                    seedTag(seed)),
                       {"seed": seed, "turnover_mode": "on",
                        "born_inside_frac": born})

    elif arm == "live_econ":
        # turnover + a LIVE econ channel (mu>0 makes independence decay bite)
        for mu in (0.6, 0.8):
            for crowd in (0.002, 0.008):
                for born in (0.8, 0.0):
                    for seed in range(1, 11):
                        addRun(os.path.join(
                                   "generational_live_econ",
                                   f"mu_{mu:g}", f"crowd_{crowd:g}",
                                   f"born_{born:g}", seedTag(seed)),
                               {"seed": seed, "turnover_mode": "on",
                                "mu_membership_reward": mu,
                                "ec_tenure_crowdout": crowd,
                                "born_inside_frac": born})

    elif arm == "panel":
        # single run with the per-step per-agent panel for the directional
        # (lagged) anti-circularity test; mu=0.6 so the econ channel is live
        addRun(os.path.join("panel", seedTag(1)),
               {"seed": 1, "turnover_mode": "on",
                "mu_membership_reward": 0.6},
               extra_flags=["--panel"])

    else:
        raise ValueError(f"unknown arm: {arm}")

    return specs


def buildCommand(python_exe, run_dir, spec):
    """assemble the exact argv used to launch one model run."""
    cmd = [python_exe, MODEL_FILE, "--outdir", run_dir]
    for flag, value in spec["params"].items():
        cmd.append(f"--{flag}")
        cmd.append(str(value))
    cmd.extend(spec["flags"])
    return cmd


def runConfig(run_dir, spec, cmd):
    """the provenance record written into every run directory. records ALL
    model parameters actually passed, the fixed geometry, the code fingerprint,
    and a UTC timestamp. this is the fix for the historic under-recording."""
    return {
        "arm": spec["arm"],
        "run_dir": os.path.relpath(run_dir, REPO_ROOT),
        "model_file": MODEL_REL,
        "code_sha256": codeFingerprint(),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "n": spec["params"]["n"],
        "steps": spec["params"]["steps"],
        "graph": spec["params"]["graph"],
        "seed": spec["params"]["seed"],
        # ec_init_random is the model default (True) and is not passed on the
        # CLI; recorded here so the config fully describes the init draw.
        "ec_init_random": True,
        "model_params": spec["params"],
        "flags": spec["flags"],
        "cmd": cmd,
    }


def runOne(job):
    """execute a single model run as a subprocess. writes run_config.json BEFORE
    launching (so provenance exists even if the run is killed mid-way) and
    updates it with the outcome afterwards. top-level for multiprocessing.Pool.
    """
    out_root, python_exe, spec = job["out_root"], job["python"], job["spec"]
    run_dir = os.path.join(out_root, spec["subdir"])
    os.makedirs(run_dir, exist_ok=True)

    cmd = buildCommand(python_exe, run_dir, spec)
    cfg = runConfig(run_dir, spec, cmd)
    cfg_path = os.path.join(run_dir, "run_config.json")
    with open(cfg_path, "w") as fh:
        json.dump(cfg, fh, indent=2, sort_keys=True)

    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    cfg["returncode"] = proc.returncode
    cfg["finished_utc"] = datetime.now(timezone.utc).isoformat()
    if proc.returncode != 0:
        cfg["stderr_tail"] = proc.stderr[-2000:]
    with open(cfg_path, "w") as fh:
        json.dump(cfg, fh, indent=2, sort_keys=True)

    return {
        "arm": spec["arm"],
        "subdir": spec["subdir"],
        "run_dir": os.path.relpath(run_dir, REPO_ROOT),
        "returncode": proc.returncode,
    }


def writeManifest(out_root, arm, specs, results=None):
    """top-level MANIFEST for the arm: every run directory and its full config."""
    entries = []
    for spec in specs:
        run_dir = os.path.join(out_root, spec["subdir"])
        cmd = buildCommand(sys.executable, run_dir, spec)
        entry = {
            "subdir": spec["subdir"],
            "run_dir": os.path.relpath(run_dir, REPO_ROOT),
            "config": runConfig(run_dir, spec, cmd),
        }
        entries.append(entry)
    manifest = {
        "arm": arm,
        "out_root": os.path.relpath(out_root, REPO_ROOT),
        "model_file": MODEL_REL,
        "code_sha256": codeFingerprint(),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "n_runs": len(specs),
        "runs": entries,
    }
    if results is not None:
        manifest["results"] = results
    path = os.path.join(out_root, f"MANIFEST_{arm}.json")
    os.makedirs(out_root, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
    return path


def runArm(arm, out_root, workers, python_exe, dry_run):
    specs = buildSpecs(arm)
    print(f"\n=== arm '{arm}': {len(specs)} run(s) -> {out_root} ===")

    if dry_run:
        for spec in specs:
            run_dir = os.path.join(out_root, spec["subdir"])
            cmd = buildCommand(python_exe, run_dir, spec)
            print("  " + " ".join(cmd))
        print(f"[dry-run] {len(specs)} planned command(s) for arm '{arm}'; "
              "nothing executed, no configs written.")
        return specs, None

    jobs = [dict(out_root=out_root, python=python_exe, spec=s) for s in specs]
    if workers > 1 and len(jobs) > 1:
        with Pool(processes=min(workers, len(jobs))) as pool:
            results = pool.map(runOne, jobs)
    else:
        results = [runOne(j) for j in jobs]

    manifest_path = writeManifest(out_root, arm, specs, results)
    n_ok = sum(1 for r in results if r["returncode"] == 0)
    print(f"[done] arm '{arm}': {n_ok}/{len(results)} runs succeeded; "
          f"manifest -> {os.path.relpath(manifest_path, REPO_ROOT)}")
    return specs, results


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", required=True,
                    choices=["erosion", "closure", "generational",
                             "live_econ", "panel", "all"])
    ap.add_argument("--out", default="results/v3_3_endogenous_capacity_v2",
                    help="output root (default results/v3_3_endogenous_capacity_v2)")
    ap.add_argument("--workers", type=int, default=1,
                    help="parallel worker processes")
    ap.add_argument("--python", default=sys.executable,
                    help="python interpreter used to launch the model")
    ap.add_argument("--dry-run", action="store_true",
                    help="print planned commands and exit without running")
    args = ap.parse_args()

    out_root = args.out if os.path.isabs(args.out) else os.path.join(REPO_ROOT, args.out)

    arms = ["erosion", "closure", "generational", "live_econ", "panel"] \
        if args.arm == "all" else [args.arm]

    print(f"model file : {MODEL_REL}")
    print(f"code sha256: {codeFingerprint()}")
    print(f"out root   : {os.path.relpath(out_root, REPO_ROOT)}")
    print(f"workers    : {args.workers}")

    total = 0
    for arm in arms:
        specs, _ = runArm(arm, out_root, args.workers, args.python, args.dry_run)
        total += len(specs)
    print(f"\ntotal planned runs across selected arm(s): {total}")


if __name__ == "__main__":
    main()
