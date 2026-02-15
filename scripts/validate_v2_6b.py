#!/usr/bin/env python3
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


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


def run_one(model_path: Path, outdir: Path, seed: int, alpha: float, delta: float, mu: float, best: dict):
    cmd = [
        sys.executable,
        str(model_path),
        "--outdir",
        str(outdir),
        "--steps",
        "450",
        "--n",
        "350",
        "--graph",
        "scale_free",
        "--seed",
        str(seed),
        "--sigma",
        "0.95",
        "--pi_reward",
        "0.50",
        "--exit_opportunity_base",
        "0.30",
        "--exit_threshold",
        "-1.0",
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
    if "v2_6b" in model_path.name:
        cmd += [
            "--alpha_punish_revalue",
            f"{alpha:.2f}",
            "--delta_outside_degrade",
            f"{delta:.2f}",
            "--mu_membership_reward",
            f"{mu:.2f}",
        ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def summarize_run(seed_dir: Path):
    mdf = pd.read_csv(seed_dir / "metrics.csv")
    adf = pd.read_csv(seed_dir / "agent_summary.csv")
    final_exit = float(mdf["exit_rate"].iloc[-1])
    punish = pd.to_numeric(adf["punish_issued"], errors="coerce").fillna(0.0).to_numpy(dtype=float)
    top5 = top_share(punish, 0.05)
    share_step = pd.to_numeric(mdf.get("enforcer_punish_share_step", pd.Series(dtype=float)), errors="coerce").replace([np.inf, -np.inf], np.nan)
    pr = pd.to_numeric(mdf.get("punish_rate", pd.Series(dtype=float)), errors="coerce")
    active_steps = pr > 0
    if active_steps.any():
        enf_share = float(share_step[active_steps].fillna(0.0).mean())
    else:
        enf_share = 0.0
    return {"final_exit_rate": final_exit, "top5_share": top5, "enforcer_share": enf_share}


def main():
    repo = Path(__file__).resolve().parents[1]
    out_root = repo / "results" / "v2.6b_validation"
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    best = load_best_params(repo / "runs" / "batch_v2_3_search_20260213_043518" / "summary" / "BEST_PARAMS.json")
    v25 = repo / "src" / "religion_fundamentalism_abm_v2_5.py"
    v26b = repo / "src" / "religion_fundamentalism_abm_v2_6b.py"

    # Check 1: exact recovery vs v2.5 with alpha=delta=mu=0.
    c1_v25 = out_root / "check1_v25_seed11"
    c1_v26b = out_root / "check1_v26b_seed11"
    run_one(v25, c1_v25, seed=11, alpha=0.0, delta=0.0, mu=0.0, best=best)
    run_one(v26b, c1_v26b, seed=11, alpha=0.0, delta=0.0, mu=0.0, best=best)
    m25 = pd.read_csv(c1_v25 / "metrics.csv")
    m26b = pd.read_csv(c1_v26b / "metrics.csv")
    shared_cols = [c for c in m25.columns if c in m26b.columns]
    check1_metrics_equal = m25[shared_cols].equals(m26b[shared_cols])
    a25 = pd.read_csv(c1_v25 / "agent_summary.csv")
    a26b = pd.read_csv(c1_v26b / "agent_summary.csv")
    shared_agent_cols = [c for c in a25.columns if c in a26b.columns]
    check1_agents_equal = a25[shared_agent_cols].equals(a26b[shared_agent_cols])
    check1_pass = bool(check1_metrics_equal and check1_agents_equal)

    # Check 2: mu>0 lowers exit while concentration metrics stay approximately stable.
    seeds = [1, 2, 3, 4, 5]
    rows = []
    conds = [
        ("baseline", 0.0, 0.0, 0.0),
        ("mu_only", 0.0, 0.0, 0.5),
    ]
    for label, alpha, delta, mu in conds:
        for seed in seeds:
            out = out_root / f"{label}_seed_{seed:02d}"
            run_one(v26b, out, seed=seed, alpha=alpha, delta=delta, mu=mu, best=best)
            s = summarize_run(out)
            s.update({"condition": label, "seed": seed, "alpha": alpha, "delta": delta, "mu": mu})
            rows.append(s)
    df = pd.DataFrame(rows)
    by = (
        df.groupby("condition", as_index=False)
        .agg(
            median_exit_rate=("final_exit_rate", "median"),
            median_top5_share=("top5_share", "median"),
            median_enforcer_punish_share=("enforcer_share", "median"),
        )
        .sort_values("condition")
    )

    base = by.set_index("condition").loc["baseline"]
    mu_only = by.set_index("condition").loc["mu_only"]

    share_tol = 0.05
    check2_exit_lower = bool(mu_only["median_exit_rate"] < base["median_exit_rate"])
    check2_shares_stable = bool(
        abs(mu_only["median_top5_share"] - base["median_top5_share"]) <= share_tol
        and abs(mu_only["median_enforcer_punish_share"] - base["median_enforcer_punish_share"]) <= share_tol
    )
    check2_pass = bool(check2_exit_lower and check2_shares_stable)

    out = {
        "check1": {
            "shared_metrics_equal": check1_metrics_equal,
            "agent_summary_equal_on_shared_cols": check1_agents_equal,
            "pass": check1_pass,
        },
        "check2": {
            "baseline": {
                "median_exit_rate": float(base["median_exit_rate"]),
                "median_top5_share": float(base["median_top5_share"]),
                "median_enforcer_punish_share": float(base["median_enforcer_punish_share"]),
            },
            "mu_only": {
                "median_exit_rate": float(mu_only["median_exit_rate"]),
                "median_top5_share": float(mu_only["median_top5_share"]),
                "median_enforcer_punish_share": float(mu_only["median_enforcer_punish_share"]),
            },
            "exit_lower": check2_exit_lower,
            "shares_stable": check2_shares_stable,
            "pass": check2_pass,
        },
        "all_pass": bool(check1_pass and check2_pass),
    }

    (out_root / "validation_by_seed.csv").write_text(df.to_csv(index=False), encoding="utf-8")
    (out_root / "validation_summary.csv").write_text(by.to_csv(index=False), encoding="utf-8")
    (out_root / "validation_report.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    lines = [
        "# v2.6b Validation",
        f"check1_pass={check1_pass}",
        f"check2_pass={check2_pass}",
        f"all_pass={out['all_pass']}",
        "",
        "summary:",
        by.to_string(index=False),
    ]
    (out_root / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_root / 'validation_report.json'}")
    print(f"Wrote {out_root / 'validation_report.md'}")
    print(f"all_pass={out['all_pass']}")
    if not out["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
