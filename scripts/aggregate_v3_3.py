#!/usr/bin/env python3
"""Aggregate a completed v3.3 endogenous-capacity arm into a summary CSV.

Reads an arm directory produced by scripts/run_v3_3_experiments.py (using its
MANIFEST_<arm>.json, or falling back to a walk of run_config.json files) and
emits one summary row per (config, seed). For the PANEL arm it additionally
runs the directional anti-circularity test: it reconstructs each agent's
capacity update from its TRUE inputs (tie stock, econ independence, tenure,
per-agent hetero factor, the generic membership benefit mu) and confirms the
structural residual against the model's recorded capacity is numerically zero,
then regresses that residual on lagged punishment received, punishment
delivered, and enforcer status with agent-clustered standard errors. If the
v3.3 anti-circularity invariant holds, those coefficients are ~0.

Every output CSV carries the model code sha256 and the aggregation timestamp,
both as columns and in a sidecar <name>.meta.json.

Usage:
  python scripts/aggregate_v3_3.py --arm erosion --dir results/v3_3_endogenous_capacity_v2
  python scripts/aggregate_v3_3.py --arm panel   --dir results/v3_3_endogenous_capacity_v2
"""

import argparse
import glob
import hashlib
import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import statsmodels.api as sm

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_FILE = os.path.join(REPO_ROOT, "src", "religion_fundamentalism_abm_v3_3.py")

EC_SNAPSHOT_STEPS = (50, 200, 449)


def codeFingerprint():
    with open(MODEL_FILE, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def utcNow():
    return datetime.now(timezone.utc).isoformat()


def loadRuns(arm, arm_dir):
    """return [(run_dir_abs, config_dict)] for the arm, preferring the manifest."""
    manifest_path = os.path.join(arm_dir, f"MANIFEST_{arm}.json")
    runs = []
    if os.path.exists(manifest_path):
        with open(manifest_path) as fh:
            manifest = json.load(fh)
        for entry in manifest["runs"]:
            run_dir = os.path.join(REPO_ROOT, entry["run_dir"])
            cfg_path = os.path.join(run_dir, "run_config.json")
            cfg = json.load(open(cfg_path)) if os.path.exists(cfg_path) else entry["config"]
            runs.append((run_dir, cfg))
        return runs
    # fallback: walk for run_config.json files whose arm matches
    for cfg_path in sorted(glob.glob(os.path.join(arm_dir, "**", "run_config.json"),
                                     recursive=True)):
        cfg = json.load(open(cfg_path))
        if cfg.get("arm") == arm:
            runs.append((os.path.dirname(cfg_path), cfg))
    return runs


def ecAtSteps(metrics, steps=EC_SNAPSHOT_STEPS):
    """mean_exit_capacity at the requested timesteps (NaN if absent)."""
    lut = metrics.set_index("t")["mean_exit_capacity"]
    return {s: float(lut.loc[s]) if s in lut.index else float("nan") for s in steps}


def enforcerPunishShare(agent_summary):
    """fraction of all punishment ACTS delivered by enforcers."""
    total = float(agent_summary["punish_issued"].sum())
    if total <= 0:
        return float("nan")
    enf = float(agent_summary.loc[agent_summary["is_enforcer"] == True,
                                  "punish_issued"].sum())
    return enf / total


def summariseRun(run_dir, cfg):
    """one summary row for a single run directory."""
    params = cfg["model_params"]
    metrics = pd.read_csv(os.path.join(run_dir, "metrics.csv"))
    agent_final = pd.read_csv(os.path.join(run_dir, "agent_final.csv"))
    agent_summary = pd.read_csv(os.path.join(run_dir, "agent_summary.csv"))

    last = metrics.iloc[-1]
    # final per-agent capacity distribution over ACTIVE (non-exited) members
    active = agent_final[agent_final["exited"] == False]
    caps = active["exit_capacity"]

    ec = ecAtSteps(metrics)
    row = {
        "arm": cfg["arm"],
        "run_dir": os.path.relpath(run_dir, REPO_ROOT),
        # every varied parameter (plus the fixed context that defines the cell)
        "seed": int(params["seed"]),
        "turnover_mode": params["turnover_mode"],
        "exit_capacity_mode": params["exit_capacity_mode"],
        "mu_membership_reward": float(params["mu_membership_reward"]),
        "ec_tenure_crowdout": float(params["ec_tenure_crowdout"]),
        "born_inside_frac": float(params["born_inside_frac"]),
        # capacity trajectory snapshots
        "ec50": ec[50],
        "ec200": ec[200],
        "ec449": ec[449],
        # final per-agent capacity distribution (active members)
        "n_active": int(len(active)),
        "exit_capacity_mean": float(caps.mean()) if len(caps) else float("nan"),
        "exit_capacity_sd": float(caps.std(ddof=0)) if len(caps) else float("nan"),
        "exit_capacity_ndistinct": int(caps.nunique()),
        # exit outcomes
        "cumulative_exit_rate": float(last["cumulative_exit_rate"]),
        "exit_rate_last100": float(last["exit_rate_last100"]),
        # composition + capacity components (final step, active members)
        "frac_born_inside": float(last["frac_born_inside"]),
        "mean_econ_independence": float(last["mean_econ_independence"]),
        "mean_outside_ties": float(last["mean_outside_ties"]),
        # enforcement concentration
        "enforcer_punish_share": enforcerPunishShare(agent_summary),
    }
    return row


def clip01(x):
    return np.clip(x, 0.0, 1.0)


def reconstructCapacity(panel, params):
    """deterministic reconstruction of each agent's capacity at step t+1 from its
    TRUE inputs at step t. mirrors _update_exit_capacity in the model exactly.

    the panel snapshots state AFTER the step-t update, so a transition
    (row t -> row t+1) for the SAME continuous agent satisfies
    tenure(t+1) == tenure(t)+1. turnover replacements reset tenure and are
    excluded by that continuity check. returns the panel with prediction,
    residual, and the lagged enforcement regressors, restricted to valid
    transitions.
    """
    p_tie_decay = float(params["ec_tie_decay"])
    p_tie_renewal_base = float(params["ec_tie_renewal_base"])
    p_tie_renewal = float(params["ec_tie_renewal"])
    p_crowdout = float(params["ec_tenure_crowdout"])
    p_econ_recovery_base = float(params["ec_econ_recovery_base"])
    p_dependence = float(params["ec_dependence_rate"])
    mu = float(np.clip(float(params["mu_membership_reward"]), 0.0, 1.0))

    df = panel.sort_values(["agent_id", "t"]).reset_index(drop=True)
    g = df.groupby("agent_id", sort=False)
    # next-step (t+1) recorded state for the same slot
    df["t_next"] = g["t"].shift(-1)
    df["tenure_next"] = g["tenure"].shift(-1)
    df["cap_next"] = g["exit_capacity"].shift(-1)
    # per-step punishment DELIVERED at the current step t = d(issued_cum)
    df["delivered_step"] = g["issued_cum"].diff()

    # prediction of capacity at t+1 from the current row's (step-t) inputs.
    # tenure used in the crowd-out term is tenure at t+1 (model increments
    # tenure before applying decay), i.e. the recorded tenure_next.
    tie_renewal_base = p_tie_renewal_base * df["ec_hetero"]
    econ_recovery_base = p_econ_recovery_base * df["ec_hetero"]
    renewal = tie_renewal_base + p_tie_renewal * df["outside_ties"]
    crowd = p_crowdout * np.minimum(df["tenure_next"] / 100.0, 1.0)
    decay = p_tie_decay * df["outside_ties"] + crowd
    ot_pred = clip01(df["outside_ties"] + renewal - decay)
    econ_decay = p_dependence * mu * df["econ_independence"]
    ei_pred = clip01(df["econ_independence"] + econ_recovery_base - econ_decay)
    df["cap_pred"] = 0.5 * ot_pred + 0.5 * ei_pred
    df["residual"] = df["cap_pred"] - df["cap_next"]

    # valid transition: consecutive steps, same continuous agent, defined lag
    valid = (
        (df["t_next"] == df["t"] + 1)
        & (df["tenure_next"] == df["tenure"] + 1)
        & df["delivered_step"].notna()
        & df["cap_next"].notna()
    )
    return df[valid].copy()


def antiCircularity(panel_run_dir, cfg):
    """run the directional anti-circularity test on a panel run.

    returns (result_df, meta) where result_df has one row per regression term
    (coef/se/p under agent-clustered SEs) and meta carries the max absolute
    structural residual and sample sizes.
    """
    params = cfg["model_params"]
    panel = pd.read_csv(os.path.join(panel_run_dir, "panel.csv"))
    rec = reconstructCapacity(panel, params)

    max_abs_resid = float(rec["residual"].abs().max())

    # regress the structural residual on LAGGED enforcement (measured at step t)
    y = rec["residual"].to_numpy(dtype=float)
    X = rec[["received_step", "delivered_step", "is_enforcer"]].to_numpy(dtype=float)
    X = sm.add_constant(X, has_constant="add")
    groups = rec["agent_id"].to_numpy()
    model = sm.OLS(y, X)
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": groups})

    terms = ["intercept", "punishment_received_lag",
             "punishment_delivered_lag", "is_enforcer_lag"]
    result = pd.DataFrame({
        "term": terms,
        "coef": fit.params,
        "se": fit.bse,
        "p_value": fit.pvalues,
    })
    result["max_abs_structural_residual"] = max_abs_resid
    result["n_transitions"] = int(len(rec))
    result["n_clusters"] = int(pd.Series(groups).nunique())
    meta = {
        "max_abs_structural_residual": max_abs_resid,
        "n_transitions": int(len(rec)),
        "n_clusters": int(pd.Series(groups).nunique()),
        "regression": "residual ~ received_step + delivered_step + is_enforcer "
                      "(cluster-robust SE by agent_id)",
    }
    return result, meta


def stampAndWrite(df, out_path, sha, ts, extra_meta=None):
    """write a CSV carrying the code sha256 + aggregation timestamp as columns,
    and a sidecar .meta.json with the same provenance."""
    df = df.copy()
    df["code_sha256"] = sha
    df["aggregated_utc"] = ts
    df.to_csv(out_path, index=False)
    meta = {"code_sha256": sha, "aggregated_utc": ts,
            "model_file": os.path.relpath(MODEL_FILE, REPO_ROOT),
            "n_rows": int(len(df))}
    if extra_meta:
        meta.update(extra_meta)
    with open(out_path + ".meta.json", "w") as fh:
        json.dump(meta, fh, indent=2, sort_keys=True)
    return out_path


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", required=True,
                    choices=["erosion", "closure", "generational",
                             "live_econ", "panel"])
    ap.add_argument("--dir", required=True,
                    help="arm output root (the --out passed to the driver)")
    ap.add_argument("--out", default=None,
                    help="summary CSV path (default <dir>/<arm>_summary.csv)")
    args = ap.parse_args()

    arm_dir = args.dir if os.path.isabs(args.dir) else os.path.join(REPO_ROOT, args.dir)
    sha, ts = codeFingerprint(), utcNow()

    runs = loadRuns(args.arm, arm_dir)
    if not runs:
        raise SystemExit(f"no runs found for arm '{args.arm}' under {arm_dir}")

    rows = [summariseRun(run_dir, cfg) for run_dir, cfg in runs]
    summary = pd.DataFrame(rows)

    out_path = args.out or os.path.join(arm_dir, f"{args.arm}_summary.csv")
    stampAndWrite(summary, out_path, sha, ts,
                  extra_meta={"arm": args.arm, "n_runs": len(runs)})
    print(f"[summary] arm '{args.arm}': {len(rows)} run(s) -> "
          f"{os.path.relpath(out_path, REPO_ROOT)}")

    if args.arm == "panel":
        # exactly one panel run; run the anti-circularity test on it
        panel_run_dir, panel_cfg = runs[0]
        result, meta = antiCircularity(panel_run_dir, panel_cfg)
        ac_path = os.path.join(arm_dir, "anticircularity_panel.csv")
        stampAndWrite(result, ac_path, sha, ts, extra_meta=meta)
        print(f"[anti-circularity] max|structural residual| = "
              f"{meta['max_abs_structural_residual']:.3e} over "
              f"{meta['n_transitions']} transitions -> "
              f"{os.path.relpath(ac_path, REPO_ROOT)}")

    return summary, out_path


if __name__ == "__main__":
    main()
