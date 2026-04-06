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

REGIME_ORDER = ["COLLAPSE", "CAPTURE", "MIXED", "QUIET"]


def classify_regime(exit_rate: float, prevalence: float, max_punish: float, capture_exit_cap: float) -> str:
    if exit_rate >= 0.90:
        return "COLLAPSE"
    if prevalence >= 0.90 and exit_rate <= capture_exit_cap:
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
    alpha: float,
    delta: float,
    mu: float,
    best: dict,
    base_opp: float,
    exit_threshold: float,
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
        "--alpha_punish_revalue",
        f"{alpha:.2f}",
        "--delta_outside_degrade",
        f"{delta:.2f}",
        "--mu_membership_reward",
        f"{mu:.2f}",
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


def run_grid(
    model_path: Path,
    root: Path,
    combos: list[tuple[float, float, float, float]],
    seeds: list[int],
    best: dict,
    workers: int,
    base_opp: float,
    exit_threshold: float,
    alpha_fixed: float,
):
    tasks = []
    for mu, delta, sigma, pi in combos:
        combo_dir = (
            root
            / f"mu_{mu:.2f}"
            / f"delta_{delta:.2f}"
            / f"sigma_{sigma:.2f}"
            / f"pi_{pi:.2f}"
        )
        for seed in seeds:
            run_dir = combo_dir / f"seed_{seed:02d}"
            tasks.append((run_dir, seed, sigma, pi, alpha_fixed, delta, mu))

    n_total = len(tasks)
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [
            ex.submit(
                run_one,
                model_path,
                run_dir,
                seed,
                sigma,
                pi,
                alpha,
                delta,
                mu,
                best,
                base_opp,
                exit_threshold,
            )
            for (run_dir, seed, sigma, pi, alpha, delta, mu) in tasks
        ]
        for fut in as_completed(futs):
            fut.result()
            done += 1
            if done % 20 == 0 or done == n_total:
                print(f"completed {done}/{n_total}")


def collect_seed_rows(root: Path, capture_exit_cap: float, alpha_fixed: float) -> pd.DataFrame:
    rows = []
    for mpath in sorted(root.rglob("metrics.csv")):
        run_dir = mpath.parent
        apath = run_dir / "agent_summary.csv"
        if not apath.exists():
            continue
        parts = mpath.relative_to(root).parts
        try:
            mu = float(parts[0].split("_", 1)[1])
            delta = float(parts[1].split("_", 1)[1])
            sigma = float(parts[2].split("_", 1)[1])
            pi_reward = float(parts[3].split("_", 1)[1])
            seed = int(parts[4].split("_", 1)[1])
        except Exception:
            continue

        mdf = pd.read_csv(mpath)
        adf = pd.read_csv(apath)
        if mdf.empty:
            continue

        final = mdf.iloc[-1]
        prevalence = float(final.get("fund_prevalence", np.nan))
        exit_rate = float(final.get("exit_rate", np.nan))
        max_punish = float(mdf["punish_rate"].max()) if "punish_rate" in mdf.columns else np.nan

        punish = pd.to_numeric(adf.get("punish_issued", pd.Series(dtype=float)), errors="coerce").fillna(0.0).to_numpy(dtype=float)
        top5 = top_share(punish, 0.05)
        top10 = top_share(punish, 0.10)

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

        regime = classify_regime(exit_rate, prevalence, max_punish, capture_exit_cap)
        rows.append(
            {
                "sigma": sigma,
                "pi_reward": pi_reward,
                "alpha": float(alpha_fixed),
                "delta": delta,
                "mu_membership_reward": mu,
                "seed": seed,
                "final_fund_prevalence": prevalence,
                "final_exit_rate": exit_rate,
                "max_punish": max_punish,
                "top5_punishment_share": top5,
                "top10_punishment_share": top10,
                "enforcer_punish_share": enforcer_share,
                "regime": regime,
                "run_dir": str(run_dir),
            }
        )
    return pd.DataFrame(rows)


def majority_regime(s: pd.Series) -> str:
    vc = s.value_counts()
    if vc.empty:
        return "QUIET"
    topn = vc.max()
    tied = sorted([k for k, n in vc.items() if n == topn], key=lambda x: REGIME_ORDER.index(x))
    return tied[0]


def summarize(seed_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    gcols = ["sigma", "pi_reward", "alpha", "delta", "mu_membership_reward"]
    for (sigma, pi, alpha, delta, mu), g in seed_df.groupby(gcols):
        rows.append(
            {
                "sigma": float(sigma),
                "pi_reward": float(pi),
                "alpha": float(alpha),
                "delta": float(delta),
                "mu_membership_reward": float(mu),
                "n_seeds": int(len(g)),
                "regime_majority": majority_regime(g["regime"]),
                "n_collapse": int((g["regime"] == "COLLAPSE").sum()),
                "n_capture": int((g["regime"] == "CAPTURE").sum()),
                "n_mixed": int((g["regime"] == "MIXED").sum()),
                "n_quiet": int((g["regime"] == "QUIET").sum()),
                "median_fund_prevalence": float(g["final_fund_prevalence"].median()),
                "median_exit_rate": float(g["final_exit_rate"].median()),
                "median_top5_share": float(g["top5_punishment_share"].median()),
                "median_max_punish": float(g["max_punish"].median()),
                "median_enforcer_punish_share": float(g["enforcer_punish_share"].median()),
            }
        )
    cols = [
        "sigma",
        "pi_reward",
        "alpha",
        "delta",
        "mu_membership_reward",
        "n_seeds",
        "regime_majority",
        "n_collapse",
        "n_capture",
        "n_mixed",
        "n_quiet",
        "median_fund_prevalence",
        "median_exit_rate",
        "median_top5_share",
        "median_max_punish",
        "median_enforcer_punish_share",
    ]
    return pd.DataFrame(rows)[cols].sort_values(["mu_membership_reward", "delta", "sigma", "pi_reward"])


def compute_synergy(summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    by_key = {
        (float(r.sigma), float(r.pi_reward), float(r.mu_membership_reward), float(r.delta)): r
        for _, r in summary.iterrows()
    }
    for sigma in sorted(summary["sigma"].unique()):
        for pi in sorted(summary["pi_reward"].unique()):
            base = by_key.get((float(sigma), float(pi), 0.0, 0.0))
            if base is None:
                continue
            e00 = float(base["median_exit_rate"])
            for mu in sorted([x for x in summary["mu_membership_reward"].unique() if x > 0]):
                for delta in sorted([x for x in summary["delta"].unique() if x > 0]):
                    combo = by_key.get((float(sigma), float(pi), float(mu), float(delta)))
                    mu_only = by_key.get((float(sigma), float(pi), float(mu), 0.0))
                    delta_only = by_key.get((float(sigma), float(pi), 0.0, float(delta)))
                    if combo is None or mu_only is None or delta_only is None:
                        continue
                    emd = float(combo["median_exit_rate"])
                    em0 = float(mu_only["median_exit_rate"])
                    e0d = float(delta_only["median_exit_rate"])
                    expected_additive = em0 + e0d - e00
                    interaction = expected_additive - emd
                    n = max(1, int(combo["n_seeds"]))
                    cap_combo = float(combo["n_capture"]) / n >= 0.70
                    cap_mu = float(mu_only["n_capture"]) / max(1, int(mu_only["n_seeds"])) >= 0.70
                    cap_delta = float(delta_only["n_capture"]) / max(1, int(delta_only["n_seeds"])) >= 0.70
                    rows.append(
                        {
                            "sigma": float(sigma),
                            "pi_reward": float(pi),
                            "mu_membership_reward": float(mu),
                            "delta": float(delta),
                            "exit_base": e00,
                            "exit_mu_only": em0,
                            "exit_delta_only": e0d,
                            "exit_combo": emd,
                            "expected_additive_exit": expected_additive,
                            "interaction_exit": interaction,
                            "combo_capture70": bool(cap_combo),
                            "mu_only_capture70": bool(cap_mu),
                            "delta_only_capture70": bool(cap_delta),
                            "synergy_capture70": bool(cap_combo and (not cap_mu) and (not cap_delta)),
                        }
                    )
    return pd.DataFrame(rows)


def write_report(
    root: Path,
    summary: pd.DataFrame,
    seeds_df: pd.DataFrame,
    synergy_df: pd.DataFrame,
    expected_seeds: int,
    base_opp: float,
    exit_threshold: float,
    capture_exit_cap: float,
):
    lines = []
    lines.append(f"n_cells={len(summary)}")
    lines.append(f"n_runs={len(seeds_df)}")
    lines.append(f"base_opp={base_opp}")
    lines.append(f"exit_threshold={exit_threshold}")
    lines.append(f"capture_exit_cap={capture_exit_cap}")
    lines.append(f"regime_majority_counts={summary['regime_majority'].value_counts().to_dict()}")
    lines.append(f"seed_regime_counts={seeds_df['regime'].value_counts().to_dict()}")
    if not summary.empty:
        lines.append(f"exit_rate_median_range=({summary['median_exit_rate'].min():.6f},{summary['median_exit_rate'].max():.6f})")
        lines.append(f"max_punish_median_range=({summary['median_max_punish'].min():.6f},{summary['median_max_punish'].max():.6f})")
        lines.append(
            f"enforcer_share_median_range=({summary['median_enforcer_punish_share'].min():.6f},{summary['median_enforcer_punish_share'].max():.6f})"
        )
    bad = summary[summary["n_seeds"] != expected_seeds]
    if bad.empty:
        lines.append("anomalies=none")
    else:
        lines.append(f"anomalies=cells_with_unexpected_seed_count:{len(bad)}")

    if synergy_df.empty:
        lines.append("synergy_rows=0")
    else:
        lines.append(f"synergy_rows={len(synergy_df)}")
        lines.append(f"synergy_capture70_count={int(synergy_df['synergy_capture70'].sum())}")
        lines.append(f"interaction_exit_median={float(synergy_df['interaction_exit'].median()):.6f}")
        moderate = synergy_df[
            (synergy_df["mu_membership_reward"] <= 0.30)
            & (synergy_df["delta"] <= 0.50)
        ]
        lines.append(f"moderate_synergy_capture70_count={int(moderate['synergy_capture70'].sum()) if not moderate.empty else 0}")

    (root / "sweep_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="src/religion_fundamentalism_abm_v2_6b.py")
    ap.add_argument("--best", default="runs/batch_v2_3_search_20260213_043518/summary/BEST_PARAMS.json")
    ap.add_argument("--mu-values", default="0.0,0.1,0.2,0.3,0.4")
    ap.add_argument("--delta-values", default="0.0,0.3,0.6")
    ap.add_argument("--sigma-values", default="0.75,0.95")
    ap.add_argument("--pi-values", default="0.25,0.50")
    ap.add_argument("--alpha-fixed", type=float, default=0.0)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--base-opp", type=float, default=0.3)
    ap.add_argument("--exit-threshold", type=float, default=-1.0)
    ap.add_argument("--capture-exit-cap", type=float, default=0.20)
    args = ap.parse_args()

    out_root = Path(args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    model_path = Path(args.model).resolve()
    best = load_best_params(Path(args.best))

    mus = parse_floats(args.mu_values)
    deltas = parse_floats(args.delta_values)
    sigmas = parse_floats(args.sigma_values)
    pis = parse_floats(args.pi_values)
    seeds = list(range(1, args.seeds + 1))

    combos = [(m, d, s, p) for m in mus for d in deltas for s in sigmas for p in pis]
    print(f"running combos={len(combos)} seeds={len(seeds)} total_runs={len(combos)*len(seeds)}")
    run_grid(
        model_path,
        out_root,
        combos,
        seeds,
        best,
        args.workers,
        args.base_opp,
        args.exit_threshold,
        args.alpha_fixed,
    )

    seeds_df = collect_seed_rows(out_root, args.capture_exit_cap, args.alpha_fixed)
    seeds_df.to_csv(out_root / "sweep_seed_results.csv", index=False)
    summary = summarize(seeds_df)
    summary.to_csv(out_root / "sweep_summary.csv", index=False)
    synergy = compute_synergy(summary)
    synergy.to_csv(out_root / "synergy_summary.csv", index=False)
    write_report(
        out_root,
        summary,
        seeds_df,
        synergy,
        expected_seeds=len(seeds),
        base_opp=args.base_opp,
        exit_threshold=args.exit_threshold,
        capture_exit_cap=args.capture_exit_cap,
    )
    print(f"Wrote {out_root / 'sweep_summary.csv'}")
    print(f"Wrote {out_root / 'sweep_seed_results.csv'}")
    print(f"Wrote {out_root / 'synergy_summary.csv'}")
    print(f"Wrote {out_root / 'sweep_report.txt'}")


if __name__ == "__main__":
    main()
