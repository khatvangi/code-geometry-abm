#!/usr/bin/env python3
"""v2.9 acquiescence sweep: calibration and confirmatory stages.

stage 1 (calibration): fix code-geometry at known enforcement-locked point,
sweep omega params to find which produce CAPTURE (capture_prevalence >= 0.90).

stage 2 (confirmatory): using best-calibration omegas, sweep code-geometry
params for direct comparison with v2.7/v2.8.

usage:
  # stage 1: calibrate omegas
  python scripts/run_v2_9_acquiescence_sweep.py \\
      --stage calibration \\
      --out results/v2.9_acquiescence_calibration

  # stage 2: confirmatory (after choosing best omegas from stage 1)
  python scripts/run_v2_9_acquiescence_sweep.py \\
      --stage confirmatory \\
      --out results/v2.9_confirmatory_sweep \\
      --omega-x 0.02 --omega-delta 0.03 --omega-e 0.04 \\
      --omega-t 0.02 --gamma-q-fixed 0.08
"""
import argparse
import itertools
import json
import math
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

REGIME_ORDER = ["COLLAPSE", "CAPTURE", "MIXED", "QUIET"]


def classify_regime(exit_rate: float, capture_prevalence: float,
                    fund_prevalence: float, max_punish: float,
                    capture_exit_cap: float) -> str:
    """classify regime using capture_prevalence (v2.9) for CAPTURE."""
    if exit_rate >= 0.90:
        return "COLLAPSE"
    # v2.9: use capture_prevalence (includes acquiescent agents)
    if capture_prevalence >= 0.90 and exit_rate <= capture_exit_cap:
        return "CAPTURE"
    if max_punish >= 0.10:
        return "MIXED"
    return "QUIET"


def parse_floats(csv_text: str) -> list[float]:
    return [float(x.strip()) for x in csv_text.split(",") if x.strip()]


def load_best_params(best_json: Path):
    d = json.loads(best_json.read_text(encoding="utf-8"))
    p = d.get("params", {})
    return {
        "membership_benefit": float(p.get("membership_benefit", 0.03)),
        "membership_benefit_threat": float(p.get("membership_benefit_threat", 0.10)),
        "exit_opportunity_threat_coeff": float(p.get("exit_opportunity_threat_coeff", 1.5)),
        "exit_block_exponent": float(p.get("exit_block_exponent", 2.5)),
        "exit_commit_steps": int(p.get("exit_commit_steps", 8)),
        "exit_cost": float(p.get("exit_cost", 0.4)),
        "shock_strength": float(p.get("shock_strength", 0.25)),
    }


def top_share(values: np.ndarray, frac: float) -> float:
    x = np.asarray(values, dtype=float)
    total = float(np.sum(x))
    if x.size == 0 or total <= 0:
        return 0.0
    k = max(1, int(math.ceil(frac * x.size)))
    return float(np.sum(np.sort(x)[::-1][:k]) / total)


def run_one(
    model_path: Path,
    run_dir: Path,
    seed: int,
    sigma: float,
    pi_reward: float,
    delta0: float,
    eta: float,
    omega_x: float,
    omega_delta: float,
    omega_e: float,
    omega_t: float,
    gamma_q: float,
    acquiescence_threshold: float,
    best: dict,
    punish_floor: float,
    base_opp: float,
    exit_threshold: float,
    steps: int,
    n: int = 350,
    p_rewire: float = 0.0,
    rewire_threshold: float = 0.20,
    rewire_random_fallback: float = 0.10,
):
    metrics_path = run_dir / "metrics.csv"
    agent_path = run_dir / "agent_summary.csv"
    if metrics_path.exists() and agent_path.exists():
        return

    run_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, str(model_path),
        "--outdir", str(run_dir),
        "--steps", str(steps),
        "--n", str(n),
        "--graph", "scale_free",
        "--seed", str(seed),
        "--sigma", f"{sigma:.2f}",
        "--pi_reward", f"{pi_reward:.2f}",
        "--alpha_punish_revalue", "0.0",
        "--mu_membership_reward", "0.0",
        "--delta_outside_degrade", f"{delta0:.2f}",
        "--eta_delta_drift", f"{eta:.2f}",
        "--punish_floor", f"{punish_floor:.2f}",
        "--exit_opportunity_base", f"{base_opp:.2f}",
        "--exit_threshold", f"{exit_threshold:.2f}",
        # v2.9 omega params
        "--omega_x", f"{omega_x:.4f}",
        "--omega_delta", f"{omega_delta:.4f}",
        "--omega_e", f"{omega_e:.4f}",
        "--omega_t", f"{omega_t:.4f}",
        "--gamma_q", f"{gamma_q:.4f}",
        "--acquiescence_threshold", f"{acquiescence_threshold:.2f}",
        # homophilic rewiring
        "--p_rewire", f"{p_rewire:.4f}",
        "--rewire_threshold", f"{rewire_threshold:.4f}",
        "--rewire_random_fallback", f"{rewire_random_fallback:.4f}",
        # fixed institutional params
        "--shock_schedule", "100,220,320",
        "--shock_strength", str(best["shock_strength"]),
        "--membership_benefit", str(best["membership_benefit"]),
        "--membership_benefit_threat", str(best["membership_benefit_threat"]),
        "--exit_opportunity_threat_coeff", str(best["exit_opportunity_threat_coeff"]),
        "--exit_block_exponent", str(best["exit_block_exponent"]),
        "--exit_commit_steps", str(best["exit_commit_steps"]),
        "--exit_cost", str(best["exit_cost"]),
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
        "--no_movie",
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run_grid(model_path, root, tasks_list, workers):
    n_total = len(tasks_list)
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(run_one, model_path, **t) for t in tasks_list]
        for fut in as_completed(futs):
            fut.result()
            done += 1
            if done % 20 == 0 or done == n_total:
                print(f"completed {done}/{n_total}")


def collect_seed_rows(root: Path, capture_exit_cap: float) -> pd.DataFrame:
    """aggregate per-seed results from directory tree."""
    rows = []
    for mpath in sorted(root.rglob("metrics.csv")):
        run_dir = mpath.parent
        apath = run_dir / "agent_summary.csv"
        if not apath.exists():
            continue

        # parse directory structure to recover params
        parts = mpath.relative_to(root).parts
        params_from_dir = {}
        for part in parts[:-1]:  # skip "metrics.csv" filename, and "seed_XX"
            if "_" in part:
                key_val = part.split("_", 1)
                if len(key_val) == 2:
                    try:
                        params_from_dir[key_val[0]] = float(key_val[1])
                    except ValueError:
                        pass
        # get seed from last dir
        seed_part = parts[-2] if len(parts) >= 2 else ""
        try:
            seed = int(seed_part.split("_")[-1])
        except (ValueError, IndexError):
            continue

        mdf = pd.read_csv(mpath)
        adf = pd.read_csv(apath)
        if mdf.empty:
            continue

        final = mdf.iloc[-1]
        fund_prevalence = float(final.get("fund_prevalence", np.nan))
        capture_prevalence = float(final.get("capture_prevalence", np.nan))
        exit_rate = float(final.get("exit_rate", np.nan))
        max_punish = float(mdf["punish_rate"].max()) if "punish_rate" in mdf.columns else np.nan
        final_delta = float(final.get("current_delta", np.nan))
        mean_q = float(final.get("mean_q", np.nan))
        q_above_threshold = float(final.get("q_above_threshold", np.nan))

        punish = pd.to_numeric(adf.get("punish_issued", pd.Series(dtype=float)),
                               errors="coerce").fillna(0.0).to_numpy(dtype=float)
        top5 = top_share(punish, 0.05)

        step_share = pd.to_numeric(
            mdf.get("enforcer_punish_share_step", pd.Series(dtype=float)), errors="coerce"
        ).replace([np.inf, -np.inf], np.nan)
        punish_rate = pd.to_numeric(mdf.get("punish_rate", pd.Series(dtype=float)), errors="coerce")
        active_steps = punish_rate > 0
        if active_steps.any():
            enforcer_share = float(step_share[active_steps].fillna(0.0).mean())
        else:
            enforcer_share = 0.0
        enforcer_share = float(np.clip(enforcer_share, 0.0, 1.0))

        regime = classify_regime(exit_rate, capture_prevalence, fund_prevalence,
                                 max_punish, capture_exit_cap)

        row = {
            "seed": seed,
            "final_fund_prevalence": fund_prevalence,
            "final_capture_prevalence": capture_prevalence,
            "final_mean_q": mean_q,
            "final_q_above_threshold": q_above_threshold,
            "final_exit_rate": exit_rate,
            "max_punish": max_punish,
            "top5_punishment_share": top5,
            "enforcer_punish_share": enforcer_share,
            "final_current_delta": final_delta,
            "regime": regime,
            "run_dir": str(run_dir),
        }
        # add all directory-encoded params
        row.update(params_from_dir)
        rows.append(row)
    return pd.DataFrame(rows)


def majority_regime(s: pd.Series) -> str:
    vc = s.value_counts()
    if vc.empty:
        return "QUIET"
    topn = vc.max()
    tied = sorted([k for k, n in vc.items() if n == topn], key=lambda x: REGIME_ORDER.index(x))
    return tied[0]


def consensus_regime(s: pd.Series, threshold: float = 0.7) -> str:
    """return regime if >= threshold fraction of seeds agree, else majority."""
    n = len(s)
    if n == 0:
        return "QUIET"
    required = int(math.ceil(threshold * n))
    vc = s.value_counts()
    for regime in REGIME_ORDER:
        if vc.get(regime, 0) >= required:
            return regime
    return majority_regime(s)


def summarize(seed_df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    rows = []
    for keys, g in seed_df.groupby(group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, [float(k) for k in keys]))
        row["n_seeds"] = int(len(g))
        row["regime_consensus"] = consensus_regime(g["regime"])
        row["regime_majority"] = majority_regime(g["regime"])
        for r in REGIME_ORDER:
            row[f"n_{r.lower()}"] = int((g["regime"] == r).sum())
        row["median_fund_prevalence"] = float(g["final_fund_prevalence"].median())
        row["median_capture_prevalence"] = float(g["final_capture_prevalence"].median())
        row["median_mean_q"] = float(g["final_mean_q"].median())
        row["median_q_above_threshold"] = float(g["final_q_above_threshold"].median())
        row["median_exit_rate"] = float(g["final_exit_rate"].median())
        row["median_top5_share"] = float(g["top5_punishment_share"].median())
        row["median_max_punish"] = float(g["max_punish"].median())
        row["median_enforcer_punish_share"] = float(g["enforcer_punish_share"].median())
        row["median_final_delta"] = float(g["final_current_delta"].median())
        rows.append(row)
    return pd.DataFrame(rows).sort_values(group_cols)


def build_calibration_tasks(args, model_path, root, best):
    """stage 1: sweep omega params at fixed code-geometry."""
    omega_x_vals = parse_floats(args.omega_x_values)
    omega_delta_vals = parse_floats(args.omega_delta_values)
    omega_e_vals = parse_floats(args.omega_e_values)
    omega_t_vals = parse_floats(args.omega_t_values)
    gamma_q_vals = parse_floats(args.gamma_q_values)
    seeds = list(range(1, args.seeds + 1))

    # fixed code-geometry: enforcement-locked point
    sigma = 0.95
    pi_reward = 0.50
    base_opp = 0.30
    eta = 0.10
    delta0 = 0.10

    tasks = []
    for ox, od, oe, ot, gq in itertools.product(
        omega_x_vals, omega_delta_vals, omega_e_vals, omega_t_vals, gamma_q_vals
    ):
        combo_dir = (
            root
            / f"ox_{ox:.4f}"
            / f"od_{od:.4f}"
            / f"oe_{oe:.4f}"
            / f"ot_{ot:.4f}"
            / f"gq_{gq:.4f}"
        )
        for seed in seeds:
            run_dir = combo_dir / f"seed_{seed:02d}"
            tasks.append(dict(
                run_dir=run_dir, seed=seed,
                sigma=sigma, pi_reward=pi_reward, delta0=delta0, eta=eta,
                omega_x=ox, omega_delta=od, omega_e=oe, omega_t=ot, gamma_q=gq,
                acquiescence_threshold=args.acquiescence_threshold,
                best=best, punish_floor=args.punish_floor,
                base_opp=base_opp, exit_threshold=args.exit_threshold,
                steps=args.steps, n=args.n,
                p_rewire=args.p_rewire, rewire_threshold=args.rewire_threshold,
                rewire_random_fallback=args.rewire_random_fallback,
            ))

    n_combos = len(omega_x_vals) * len(omega_delta_vals) * len(omega_e_vals) * len(omega_t_vals) * len(gamma_q_vals)
    print(f"stage 1 calibration: {n_combos} combos x {len(seeds)} seeds = {len(tasks)} runs")
    print(f"  fixed: sigma={sigma} pi={pi_reward} base_opp={base_opp} eta={eta} delta0={delta0}")
    return tasks, ["ox", "od", "oe", "ot", "gq"]


def build_confirmatory_tasks(args, model_path, root, best):
    """stage 2: sweep code-geometry with fixed best-calibration omegas."""
    sigma_vals = parse_floats(args.sigma_values)
    pi_vals = parse_floats(args.pi_values)
    base_opp_vals = parse_floats(args.base_opp_values)
    eta_vals = parse_floats(args.eta_values)
    delta_vals = parse_floats(args.delta_values)
    seeds = list(range(1, args.seeds + 1))

    tasks = []
    for sigma, pi, bopp, eta, delta0 in itertools.product(
        sigma_vals, pi_vals, base_opp_vals, eta_vals, delta_vals
    ):
        combo_dir = (
            root
            / f"sigma_{sigma:.2f}"
            / f"pi_{pi:.2f}"
            / f"bopp_{bopp:.2f}"
            / f"eta_{eta:.2f}"
            / f"delta0_{delta0:.2f}"
        )
        for seed in seeds:
            run_dir = combo_dir / f"seed_{seed:02d}"
            tasks.append(dict(
                run_dir=run_dir, seed=seed,
                sigma=sigma, pi_reward=pi, delta0=delta0, eta=eta,
                omega_x=args.omega_x_fixed, omega_delta=args.omega_delta_fixed,
                omega_e=args.omega_e_fixed, omega_t=args.omega_t_fixed,
                gamma_q=args.gamma_q_fixed,
                acquiescence_threshold=args.acquiescence_threshold,
                best=best, punish_floor=args.punish_floor,
                base_opp=bopp, exit_threshold=args.exit_threshold,
                steps=args.steps, n=args.n,
                p_rewire=args.p_rewire, rewire_threshold=args.rewire_threshold,
                rewire_random_fallback=args.rewire_random_fallback,
            ))

    n_combos = len(sigma_vals) * len(pi_vals) * len(base_opp_vals) * len(eta_vals) * len(delta_vals)
    print(f"stage 2 confirmatory: {n_combos} code-geometry combos x {len(seeds)} seeds = {len(tasks)} runs")
    print(f"  fixed omegas: x={args.omega_x_fixed} d={args.omega_delta_fixed} "
          f"e={args.omega_e_fixed} t={args.omega_t_fixed} q={args.gamma_q_fixed}")
    return tasks, ["sigma", "pi", "bopp", "eta", "delta0"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="src/religion_fundamentalism_abm_v2_9.py")
    ap.add_argument("--best", default="runs/batch_v2_3_search_20260213_043518/summary/BEST_PARAMS.json")
    ap.add_argument("--stage", required=True, choices=["calibration", "confirmatory"])
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--steps", type=int, default=450)
    ap.add_argument("--punish-floor", type=float, default=0.08)
    ap.add_argument("--exit-threshold", type=float, default=-1.0)
    ap.add_argument("--capture-exit-cap", type=float, default=0.20)
    ap.add_argument("--acquiescence-threshold", type=float, default=0.60)
    ap.add_argument("--n", type=int, default=350, help="population size (default 350)")
    # homophilic rewiring
    ap.add_argument("--p-rewire", type=float, default=0.0)
    ap.add_argument("--rewire-threshold", type=float, default=0.20)
    ap.add_argument("--rewire-random-fallback", type=float, default=0.10)

    # stage 1: omega sweep values
    ap.add_argument("--omega-x-values", default="0.01,0.02,0.04")
    ap.add_argument("--omega-delta-values", default="0.01,0.03,0.05")
    ap.add_argument("--omega-e-values", default="0.02,0.04,0.08")
    ap.add_argument("--omega-t-values", default="0.01,0.02,0.04")
    ap.add_argument("--gamma-q-values", default="0.05,0.08,0.12")

    # stage 2: code-geometry sweep values
    ap.add_argument("--sigma-values", default="0.25,0.75,0.95")
    ap.add_argument("--pi-values", default="0.05,0.25")
    ap.add_argument("--base-opp-values", default="0.3,0.6,0.9")
    ap.add_argument("--eta-values", default="0.0,0.2")
    ap.add_argument("--delta-values", default="0.0,0.1")

    # stage 2: fixed omegas from calibration
    ap.add_argument("--omega-x-fixed", type=float, default=0.02)
    ap.add_argument("--omega-delta-fixed", type=float, default=0.03)
    ap.add_argument("--omega-e-fixed", type=float, default=0.04)
    ap.add_argument("--omega-t-fixed", type=float, default=0.02)
    ap.add_argument("--gamma-q-fixed", type=float, default=0.08)

    args = ap.parse_args()

    out_root = Path(args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    model_path = Path(args.model).resolve()
    best = load_best_params(Path(args.best))

    if args.stage == "calibration":
        tasks, group_cols = build_calibration_tasks(args, model_path, out_root, best)
    else:
        tasks, group_cols = build_confirmatory_tasks(args, model_path, out_root, best)

    run_grid(model_path, out_root, tasks, args.workers)

    seeds_df = collect_seed_rows(out_root, args.capture_exit_cap)
    seeds_df.to_csv(out_root / "sweep_seed_results.csv", index=False)

    summary = summarize(seeds_df, group_cols)
    summary.to_csv(out_root / "sweep_summary.csv", index=False)

    # write report
    lines = [
        f"stage={args.stage}",
        f"n_cells={len(summary)}",
        f"n_runs={len(seeds_df)}",
        f"capture_exit_cap={args.capture_exit_cap}",
        f"acquiescence_threshold={args.acquiescence_threshold}",
        f"regime_consensus_counts={summary['regime_consensus'].value_counts().to_dict()}",
        f"regime_majority_counts={summary['regime_majority'].value_counts().to_dict()}",
        f"seed_regime_counts={seeds_df['regime'].value_counts().to_dict()}",
    ]
    if not summary.empty:
        lines.append(f"capture_prevalence_median_range=({summary['median_capture_prevalence'].min():.4f},{summary['median_capture_prevalence'].max():.4f})")
        lines.append(f"mean_q_median_range=({summary['median_mean_q'].min():.4f},{summary['median_mean_q'].max():.4f})")
    (out_root / "sweep_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\nWrote {out_root / 'sweep_summary.csv'}")
    print(f"Wrote {out_root / 'sweep_seed_results.csv'}")
    print(f"Wrote {out_root / 'sweep_report.txt'}")


if __name__ == "__main__":
    main()
