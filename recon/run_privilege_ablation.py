#!/usr/bin/env python3
"""H2 privilege-ablation: is punishment concentration EMERGENT or ASSUMED?

Staged decomposition of the enforcer-privilege bundle to find WHICH institutional
feature generates punishment concentration (the ceiling shows top-5% ~0.8; is that
manufactured by privilege, and by which privilege?).

Arms: floor (all privileges off), ceiling (all on), one add-back arm per privilege
(floor + that privilege restored), plus an equalization sweep of the floor.

THREE GUARDRAILS (all folded in here so the residual claim is supportable):
  1. ACTIVE-ONLY metrics. Concentration is computed over non-exited agents only.
     Otherwise exited agents (60% of the floor population) sit at zero punishment
     and mechanically inflate inequality; two arms with different exit rates are
     then not comparable. (Same active-agent contamination fixed once in v3.2.)
  2. STOCHASTIC NULL. Report observed Gini against a same-volume random-allocation
     null per arm, so "residual inequality" means "above what random counting noise
     of the same punishment volume would produce."
  3. EQUALIZATION SWEEP. Run the floor at several non_enforcer_punish_eps levels to
     confirm the concentration collapse is not an artifact of setting eps=1.0.

Concentration is measured ROLE-INDEPENDENTLY (top-5% punishment share + Gini over
per-agent punishment counts), never enforcer_punish_share, which is vacuous once
the quota/cadre is removed.

Exit is recorded per arm alongside concentration: if a privilege turns out weak
for concentration but strong for retention, that is a distinct, useful result
about why these institutional features travel together.

usage: .venv/bin/python recon/run_privilege_ablation.py [--workers N]
"""
import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "src" / "religion_fundamentalism_abm_v2_7.py"
PY = ROOT / ".venv" / "bin" / "python"
if not PY.exists():
    PY = Path(sys.executable)
OUTROOT = ROOT / "recon" / "privilege_ablation"

BASE = dict(n=350, steps=450, exit_opportunity_base=0.3, shock_schedule="",
            delta_mode="exogenous", delta_outside_degrade=0.95, eta_delta_drift=0.0,
            punish_floor=0.08, exit_threshold=-1.0)
CELLS = [(0.75, 0.25), (0.75, 0.50), (0.95, 0.25), (0.95, 0.50)]
SEEDS = list(range(1, 31))
NULL_REPS = 100

# each privilege -> the CLI overrides that DISABLE it. floor applies all of them.
PRIVILEGE_OFF = {
    "monopoly":         {"A_enforcer_monopoly": 2.0},
    "quota":            {"enforcer_quota_frac": 0.0},
    "punish_mult":      {"non_enforcer_punish_eps": 1.0, "enforcer_punish_mult": 1.0},
    "cap_gain":         {"cap_gain_per_punish": 0.0},
    "cost_discount":    {"kappa_cap_discount": 0.0, "enforcer_kappa_mult": 1.0},
    "backlash_protect": {"enforcer_backlash_mult": 1.0},
    "budget_patronage": {"budget_base": 0.0, "budget_threat_gain": 0.0},
}


def floorOverrides():
    o = {}
    for d in PRIVILEGE_OFF.values():
        o.update(d)
    return o


def buildArms():
    arms = {"floor": floorOverrides(), "ceiling": {}}
    for name, off in PRIVILEGE_OFF.items():
        o = floorOverrides()
        for k in off:
            o.pop(k, None)                 # restore this one privilege to its default
        arms[f"add_{name}"] = o
    # equalization sweep: floor with the neutral punish rate lowered (guardrail 3)
    arms["floor_eps0.50"] = {**floorOverrides(), "non_enforcer_punish_eps": 0.50}
    arms["floor_eps0.25"] = {**floorOverrides(), "non_enforcer_punish_eps": 0.25}
    return arms


ARMS = buildArms()

# historically-motivated NESTED path (papal-inquisition sequence): a specialized
# body is designated first, then accumulates powers in a consistent order —
# designation (quota), coercive power (multiplier), exclusivity (monopoly),
# immunity (backlash protection), material self-funding (cap-gain per punishment),
# standing budget, cost discount. monopoly follows the multiplier because
# exclusivity is meaningless until there is a differential worth being exclusive
# about. each arm turns ON one more privilege, cumulatively.
NESTED_ORDER = ["quota", "punish_mult", "monopoly", "backlash_protect",
                "cap_gain", "budget_patronage", "cost_discount"]
NESTED_LABEL = {1: "n1_quota", 2: "n2_multiplier", 3: "n3_monopoly",
                4: "n4_immunity", 5: "n5_capgain", 6: "n6_budget"}
# n0 = floor (nothing on), n7 = ceiling (all on); reuse those rather than re-run.


def buildNested():
    arms = {}
    for k in range(1, len(NESTED_ORDER)):        # k=1..6 -> n1..n6 (n0=floor, n7=ceiling)
        o = floorOverrides()
        for name in NESTED_ORDER[:k]:            # re-enable the first k privileges
            for key in PRIVILEGE_OFF[name]:
                o.pop(key, None)
        arms[NESTED_LABEL[k]] = o
    return arms


ARMS.update(buildNested())


def gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return 0.0
    c = np.cumsum(x)
    return float((n + 1 - 2 * np.sum(c) / c[-1]) / n)


def topShare(x, frac=0.05):
    x = np.sort(np.asarray(x, dtype=float))[::-1]
    tot = x.sum()
    if tot <= 0:
        return 0.0
    k = max(1, int(np.ceil(frac * len(x))))
    return float(x[:k].sum() / tot)


def nullGini(total, n, seed, reps=NULL_REPS):
    """median Gini of `total` punishment acts allocated uniformly at random over n
    active agents — the concentration expected from counting noise alone."""
    total = int(round(total))
    if total <= 0 or n <= 0:
        return 0.0
    rng = np.random.default_rng(seed)
    return float(np.median([gini(rng.multinomial(total, np.ones(n) / n)) for _ in range(reps)]))


def runOne(arm, sigma, pi, seed):
    outdir = OUTROOT / arm / f"sig_{sigma}" / f"pi_{pi}" / f"seed_{seed}"
    if not (outdir / "agent_summary.csv").exists():
        outdir.mkdir(parents=True, exist_ok=True)
        cfg = dict(BASE)
        cfg.update(sigma=sigma, pi_reward=pi, seed=seed)
        cfg.update(ARMS[arm])
        cmd = [str(PY), str(MODEL), "--outdir", str(outdir), "--graph", "scale_free", "--no_movie"]
        for k, v in cfg.items():
            cmd += [f"--{k}", str(v)]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    a = pd.read_csv(outdir / "agent_summary.csv")
    m = pd.read_csv(outdir / "metrics.csv")
    active = a[~a["exited"].astype(bool)]                       # guardrail 1: active only
    p_act = active["punish_issued"].to_numpy(dtype=float)
    p_all = a["punish_issued"].to_numpy(dtype=float)
    return dict(
        arm=arm, sigma=sigma, pi=pi, seed=seed,
        top5_active=topShare(p_act), gini_active=gini(p_act),
        gini_null=nullGini(p_act.sum(), len(p_act), seed),       # guardrail 2
        top5_all=topShare(p_all), gini_all=gini(p_all),
        total_punish=float(p_act.sum()), n_active=int(len(p_act)),
        exit_rate=float(m["exit_rate"].iloc[-1]),
    )


def aggregate(rows):
    df = pd.DataFrame(rows)
    OUTROOT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTROOT / "ablation_seed_results.csv", index=False)
    agg = df.groupby("arm").agg(
        top5_active=("top5_active", "median"),
        gini_active=("gini_active", "median"),
        gini_null=("gini_null", "median"),
        exit_rate=("exit_rate", "median"),
        total_punish=("total_punish", "median"),
    )
    order = (["floor", "floor_eps0.25", "floor_eps0.50"]
             + [f"add_{k}" for k in PRIVILEGE_OFF]
             + [NESTED_LABEL[k] for k in range(1, len(NESTED_ORDER))]
             + ["ceiling"])
    agg = agg.reindex([a for a in order if a in agg.index])
    agg["gini_above_null"] = (agg["gini_active"] - agg["gini_null"]).round(3)
    agg.to_csv(OUTROOT / "ablation_summary.csv")
    print("\n=== privilege-ablation (active-only metrics; ranked) ===")
    print(agg.round(3).to_string())

    if "floor" in agg.index and "ceiling" in agg.index:
        fl, ce = agg.loc["floor", "top5_active"], agg.loc["ceiling", "top5_active"]
        span = ce - fl
        print(f"\nheadline: top-5% (active) floor {fl:.3f} -> ceiling {ce:.3f}  "
              f"({100*(ce-fl)/ce:.0f}% of ceiling concentration is privilege-manufactured)")
        # rank each privilege's marginal contribution (add-back minus floor), share of span
        print("\nprivilege contribution to concentration (add_X top5_active - floor), ranked:")
        contrib = {k: agg.loc[f"add_{k}", "top5_active"] - fl
                   for k in PRIVILEGE_OFF if f"add_{k}" in agg.index}
        for k, v in sorted(contrib.items(), key=lambda kv: -kv[1]):
            pct = 100 * v / span if span > 0 else 0.0
            print(f"  {k:18s} +{v:.3f}  ({pct:+.0f}% of the floor->ceiling span)  "
                  f"exit={agg.loc[f'add_{k}','exit_rate']:.2f}")
        print("\nequalization sweep (collapse must hold across eps): "
              + ", ".join(f"{a.split('eps')[-1] if 'eps' in a else '1.00'}->top5={agg.loc[a,'top5_active']:.3f}"
                          for a in ["floor_eps0.25", "floor_eps0.50", "floor"] if a in agg.index))

        # nested historical path: cumulative concentration + retention, marginal per step
        path = ["floor"] + [NESTED_LABEL[k] for k in range(1, len(NESTED_ORDER))] + ["ceiling"]
        path = [a for a in path if a in agg.index]
        print("\n=== nested path (historical order): marginal Δ per privilege added ===")
        print(f"{'step':14s} {'top5':>6s} {'Δtop5':>7s} {'gini':>6s} {'exit':>6s} {'Δexit':>7s}")
        prev_t = prev_e = None
        for a in path:
            t, e, gi = agg.loc[a, "top5_active"], agg.loc[a, "exit_rate"], agg.loc[a, "gini_active"]
            dt = "" if prev_t is None else f"{t-prev_t:+.3f}"
            de = "" if prev_e is None else f"{e-prev_e:+.3f}"
            print(f"{a:14s} {t:6.3f} {dt:>7s} {gi:6.3f} {e:6.3f} {de:>7s}")
            prev_t, prev_e = t, e
        print("(large +Δtop5 = the privilege that manufactures concentration; "
              "large -Δexit at small +Δtop5 = a privilege that retains without concentrating)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=48)
    args = ap.parse_args()
    jobs = [(a, s, p, sd) for a in ARMS for (s, p) in CELLS for sd in SEEDS]
    print(f"running {len(jobs)} runs ({len(ARMS)} arms x {len(CELLS)} cells x {len(SEEDS)} seeds; "
          f"cached runs skip)", flush=True)
    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(runOne, *j): j for j in jobs}
        for fut in as_completed(futs):
            rows.append(fut.result())
    aggregate(rows)


if __name__ == "__main__":
    main()
