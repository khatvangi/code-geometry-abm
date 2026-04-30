#!/usr/bin/env python3
"""build_methodology_paper_canonical.py

builds results/v2.5_methodology_paper_canonical/ deterministically from the
immutable v2.5 confirmatory sweep run dirs at
results/v2.5_corrected_three_regime_confirm/.

hard-coded canonical parameters (no CLI flags so they cannot drift):
- capture_exit_cap = 0.20
  source of authority: manuscript/manuscript.tex section 6.10 stated rule
- active-rate correction applied
  active_punish_rate_t = punish_rate_t / max(1 - exit_rate_t, eps)
  source of authority: HISTORY.md cap-divergence diagnosis 2026-04-28

run from repo root: python scripts/build_methodology_paper_canonical.py

writes:
  results/v2.5_methodology_paper_canonical/
    sweep_seed_results.csv       360 rows: per-seed classifier inputs and labels
    sweep_summary.csv             72 rows: per-cell aggregates
    phase_bundle/                 produced by scripts/build_v2_5_phase_bundle.py
    timeseries_regime_hier_*.csv  per-regime per-seed-per-step rows for figure 4
    sigma_*/pi_*/base_opp_*/exit_threshold_*/seed_*/  relative symlinks to the
                                                       frozen source run dirs
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "results" / "v2.5_corrected_three_regime_confirm"
CANONICAL = REPO_ROOT / "results" / "v2.5_methodology_paper_canonical"

CAPTURE_EXIT_CAP = 0.20  # manuscript section 6.10
EPS = 1e-9
EXPECTED_HIER = {"CAPTURE_HIERARCHICAL": 0, "MIXED": 55, "QUIET": 8, "COLLAPSE": 9}

REGIMES_HIER = ["QUIET", "MIXED", "COLLAPSE", "CAPTURE_HIERARCHICAL"]
REGIMES_LEGACY = ["QUIET", "MIXED", "COLLAPSE", "CAPTURE"]
SEVERITY_HIER = ["COLLAPSE", "CAPTURE_HIERARCHICAL", "MIXED", "QUIET"]
SEVERITY_LEGACY = ["COLLAPSE", "CAPTURE", "MIXED", "QUIET"]
CELL_KEYS = ["sigma", "pi_reward", "base_opp", "exit_threshold"]


def classifyHier(exit_rate: float, max_active_punish: float, enforcer_share: float) -> str:
    if exit_rate >= 0.90:
        return "COLLAPSE"
    if (
        exit_rate <= CAPTURE_EXIT_CAP
        and max_active_punish >= 0.10
        and enforcer_share >= 0.70
    ):
        return "CAPTURE_HIERARCHICAL"
    if max_active_punish >= 0.10:
        return "MIXED"
    return "QUIET"


def classifyLegacy(exit_rate: float, prevalence: float, max_active_punish: float) -> str:
    if exit_rate >= 0.90:
        return "COLLAPSE"
    if prevalence >= 0.90 and exit_rate <= CAPTURE_EXIT_CAP:
        return "CAPTURE"
    if max_active_punish >= 0.10:
        return "MIXED"
    return "QUIET"


def topShare(values: np.ndarray, frac: float) -> float:
    x = np.asarray(values, dtype=float)
    total = float(np.sum(x))
    if x.size == 0 or total <= 0:
        return 0.0
    k = max(1, int(np.ceil(frac * x.size)))
    return float(np.sum(np.sort(x)[::-1][:k]) / total)


def parseSeedPath(rel_parts: tuple) -> tuple:
    """parse (sigma, pi_reward, base_opp, exit_threshold, seed) from path parts."""
    sigma = float(rel_parts[0].split("_", 1)[1])
    pi = float(rel_parts[1].split("_", 1)[1])
    opp = float(rel_parts[2].split("_", 2)[2])
    ex_th = float(rel_parts[3].split("_", 2)[2])
    seed = int(rel_parts[4].split("_", 1)[1])
    return sigma, pi, opp, ex_th, seed


def computeRunRow(seed_dir: Path) -> dict:
    """read metrics.csv + agent_summary.csv from a seed dir; return classifier inputs and labels."""
    mdf = pd.read_csv(seed_dir / "metrics.csv")
    adf = pd.read_csv(seed_dir / "agent_summary.csv")

    final = mdf.iloc[-1]
    final_prev = float(final["fund_prevalence"])
    final_exit = float(final["exit_rate"])
    final_pr = float(final["punish_rate"])
    final_active_pr = (
        final_pr / max(1.0 - final_exit, EPS) if (1.0 - final_exit) > EPS else 0.0
    )

    pr_series = pd.to_numeric(mdf["punish_rate"], errors="coerce").fillna(0.0)
    er_series = pd.to_numeric(mdf["exit_rate"], errors="coerce").fillna(0.0)
    active_frac = 1.0 - er_series
    active_pr_series = np.where(active_frac > EPS, pr_series / active_frac, 0.0)
    max_punish = float(pr_series.max())
    max_active_punish = float(np.max(active_pr_series))

    step_share = pd.to_numeric(
        mdf.get("enforcer_punish_share_step", pd.Series(dtype=float)),
        errors="coerce",
    ).replace([np.inf, -np.inf], np.nan)
    mask = pr_series > 0
    if mask.any() and not step_share.isna().all():
        enforcer_share = float(
            max(0.0, min(1.0, float(step_share[mask].fillna(0.0).mean()) + EPS))
        )
    else:
        enforcer_share = EPS

    punish_col = (
        pd.to_numeric(adf.get("punish_issued", pd.Series(dtype=float)), errors="coerce")
        .fillna(0.0)
        .to_numpy(dtype=float)
    )
    top5 = topShare(punish_col, 0.05)
    top10 = topShare(punish_col, 0.10)

    regime_legacy = classifyLegacy(final_exit, final_prev, max_active_punish)
    regime_hier = classifyHier(final_exit, max_active_punish, enforcer_share)

    return {
        "final_fund_prevalence": final_prev,
        "final_exit_rate": final_exit,
        "punish_rate": final_pr,
        "active_punish_rate": final_active_pr,
        "max_punish": max_punish,
        "max_active_punish": max_active_punish,
        "enforcer_punish_share": enforcer_share,
        "top5_punishment_share": top5,
        "top10_punishment_share": top10,
        "regime_legacy": regime_legacy,
        "regime_hier": regime_hier,
    }


def majorityRegime(labels: pd.Series, severity_order: list) -> str:
    """mode with severity-weighted tiebreak; severity_order lists most-severe first."""
    vc = labels.value_counts()
    if vc.empty:
        return "QUIET"
    topn = vc.max()
    tied = [r for r, n in vc.items() if n == topn]
    for r in severity_order:
        if r in tied:
            return r
    return tied[0]


def buildSeedAndSummary(seed_dirs: list) -> tuple:
    """walk every frozen seed dir, classify, also collect timeseries frames."""
    rows = []
    timeseries_frames = []

    for seed_dir in seed_dirs:
        rel = seed_dir.relative_to(SOURCE)
        sigma, pi, opp, ex_th, seed = parseSeedPath(rel.parts)

        # symlink the canonical seed dir at the matching relative path under CANONICAL
        canonical_seed = CANONICAL / rel
        canonical_seed.parent.mkdir(parents=True, exist_ok=True)
        target_rel = os.path.relpath(
            seed_dir.resolve(), start=canonical_seed.parent.resolve()
        )
        canonical_seed.symlink_to(target_rel)

        run_data = computeRunRow(seed_dir)
        rows.append(
            {
                "sigma": sigma,
                "pi_reward": pi,
                "base_opp": opp,
                "exit_threshold": ex_th,
                "seed": seed,
                **run_data,
                "run_dir": str(canonical_seed.relative_to(REPO_ROOT)),
            }
        )

        # collect per-step timeseries tagged with regime; figure 4 averages across seeds
        mdf = pd.read_csv(seed_dir / "metrics.csv")
        active_pr = np.where(
            (1 - mdf["exit_rate"]) > EPS,
            mdf["punish_rate"] / (1 - mdf["exit_rate"]),
            0.0,
        )
        ts = pd.DataFrame(
            {
                "t": mdf["t"],
                "fund_prevalence": mdf["fund_prevalence"],
                "exit_rate": mdf["exit_rate"],
                "punish_rate": mdf["punish_rate"],
                "active_punish_rate": active_pr,
                "enforcer_punish_share_step": mdf.get(
                    "enforcer_punish_share_step", pd.Series([np.nan] * len(mdf))
                ),
                "sigma": sigma,
                "pi_reward": pi,
                "base_opp": opp,
                "exit_threshold": ex_th,
                "seed": seed,
                "regime_hier": run_data["regime_hier"],
                "regime_legacy": run_data["regime_legacy"],
            }
        )
        timeseries_frames.append(ts)

    seed_df = pd.DataFrame(rows).sort_values(CELL_KEYS + ["seed"]).reset_index(drop=True)

    # cell-level aggregation
    summary_rows = []
    for keys, group in seed_df.groupby(CELL_KEYS):
        sigma, pi, opp, ex_th = keys
        summary_rows.append(
            {
                "sigma": sigma,
                "pi_reward": pi,
                "base_opp": opp,
                "exit_threshold": ex_th,
                "n_seeds": len(group),
                "regime_majority_legacy": majorityRegime(
                    group["regime_legacy"], SEVERITY_LEGACY
                ),
                "regime_majority_hier": majorityRegime(
                    group["regime_hier"], SEVERITY_HIER
                ),
                "n_collapse_legacy": int((group["regime_legacy"] == "COLLAPSE").sum()),
                "n_capture_legacy": int((group["regime_legacy"] == "CAPTURE").sum()),
                "n_mixed_legacy": int((group["regime_legacy"] == "MIXED").sum()),
                "n_quiet_legacy": int((group["regime_legacy"] == "QUIET").sum()),
                "n_collapse_hier": int((group["regime_hier"] == "COLLAPSE").sum()),
                "n_capture_hier": int(
                    (group["regime_hier"] == "CAPTURE_HIERARCHICAL").sum()
                ),
                "n_mixed_hier": int((group["regime_hier"] == "MIXED").sum()),
                "n_quiet_hier": int((group["regime_hier"] == "QUIET").sum()),
                "median_fund_prevalence": float(group["final_fund_prevalence"].median()),
                "median_exit_rate": float(group["final_exit_rate"].median()),
                # canonical median punish: active-rate version, since active-rate is the canonical input
                "median_max_punish": float(group["max_active_punish"].median()),
                "median_enforcer_punish_share": float(group["enforcer_punish_share"].median()),
                "median_top5_share": float(group["top5_punishment_share"].median()),
            }
        )
    summary_df = pd.DataFrame(summary_rows).sort_values(CELL_KEYS).reset_index(drop=True)

    timeseries_df = pd.concat(timeseries_frames, ignore_index=True)
    return seed_df, summary_df, timeseries_df


def main():
    if not SOURCE.exists():
        sys.exit(f"source dir not found: {SOURCE}")

    if CANONICAL.exists():
        shutil.rmtree(CANONICAL)
    CANONICAL.mkdir(parents=True)

    seed_dirs = sorted(
        SOURCE.glob("sigma_*/pi_*/base_opp_*/exit_threshold_*/seed_*")
    )
    if not seed_dirs:
        sys.exit(f"no seed dirs found under {SOURCE}")
    print(f"processing {len(seed_dirs)} seed dirs from {SOURCE.relative_to(REPO_ROOT)}")

    seed_df, summary_df, timeseries_df = buildSeedAndSummary(seed_dirs)

    seed_df.to_csv(CANONICAL / "sweep_seed_results.csv", index=False)
    print(f"wrote {(CANONICAL / 'sweep_seed_results.csv').relative_to(REPO_ROOT)} ({len(seed_df)} rows)")

    summary_df.to_csv(CANONICAL / "sweep_summary.csv", index=False)
    print(f"wrote {(CANONICAL / 'sweep_summary.csv').relative_to(REPO_ROOT)} ({len(summary_df)} rows)")

    # per-regime timeseries CSVs (per-seed-per-step rows; figure 4 averages across seeds)
    for regime in REGIMES_HIER:
        sub = timeseries_df[timeseries_df["regime_hier"] == regime]
        outpath = CANONICAL / f"timeseries_regime_hier_{regime}.csv"
        sub.to_csv(outpath, index=False)
        print(f"wrote {outpath.name} ({len(sub)} rows)")

    # invoke phase_bundle builder (frozen artifact, parameterized via --root)
    print(f"invoking scripts/build_v2_5_phase_bundle.py against canonical dir...")
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "build_v2_5_phase_bundle.py"),
            "--root",
            str(CANONICAL),
        ],
        check=True,
        cwd=str(REPO_ROOT),
    )

    # gate: regime counts must match expected
    counts = summary_df["regime_majority_hier"].value_counts().to_dict()
    print(f"\nregime_majority_hier counts: {counts}")
    ok = all(counts.get(k, 0) == v for k, v in EXPECTED_HIER.items()) and sum(counts.values()) == 72
    if not ok:
        sys.exit(f"FAIL: expected {EXPECTED_HIER}, got {counts}")
    print(f"PASS: matches expected {EXPECTED_HIER}")
    print(f"\nbuilt {CANONICAL.relative_to(REPO_ROOT)}/ with regime counts: {counts}")


if __name__ == "__main__":
    main()
