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


def classify_regime(exit_rate: float, prevalence: float, max_punish: float, capture_exit_cap: float = 0.20) -> str:
    if exit_rate >= 0.90:
        return "COLLAPSE"
    if prevalence >= 0.90 and exit_rate <= capture_exit_cap:
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


def run_one(
    model_path: Path,
    outdir: Path,
    seed: int,
    sigma: float,
    pi_reward: float,
    delta0: float,
    eta: float,
    punish_floor: float,
    best: dict,
):
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
        f"{sigma:.2f}",
        "--pi_reward",
        f"{pi_reward:.2f}",
        "--alpha_punish_revalue",
        "0.0",
        "--mu_membership_reward",
        "0.0",
        "--delta_outside_degrade",
        f"{delta0:.2f}",
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
    if "v2_7" in model_path.name:
        cmd += [
            "--eta_delta_drift",
            f"{eta:.2f}",
            "--punish_floor",
            f"{punish_floor:.2f}",
        ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def summarize_run(seed_dir: Path):
    mdf = pd.read_csv(seed_dir / "metrics.csv")
    adf = pd.read_csv(seed_dir / "agent_summary.csv")

    final = mdf.iloc[-1]
    final_exit = float(final["exit_rate"])
    final_prev = float(final.get("fund_prevalence", np.nan))
    max_punish = float(mdf["punish_rate"].max()) if "punish_rate" in mdf.columns else np.nan
    final_delta = float(final.get("current_delta", final.get("delta_outside_degrade", np.nan)))
    regime = classify_regime(final_exit, final_prev, max_punish)

    punish = pd.to_numeric(adf["punish_issued"], errors="coerce").fillna(0.0).to_numpy(dtype=float)
    top5 = top_share(punish, 0.05)
    share_step = pd.to_numeric(mdf.get("enforcer_punish_share_step", pd.Series(dtype=float)), errors="coerce").replace([np.inf, -np.inf], np.nan)
    pr = pd.to_numeric(mdf.get("punish_rate", pd.Series(dtype=float)), errors="coerce")
    active_steps = pr > 0
    if active_steps.any():
        enf_share = float(share_step[active_steps].fillna(0.0).mean())
    else:
        enf_share = 0.0

    return {
        "final_exit_rate": final_exit,
        "final_current_delta": final_delta,
        "top5_share": top5,
        "enforcer_share": enf_share,
        "final_regime": regime,
    }


def main():
    repo = Path(__file__).resolve().parents[1]
    out_root = repo / "results" / "v2.7_validation"
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    best = load_best_params(repo / "runs" / "batch_v2_3_search_20260213_043518" / "summary" / "BEST_PARAMS.json")
    v26b = repo / "src" / "religion_fundamentalism_abm_v2_6b.py"
    v27 = repo / "src" / "religion_fundamentalism_abm_v2_7.py"

    # Check 1: eta=0 recovers v2.6b when delta0 held fixed.
    c1_v26b = out_root / "check1_v26b_seed11"
    c1_v27 = out_root / "check1_v27_seed11"
    run_one(v26b, c1_v26b, seed=11, sigma=0.95, pi_reward=0.50, delta0=0.20, eta=0.0, punish_floor=0.08, best=best)
    run_one(v27, c1_v27, seed=11, sigma=0.95, pi_reward=0.50, delta0=0.20, eta=0.0, punish_floor=0.08, best=best)
    m26b = pd.read_csv(c1_v26b / "metrics.csv")
    m27 = pd.read_csv(c1_v27 / "metrics.csv")
    shared_cols = [c for c in m26b.columns if c in m27.columns]
    check1_metrics_equal = m26b[shared_cols].equals(m27[shared_cols])
    a26b = pd.read_csv(c1_v26b / "agent_summary.csv")
    a27 = pd.read_csv(c1_v27 / "agent_summary.csv")
    shared_agent_cols = [c for c in a26b.columns if c in a27.columns]
    check1_agents_equal = a26b[shared_agent_cols].equals(a27[shared_agent_cols])
    check1_pass = bool(check1_metrics_equal and check1_agents_equal)

    seeds = [1, 2, 3, 4, 5]

    # Check 2: sigma=0.25, pi=0.05 with eta>0 should not produce capture.
    rows2 = []
    for seed in seeds:
        out = out_root / f"check2_sigma025_seed_{seed:02d}"
        run_one(v27, out, seed=seed, sigma=0.25, pi_reward=0.05, delta0=0.20, eta=0.05, punish_floor=0.08, best=best)
        s = summarize_run(out)
        s.update({"check": "check2", "seed": seed})
        rows2.append(s)
    df2 = pd.DataFrame(rows2)
    check2_capture_count = int((df2["final_regime"] == "CAPTURE").sum())
    check2_pass = bool(check2_capture_count == 0)

    # Check 3: sigma=0.95, pi=0.50 with eta>0 should still produce capture.
    rows3 = []
    for seed in seeds:
        out = out_root / f"check3_sigma095_seed_{seed:02d}"
        run_one(v27, out, seed=seed, sigma=0.95, pi_reward=0.50, delta0=0.20, eta=0.05, punish_floor=0.08, best=best)
        s = summarize_run(out)
        s.update({"check": "check3", "seed": seed})
        rows3.append(s)
    df3 = pd.DataFrame(rows3)
    check3_capture_count = int((df3["final_regime"] == "CAPTURE").sum())
    check3_delta_median = float(df3["final_current_delta"].median())
    check3_pass = bool(check3_capture_count >= 1 and check3_delta_median > 0.2)

    by = pd.concat([df2, df3], ignore_index=True)
    (out_root / "validation_by_seed.csv").write_text(by.to_csv(index=False), encoding="utf-8")

    out = {
        "check1": {
            "shared_metrics_equal": check1_metrics_equal,
            "agent_summary_equal_on_shared_cols": check1_agents_equal,
            "pass": check1_pass,
        },
        "check2": {
            "scenario": "sigma=0.25, pi=0.05, eta=0.05, delta0=0.2",
            "capture_count": check2_capture_count,
            "pass": check2_pass,
        },
        "check3": {
            "scenario": "sigma=0.95, pi=0.50, eta=0.05, delta0=0.2",
            "capture_count": check3_capture_count,
            "median_final_delta": check3_delta_median,
            "pass": check3_pass,
        },
        "all_pass": bool(check1_pass and check2_pass and check3_pass),
    }

    (out_root / "validation_report.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    lines = [
        "# v2.7 Validation (Gated Drift)",
        f"check1_pass={check1_pass}",
        f"check2_pass={check2_pass}",
        f"check3_pass={check3_pass}",
        f"all_pass={out['all_pass']}",
        "",
        f"check2_capture_count={check2_capture_count}",
        f"check3_capture_count={check3_capture_count}",
        f"check3_median_final_delta={check3_delta_median:.6f}",
    ]
    (out_root / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_root / 'validation_report.json'}")
    print(f"Wrote {out_root / 'validation_report.md'}")
    print(f"all_pass={out['all_pass']}")
    if not out["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
