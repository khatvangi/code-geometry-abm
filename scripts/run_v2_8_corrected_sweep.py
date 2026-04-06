#!/usr/bin/env python3
"""v2.8 multiplex sweep with corrected parameters.

fixes applied:
1. uses BEST_PARAMS exit values from v2.5 sweep (exit_block_exponent=5.98,
   exit_cost=1.0, exit_commit_steps=12, membership_benefit=0.063,
   exit_opportunity_threat_coeff=2.91, shock_strength=0.10)
2. CAPTURE threshold uses fund_prevalence >= 0.90 (matching v2.5 baseline)
3. parameter grid includes base_opp (exit_opportunity_base) for direct
   comparison with v2.5 baseline sweep
"""
import argparse
import math
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

REGIME_ORDER = ["COLLAPSE", "CAPTURE", "MIXED", "QUIET"]

# --- v2.5 BEST_PARAMS (from runs/batch_v2_3_search_.../BEST_PARAMS.json) ---
BEST_PARAMS = {
    "membership_benefit": 0.063,
    "membership_benefit_threat": 0.106,
    "exit_opportunity_threat_coeff": 2.91,
    "exit_block_exponent": 5.98,
    "exit_commit_steps": 12,
    "exit_cost": 1.0,
    "shock_strength": 0.10,
}


def classify_regime(
    exit_rate: float,
    prevalence_active: float,
    max_punish: float,
) -> str:
    """regime classifier matching v2.5 baseline thresholds."""
    if exit_rate >= 0.90:
        return "COLLAPSE"
    # fund_prevalence >= 0.90 — matches v2.5, NOT the 0.10 used in codex sweeps
    if prevalence_active >= 0.90 and exit_rate <= 0.20:
        return "CAPTURE"
    if max_punish >= 0.10:
        return "MIXED"
    return "QUIET"


def classify_regime_hierarchical(
    exit_rate: float,
    prevalence_active: float,
    max_punish: float,
    enforcer_share: float,
) -> str:
    """hierarchical variant adding CAPTURE_HIERARCHICAL."""
    if exit_rate >= 0.90:
        return "COLLAPSE"
    if prevalence_active >= 0.90 and exit_rate <= 0.20:
        if enforcer_share >= 0.70:
            return "CAPTURE_HIERARCHICAL"
        return "CAPTURE"
    if max_punish >= 0.10:
        return "MIXED"
    return "QUIET"


def top_share(values: np.ndarray, frac: float) -> float:
    x = np.asarray(values, dtype=float)
    total = float(np.sum(x))
    if x.size == 0 or total <= 0:
        return 0.0
    k = max(1, int(math.ceil(frac * x.size)))
    return float(np.sum(np.sort(x)[::-1][:k]) / total)


def pick_punish_signal(mdf: pd.DataFrame) -> pd.Series:
    if "punish_intensity_step" in mdf.columns:
        s = pd.to_numeric(mdf["punish_intensity_step"], errors="coerce")
    elif "punish_rate" in mdf.columns:
        s = pd.to_numeric(mdf["punish_rate"], errors="coerce")
    else:
        s = pd.Series(dtype=float)
    return s.replace([np.inf, -np.inf], np.nan)


def run_one(
    model_script: Path,
    python_bin: str,
    run_dir: Path,
    seed: int,
    sigma: float,
    pi_reward: float,
    base_opp: float,
    eta: float,
    delta0: float,
    steps: int,
    n_agents: int,
    quiet: bool,
) -> None:
    """run a single simulation with BEST_PARAMS exit values."""
    metrics_path = run_dir / "metrics.csv"
    agents_path = run_dir / "agent_summary.csv"
    if metrics_path.exists() and agents_path.exists():
        return

    run_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        python_bin,
        str(model_script),
        "--outdir", str(run_dir),
        "--n", str(n_agents),
        "--steps", str(steps),
        "--seed", str(seed),
        "--sigma", f"{sigma:.2f}",
        "--pi-reward", f"{pi_reward:.2f}",
        # exit params from BEST_PARAMS
        "--exit-block-exponent", f"{BEST_PARAMS['exit_block_exponent']:.2f}",
        "--exit-cost", f"{BEST_PARAMS['exit_cost']:.2f}",
        "--exit-commit-steps", str(BEST_PARAMS["exit_commit_steps"]),
        "--membership-benefit", f"{BEST_PARAMS['membership_benefit']:.4f}",
        "--membership-benefit-threat", f"{BEST_PARAMS['membership_benefit_threat']:.4f}",
        "--exit-opportunity-threat-coeff", f"{BEST_PARAMS['exit_opportunity_threat_coeff']:.2f}",
        "--exit-opportunity-base", f"{base_opp:.2f}",
        "--shock-strength", f"{BEST_PARAMS['shock_strength']:.2f}",
        "--shock-schedule", "100,220,320",
        # endogenous delta
        "--delta-outside-degrade", f"{delta0:.2f}",
        "--eta-delta-drift", f"{eta:.2f}",
        # standard fixed params
        "--enforcer-quota-frac", "0.08",
        "--A-enforcer-monopoly", "0.35",
        "--lam-punish", "0.25",
        "--d0", "0.18",
    ]
    kw = {}
    if quiet:
        kw = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    subprocess.run(cmd, check=True, **kw)


def analyze_run(run_dir: Path) -> dict | None:
    """extract summary metrics from a completed run."""
    metrics_path = run_dir / "metrics.csv"
    agents_path = run_dir / "agent_summary.csv"
    if not metrics_path.exists():
        return None

    mdf = pd.read_csv(metrics_path)
    if mdf.empty:
        return None

    last = mdf.iloc[-1]
    exit_rate = float(last.get("exit_rate", 0))
    fund_prev = float(last.get("fund_prevalence", 0))

    punish_sig = pick_punish_signal(mdf)
    max_punish = float(punish_sig.max()) if len(punish_sig) > 0 and not punish_sig.isna().all() else 0.0

    # enforcer share from per-step data
    if "enforcer_punish_share_step" in mdf.columns:
        esh = pd.to_numeric(mdf["enforcer_punish_share_step"], errors="coerce").fillna(0)
        enforcer_share = float(esh.iloc[-1]) if len(esh) > 0 else 0.0
    else:
        enforcer_share = 0.0

    # concentration from agent_summary if available
    top5 = 0.0
    top10 = 0.0
    if agents_path.exists():
        try:
            adf = pd.read_csv(agents_path)
            if "punished_total" in adf.columns:
                pvals = adf["punished_total"].values.astype(float)
                top5 = top_share(pvals, 0.05)
                top10 = top_share(pvals, 0.10)
        except Exception:
            pass

    # rewiring
    rewire_peer = float(mdf["rewire_peer_step"].median()) if "rewire_peer_step" in mdf.columns else 0
    rewire_inst = float(mdf["rewire_inst_step"].median()) if "rewire_inst_step" in mdf.columns else 0
    rewire_media = float(mdf["rewire_media_step"].median()) if "rewire_media_step" in mdf.columns else 0

    delta_final = float(last.get("current_delta", 0))

    regime = classify_regime(exit_rate, fund_prev, max_punish)
    regime_h = classify_regime_hierarchical(exit_rate, fund_prev, max_punish, enforcer_share)

    return {
        "exit_rate": exit_rate,
        "fund_prevalence": fund_prev,
        "max_punish": max_punish,
        "enforcer_share": enforcer_share,
        "top5_share": top5,
        "top10_share": top10,
        "rewire_peer": rewire_peer,
        "rewire_inst": rewire_inst,
        "rewire_media": rewire_media,
        "delta_final": delta_final,
        "regime": regime,
        "regime_hierarchical": regime_h,
    }


def main():
    ap = argparse.ArgumentParser(description="v2.8 corrected sweep with BEST_PARAMS")
    ap.add_argument("--out", required=True, help="output root directory")
    ap.add_argument("--model-script", default="codex-mod/scaleup/scripts/simulate_v2_8_multiplex.py")
    ap.add_argument("--python-bin", default=None)

    # swept parameters
    ap.add_argument("--sigma-values", default="0.25,0.75,0.95")
    ap.add_argument("--pi-values", default="0.05,0.25")
    ap.add_argument("--base-opp-values", default="0.3,0.6,0.9")
    ap.add_argument("--eta-values", default="0.0,0.2")
    ap.add_argument("--delta-values", default="0.0,0.1")

    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--steps", type=int, default=450)
    ap.add_argument("--n", type=int, default=10000)
    ap.add_argument("--quiet", action="store_true", help="suppress subprocess output")
    args = ap.parse_args()

    out_root = Path(args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    model_script = Path(args.model_script).resolve()
    python_bin = args.python_bin or sys.executable

    sigmas = [float(x) for x in args.sigma_values.split(",")]
    pis = [float(x) for x in args.pi_values.split(",")]
    opps = [float(x) for x in args.base_opp_values.split(",")]
    etas = [float(x) for x in args.eta_values.split(",")]
    deltas = [float(x) for x in args.delta_values.split(",")]

    # build grid
    cells = []
    for eta in etas:
        for d0 in deltas:
            for sig in sigmas:
                for pi in pis:
                    for opp in opps:
                        cells.append((eta, d0, sig, pi, opp))

    n_cells = len(cells)
    n_runs = n_cells * args.seeds
    print(f"grid: {n_cells} cells x {args.seeds} seeds = {n_runs} runs")
    print(f"  sigma: {sigmas}")
    print(f"  pi_reward: {pis}")
    print(f"  base_opp: {opps}")
    print(f"  eta: {etas}")
    print(f"  delta0: {deltas}")
    print(f"  n={args.n}, steps={args.steps}")
    print(f"  BEST_PARAMS: {BEST_PARAMS}")
    print()

    # run simulations
    futures = {}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for (eta, d0, sig, pi, opp) in cells:
            for seed in range(1, args.seeds + 1):
                run_dir = (
                    out_root
                    / f"eta_{eta:.2f}"
                    / f"delta0_{d0:.2f}"
                    / f"sigma_{sig:.2f}"
                    / f"pi_{pi:.2f}"
                    / f"base_opp_{opp:.1f}"
                    / f"seed_{seed:02d}"
                )
                fut = ex.submit(
                    run_one,
                    model_script, python_bin, run_dir, seed,
                    sig, pi, opp, eta, d0,
                    args.steps, args.n, args.quiet,
                )
                futures[fut] = (eta, d0, sig, pi, opp, seed, run_dir)

        done = 0
        for fut in as_completed(futures):
            done += 1
            key = futures[fut]
            try:
                fut.result()
            except Exception as e:
                print(f"  FAILED {key}: {e}")
            if done % 20 == 0 or done == n_runs:
                print(f"  completed {done}/{n_runs}")

    # collect results
    seed_rows = []
    for (eta, d0, sig, pi, opp) in cells:
        for seed in range(1, args.seeds + 1):
            run_dir = (
                out_root
                / f"eta_{eta:.2f}"
                / f"delta0_{d0:.2f}"
                / f"sigma_{sig:.2f}"
                / f"pi_{pi:.2f}"
                / f"base_opp_{opp:.1f}"
                / f"seed_{seed:02d}"
            )
            result = analyze_run(run_dir)
            if result is None:
                continue
            seed_rows.append({
                "eta": eta,
                "delta0": d0,
                "sigma": sig,
                "pi_reward": pi,
                "base_opp": opp,
                "seed": seed,
                **result,
            })

    seed_df = pd.DataFrame(seed_rows)
    seed_df.to_csv(out_root / "seed_results.csv", index=False)
    print(f"\nseed-level results: {len(seed_df)} runs")

    # regime counts
    if len(seed_df) > 0:
        print("\n--- seed-level regime counts ---")
        print(seed_df["regime"].value_counts().to_string())
        print("\n--- seed-level hierarchical regime counts ---")
        print(seed_df["regime_hierarchical"].value_counts().to_string())

    # cell-level summary (majority vote, ceil(0.7*n_seeds) consensus)
    gcols = ["eta", "delta0", "sigma", "pi_reward", "base_opp"]
    cell_rows = []
    for keys, grp in seed_df.groupby(gcols):
        n_s = len(grp)
        regime_counts = grp["regime"].value_counts()
        majority = regime_counts.index[0]
        cell_rows.append({
            **dict(zip(gcols, keys)),
            "n_seeds": n_s,
            "regime_majority": majority,
            "n_collapse": int(regime_counts.get("COLLAPSE", 0)),
            "n_capture": int(regime_counts.get("CAPTURE", 0)),
            "n_mixed": int(regime_counts.get("MIXED", 0)),
            "n_quiet": int(regime_counts.get("QUIET", 0)),
            "median_exit_rate": float(grp["exit_rate"].median()),
            "median_fund_prevalence": float(grp["fund_prevalence"].median()),
            "median_max_punish": float(grp["max_punish"].median()),
            "median_enforcer_share": float(grp["enforcer_share"].median()),
            "median_top5_share": float(grp["top5_share"].median()),
            "median_delta_final": float(grp["delta_final"].median()),
        })

    cell_df = pd.DataFrame(cell_rows)
    cell_df.to_csv(out_root / "cell_summary.csv", index=False)
    print(f"\ncell-level summary: {len(cell_df)} cells")

    if len(cell_df) > 0:
        print("\n--- cell-level regime distribution ---")
        print(cell_df["regime_majority"].value_counts().to_string())

    print(f"\nall results in: {out_root}")


if __name__ == "__main__":
    main()
