#!/usr/bin/env python3
import argparse
import json
import math
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

LEGACY_ORDER = ["COLLAPSE", "CAPTURE", "MIXED", "QUIET"]
HIER_ORDER = ["COLLAPSE", "CAPTURE_HIERARCHICAL", "MIXED", "QUIET"]


def classify_legacy(exit_rate: float, prevalence_active: float, max_punish: float) -> str:
    if exit_rate >= 0.90:
        return "COLLAPSE"
    if prevalence_active >= 0.90 and exit_rate <= 0.20:
        return "CAPTURE"
    if max_punish >= 0.10:
        return "MIXED"
    return "QUIET"


def classify_hier(
    exit_rate: float,
    max_punish: float,
    enforcer_punish_share: float,
    capture_exit_cap: float,
) -> str:
    if exit_rate >= 0.90:
        return "COLLAPSE"
    if exit_rate <= capture_exit_cap and max_punish >= 0.10 and enforcer_punish_share >= 0.70:
        return "CAPTURE_HIERARCHICAL"
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


def run_one(
    model_path: Path,
    run_dir: Path,
    seed: int,
    sigma: float,
    pi_reward: float,
    base_opp: float,
    exit_threshold: float,
    best: dict,
):
    metrics_path = run_dir / "metrics.csv"
    agent_path = run_dir / "agent_summary.csv"
    if metrics_path.exists() and agent_path.exists():
        return

    run_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(model_path),
        "--outdir",
        str(run_dir),
        "--steps",
        "450",
        "--n",
        "350",
        "--graph",
        "scale_free",
        "--seed",
        str(seed),
        "--sigma",
        f"{sigma:.2f}",
        "--pi_reward",
        f"{pi_reward:.2f}",
        "--exit_opportunity_base",
        f"{base_opp:.2f}",
        "--exit_threshold",
        f"{exit_threshold:.2f}",
        "--shock_schedule",
        "100,220,320",
        "--shock_strength",
        str(best["shock_strength"]),
        "--membership_benefit",
        str(best["membership_benefit"]),
        "--membership_benefit_threat",
        str(best["membership_benefit_threat"]),
        "--exit_opportunity_threat_coeff",
        str(best["exit_opportunity_threat_coeff"]),
        "--exit_block_exponent",
        str(best["exit_block_exponent"]),
        "--exit_commit_steps",
        str(best["exit_commit_steps"]),
        "--exit_cost",
        str(best["exit_cost"]),
        "--enforcer_quota_frac",
        "0.08",
        "--A_gain_threat",
        "2.0",
        "--A_enforcer_monopoly",
        "0.35",
        "--budget_base",
        "0.15",
        "--budget_threat_gain",
        "0.60",
        "--cap_decay",
        "0.005",
        "--cap_gain_per_punish",
        "0.15",
        "--cap_to_enforcer",
        "0.25",
        "--cap_max",
        "2.0",
        "--service_decay",
        "0.02",
        "--non_enforcer_punish_mult",
        "0.25",
        "--non_enforcer_punish_eps",
        "0.02",
        "--enforcer_punish_mult",
        "1.5",
        "--kappa_cap_discount",
        "0.20",
        "--enforcer_backlash_mult",
        "0.25",
        "--enforcer_kappa_mult",
        "0.30",
        "--no_movie",
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run_grid(model_path: Path, root: Path, combos: list, seeds: list, best: dict, workers: int):
    tasks = []
    for sigma, pi, opp, ex_th in combos:
        combo_dir = (
            root
            / f"sigma_{sigma:.2f}"
            / f"pi_{pi:.2f}"
            / f"base_opp_{opp:.2f}"
            / f"exit_threshold_{ex_th:.2f}"
        )
        for seed in seeds:
            run_dir = combo_dir / f"seed_{seed:02d}"
            tasks.append((run_dir, seed, sigma, pi, opp, ex_th))

    n_total = len(tasks)
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [
            ex.submit(run_one, model_path, run_dir, seed, sigma, pi, opp, ex_th, best)
            for (run_dir, seed, sigma, pi, opp, ex_th) in tasks
        ]
        for fut in as_completed(futs):
            fut.result()
            done += 1
            if done % 20 == 0 or done == n_total:
                print(f"completed {done}/{n_total}")


def collect_seed_rows(root: Path):
    rows = []
    for mpath in sorted(root.rglob("metrics.csv")):
        seed_dir = mpath.parent
        agent_path = seed_dir / "agent_summary.csv"
        if not agent_path.exists():
            continue
        parts = mpath.relative_to(root).parts
        try:
            sigma = float(parts[0].split("_", 1)[1])
            pi = float(parts[1].split("_", 1)[1])
            opp = float(parts[2].split("_", 2)[2])
            ex_th = float(parts[3].split("_", 2)[2])
            seed = int(parts[4].split("_", 1)[1])
        except Exception:
            continue

        mdf = pd.read_csv(mpath)
        adf = pd.read_csv(agent_path)
        if mdf.empty:
            continue
        final = mdf.iloc[-1]
        prev = float(final.get("fund_prevalence", np.nan))
        exit_rate = float(final.get("exit_rate", np.nan))
        max_punish = float(mdf["punish_rate"].max()) if "punish_rate" in mdf.columns else np.nan

        punish = pd.to_numeric(
            adf.get("punish_issued", pd.Series(dtype=float)), errors="coerce"
        ).fillna(0.0).to_numpy(dtype=float)
        top5 = top_share(punish, 0.05)
        top10 = top_share(punish, 0.10)

        eps = 1e-9
        step_share = pd.to_numeric(
            mdf.get("enforcer_punish_share_step", pd.Series(dtype=float)), errors="coerce"
        ).replace([np.inf, -np.inf], np.nan)
        punish_rate = pd.to_numeric(mdf.get("punish_rate", pd.Series(dtype=float)), errors="coerce")
        mask = punish_rate > 0
        if mask.any():
            enforcer_punish_share = float(step_share[mask].fillna(0.0).mean())
        else:
            enforcer_punish_share = 0.0
        enforcer_punish_share = float(max(0.0, min(1.0, enforcer_punish_share + eps)))

        regime_legacy = classify_legacy(exit_rate, prev, max_punish)
        capture_exit_cap = float(getattr(collect_seed_rows, "capture_exit_cap", 0.20))
        regime_hier = classify_hier(exit_rate, max_punish, enforcer_punish_share, capture_exit_cap)

        rows.append(
            {
                "sigma": sigma,
                "pi_reward": pi,
                "base_opp": opp,
                "exit_threshold": ex_th,
                "seed": seed,
                "final_fund_prevalence": prev,
                "final_exit_rate": exit_rate,
                "max_punish": max_punish,
                "enforcer_punish_share": enforcer_punish_share,
                "top5_punishment_share": top5,
                "top10_punishment_share": top10,
                "regime_legacy": regime_legacy,
                "regime_hier": regime_hier,
                "run_dir": str(seed_dir),
            }
        )
    return pd.DataFrame(rows)


def majority_regime(group: pd.Series, order: list) -> str:
    vc = group.value_counts()
    if vc.empty:
        return "QUIET"
    topn = vc.max()
    tied = sorted([r for r, n in vc.items() if n == topn], key=lambda r: order.index(r))
    return tied[0]


def summarize(seed_df: pd.DataFrame) -> pd.DataFrame:
    gcols = ["sigma", "pi_reward", "base_opp", "exit_threshold"]
    rows = []
    for key, g in seed_df.groupby(gcols, as_index=False):
        sigma, pi, opp, ex_th = key
        rows.append(
            {
                "sigma": sigma,
                "pi_reward": pi,
                "base_opp": opp,
                "exit_threshold": ex_th,
                "n_seeds": int(len(g)),
                "regime_majority_legacy": majority_regime(g["regime_legacy"], LEGACY_ORDER),
                "regime_majority_hier": majority_regime(g["regime_hier"], HIER_ORDER),
                "n_collapse_legacy": int((g["regime_legacy"] == "COLLAPSE").sum()),
                "n_capture_legacy": int((g["regime_legacy"] == "CAPTURE").sum()),
                "n_mixed_legacy": int((g["regime_legacy"] == "MIXED").sum()),
                "n_quiet_legacy": int((g["regime_legacy"] == "QUIET").sum()),
                "n_collapse_hier": int((g["regime_hier"] == "COLLAPSE").sum()),
                "n_capture_hier": int((g["regime_hier"] == "CAPTURE_HIERARCHICAL").sum()),
                "n_mixed_hier": int((g["regime_hier"] == "MIXED").sum()),
                "n_quiet_hier": int((g["regime_hier"] == "QUIET").sum()),
                "median_fund_prevalence": float(g["final_fund_prevalence"].median()),
                "median_exit_rate": float(g["final_exit_rate"].median()),
                "median_top5_share": float(g["top5_punishment_share"].median()),
                "median_max_punish": float(g["max_punish"].median()),
                "median_enforcer_punish_share": float(g["enforcer_punish_share"].median()),
            }
        )
    return pd.DataFrame(rows).sort_values(gcols)


def write_representative_timeseries(seed_df: pd.DataFrame, out_root: Path, regime_col: str, regimes: list):
    for regime in regimes:
        sub = seed_df[seed_df[regime_col] == regime].copy()
        if sub.empty:
            continue
        if regime == "COLLAPSE":
            metric = "final_exit_rate"
        elif regime in {"CAPTURE", "CAPTURE_HIERARCHICAL"}:
            metric = "max_punish"
        else:
            metric = "max_punish"
        med = float(sub[metric].median())
        sub["dist"] = (sub[metric] - med).abs()
        chosen = sub.sort_values(["dist", "seed"]).iloc[0]
        run_dir = Path(chosen["run_dir"])
        mdf = pd.read_csv(run_dir / "metrics.csv")
        ts = pd.DataFrame(
            {
                "t": mdf["t"],
                "fund_prevalence": mdf.get("fund_prevalence", np.nan),
                "exit_rate": mdf.get("exit_rate", np.nan),
                "punish_rate": mdf.get("punish_rate", np.nan),
                "enforcer_punish_share_step": mdf.get("enforcer_punish_share_step", np.nan),
                "sigma": chosen["sigma"],
                "pi_reward": chosen["pi_reward"],
                "base_opp": chosen["base_opp"],
                "exit_threshold": chosen["exit_threshold"],
                "seed": int(chosen["seed"]),
                "regime": regime,
                "regime_column": regime_col,
            }
        )
        name = f"timeseries_{regime_col}_{regime}.csv"
        ts.to_csv(out_root / name, index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/v2.5_corrected_sweep_regime_search")
    ap.add_argument(
        "--best",
        default="runs/batch_v2_3_search_20260213_043518/summary/BEST_PARAMS.json",
    )
    ap.add_argument("--model", default="src/religion_fundamentalism_abm_v2_5.py")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--capture-exit-cap", type=float, default=0.20)
    ap.add_argument("--sigma-values", default="0.25,0.50,0.75,0.95")
    ap.add_argument("--pi-values", default="0.05,0.10,0.25,0.50")
    ap.add_argument("--base-opp-values", default="0.3,0.7,1.5,3.0,5.0")
    ap.add_argument("--exit-threshold-values", default="-1.0,0.5,1.0,1.5")
    args = ap.parse_args()
    collect_seed_rows.capture_exit_cap = float(args.capture_exit_cap)

    out_root = Path(args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    best = load_best_params(Path(args.best))
    model_path = Path(args.model).resolve()

    sigma_vals = [float(x.strip()) for x in args.sigma_values.split(",") if x.strip()]
    pi_vals = [float(x.strip()) for x in args.pi_values.split(",") if x.strip()]
    opp_vals = [float(x.strip()) for x in args.base_opp_values.split(",") if x.strip()]
    exit_threshold_vals = [float(x.strip()) for x in args.exit_threshold_values.split(",") if x.strip()]
    seeds = list(range(1, args.seeds + 1))

    combos = [(s, p, o, e) for s in sigma_vals for p in pi_vals for o in opp_vals for e in exit_threshold_vals]
    print(f"running combos={len(combos)} seeds={len(seeds)} total_runs={len(combos) * len(seeds)}")
    run_grid(model_path, out_root, combos, seeds, best, args.workers)

    seed_df = collect_seed_rows(out_root)
    seed_df.to_csv(out_root / "sweep_seed_results.csv", index=False)
    summary = summarize(seed_df)
    summary.to_csv(out_root / "sweep_summary.csv", index=False)

    write_representative_timeseries(seed_df, out_root, "regime_legacy", LEGACY_ORDER)
    write_representative_timeseries(seed_df, out_root, "regime_hier", HIER_ORDER)

    legacy_found = sorted(seed_df["regime_legacy"].dropna().unique()) if not seed_df.empty else []
    hier_found = sorted(seed_df["regime_hier"].dropna().unique()) if not seed_df.empty else []
    with open(out_root / "sweep_report.txt", "w", encoding="utf-8") as f:
        f.write(f"n_runs={len(seed_df)}\n")
        f.write(f"legacy_regimes_found={legacy_found}\n")
        f.write(f"hier_regimes_found={hier_found}\n")
        f.write(f"capture_exit_cap={collect_seed_rows.capture_exit_cap}\n")
        f.write(f"seeds_per_combo={len(seeds)}\n")

    print(f"Wrote {out_root / 'sweep_summary.csv'}")
    print(f"Wrote {out_root / 'sweep_seed_results.csv'}")
    print(f"Legacy regimes found: {legacy_found}")
    print(f"Hierarchical regimes found: {hier_found}")


if __name__ == "__main__":
    main()
