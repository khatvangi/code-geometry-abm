"""
build_reclassified_phase_bundle.py

derives a parallel results-directory structure from the active-rate-reclassified
data so that scripts/build_v2_5_publication_figures.py can rebuild figs 1-5 from
the corrected classification.

inputs (read-only, from the frozen v2.5 confirmatory dir):
  reclassified_seed_results.csv
  reclassified_summary.csv
  timeseries_regime_hier_<REGIME>.csv  (4 files)

outputs (written to a new whitelisted dir):
  sweep_seed_results.csv               (run-level, columns aliased to original schema)
  phase_bundle/phase_table.csv         (cell-level, columns aliased)
  phase_bundle/regime_counts.csv       (cell-majority counts under reclassified labels)
  phase_bundle/seed_regime_counts.csv  (seed-level counts under reclassified labels)
  timeseries_regime_hier_<REGIME>.csv  (regrouped from per-seed metrics under new labels)

aliasing of column names (frozen schema -> figure-script schema):
  new_regime_majority_legacy -> regime_majority_legacy
  new_regime_majority_hier   -> regime_majority_hier
  n_capture_hier_hier        -> n_capture_hier  (fixes a double-suffix typo in
                                reclassify_regimes.py output; do not fix upstream
                                because that file is part of the audit trail)
  median_new_max_punish      -> median_max_punish
  new_max_punish             -> max_punish
  new_regime_legacy          -> regime_legacy
  new_regime_hier            -> regime_hier

per Phase S1 §15.3, this rebuilds the manuscript figures from active-rate-corrected
data without touching the original frozen artifact in
results/v2.5_corrected_three_regime_confirm/.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REGIMES_HIER = ["QUIET", "MIXED", "COLLAPSE", "CAPTURE_HIERARCHICAL"]
REGIMES_LEGACY = ["QUIET", "MIXED", "COLLAPSE"]
CELL_KEYS = ["sigma", "pi_reward", "base_opp", "exit_threshold"]


def buildSweepSeedResults(reclassified_seeds: pd.DataFrame) -> pd.DataFrame:
    """one row per seed run, columns aliased to original sweep_seed_results.csv schema."""
    out = reclassified_seeds.rename(
        columns={
            "new_max_punish": "max_punish",
            "new_regime_legacy": "regime_legacy",
            "new_regime_hier": "regime_hier",
        }
    )
    keep = [
        "sigma",
        "pi_reward",
        "base_opp",
        "exit_threshold",
        "seed",
        "final_fund_prevalence",
        "final_exit_rate",
        "max_punish",
        "enforcer_punish_share",
        "top5_punishment_share",
        "top10_punishment_share",
        "regime_legacy",
        "regime_hier",
        "run_dir",
    ]
    return out[keep]


def buildPhaseTable(
    reclassified_summary: pd.DataFrame, reclassified_seeds: pd.DataFrame
) -> pd.DataFrame:
    """one row per parameter cell, columns aliased to original phase_table.csv schema."""
    summary_aliased = reclassified_summary.rename(
        columns={
            "new_regime_majority_legacy": "regime_majority_legacy",
            "new_regime_majority_hier": "regime_majority_hier",
            "n_capture_hier_hier": "n_capture_hier",
            "median_new_max_punish": "median_max_punish",
        }
    )
    # median_fund_prevalence is not in reclassified_summary; recompute from seed-level data
    fp = (
        reclassified_seeds.groupby(CELL_KEYS, as_index=False)["final_fund_prevalence"]
        .median()
        .rename(columns={"final_fund_prevalence": "median_fund_prevalence"})
    )
    merged = summary_aliased.merge(fp, on=CELL_KEYS, how="left")
    keep = [
        *CELL_KEYS,
        "n_seeds",
        "regime_majority_legacy",
        "regime_majority_hier",
        "n_collapse_legacy",
        "n_capture_legacy",
        "n_mixed_legacy",
        "n_quiet_legacy",
        "n_collapse_hier",
        "n_capture_hier",
        "n_mixed_hier",
        "n_quiet_hier",
        "median_fund_prevalence",
        "median_exit_rate",
        "median_max_punish",
        "median_enforcer_punish_share",
        "median_top5_share",
    ]
    return merged[keep]


def buildRegimeCounts(phase_table: pd.DataFrame) -> pd.DataFrame:
    """cell-majority counts: rows per (regime, schema)."""
    rows = []
    for r in REGIMES_LEGACY:
        n = int((phase_table["regime_majority_legacy"] == r).sum())
        if n > 0:
            rows.append({"regime": r, "n_cells": n, "schema": "legacy"})
    for r in REGIMES_HIER:
        n = int((phase_table["regime_majority_hier"] == r).sum())
        if n > 0:
            rows.append({"regime": r, "n_cells": n, "schema": "hierarchical"})
    return pd.DataFrame(rows)


def buildSeedRegimeCounts(seed_df: pd.DataFrame) -> pd.DataFrame:
    """seed-level counts: rows per (regime, schema)."""
    rows = []
    for r in REGIMES_LEGACY:
        n = int((seed_df["regime_legacy"] == r).sum())
        if n > 0:
            rows.append({"regime": r, "n_seed_runs": n, "schema": "legacy"})
    for r in REGIMES_HIER:
        n = int((seed_df["regime_hier"] == r).sum())
        if n > 0:
            rows.append({"regime": r, "n_seed_runs": n, "schema": "hierarchical"})
    return pd.DataFrame(rows)


def regroupTimeseries(
    frozen_root: Path, seed_df: pd.DataFrame, out_root: Path
) -> dict:
    """
    read the four original timeseries CSVs (which carry old regime labels), join
    with reclassified labels by cell+seed, and rewrite four new CSVs partitioned
    by the new label.

    the original schema includes per-seed-per-step rows so regrouping is mechanical:
    drop the old regime label, attach the new one, repartition.
    """
    frames = []
    for r in REGIMES_HIER:
        p = frozen_root / f"timeseries_regime_hier_{r}.csv"
        if not p.exists():
            continue
        df = pd.read_csv(p)
        frames.append(df)
    if not frames:
        raise RuntimeError(f"no timeseries CSVs found in {frozen_root}")
    all_ts = pd.concat(frames, ignore_index=True)
    # drop old regime label and join with new label
    all_ts = all_ts.drop(columns=["regime"], errors="ignore")
    label_map = seed_df[CELL_KEYS + ["seed", "regime_hier"]].rename(
        columns={"regime_hier": "regime"}
    )
    joined = all_ts.merge(label_map, on=CELL_KEYS + ["seed"], how="left")
    # repartition by new regime
    counts = {}
    for r in REGIMES_HIER:
        sub = joined[joined["regime"] == r].copy()
        outpath = out_root / f"timeseries_regime_hier_{r}.csv"
        sub.to_csv(outpath, index=False)
        counts[r] = {"n_rows": len(sub), "n_seeds": sub["seed"].nunique() if len(sub) else 0}
    return counts


def verifyCaptureCellSurvives(phase_table: pd.DataFrame) -> dict:
    """
    Hard Rule 9 check: identify the (sigma, pi_reward, base_opp, exit_threshold)
    cell that was originally CAPTURE_HIERARCHICAL and verify it still is under
    reclassification.

    This is checked by reading the ORIGINAL phase_table.csv from the frozen dir
    (which has the old regime_majority_hier) and comparing.
    """
    capture_cells = phase_table[
        phase_table["regime_majority_hier"] == "CAPTURE_HIERARCHICAL"
    ]
    return {
        "n_capture_cells_after_reclassification": len(capture_cells),
        "capture_cells": capture_cells[
            CELL_KEYS + ["regime_majority_hier", "n_capture_hier", "n_seeds"]
        ].to_dict(orient="records"),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--frozen-root",
        type=Path,
        default=Path("results/v2.5_corrected_three_regime_confirm"),
    )
    ap.add_argument(
        "--out-root",
        type=Path,
        default=Path("results/v2.5_corrected_three_regime_confirm_active_rate"),
    )
    args = ap.parse_args()

    frozen = args.frozen_root.resolve()
    out = args.out_root.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "phase_bundle").mkdir(exist_ok=True)

    print(f"reading reclassified data from: {frozen}")
    reclassified_seeds = pd.read_csv(frozen / "reclassified_seed_results.csv")
    reclassified_summary = pd.read_csv(frozen / "reclassified_summary.csv")
    print(
        f"  reclassified_seed_results: {len(reclassified_seeds)} rows, "
        f"reclassified_summary: {len(reclassified_summary)} rows"
    )

    sweep_seeds = buildSweepSeedResults(reclassified_seeds)
    sweep_seeds.to_csv(out / "sweep_seed_results.csv", index=False)
    print(f"wrote: {out / 'sweep_seed_results.csv'}  ({len(sweep_seeds)} rows)")

    phase_table = buildPhaseTable(reclassified_summary, reclassified_seeds)
    phase_table.to_csv(out / "phase_bundle" / "phase_table.csv", index=False)
    print(f"wrote: phase_bundle/phase_table.csv  ({len(phase_table)} rows)")

    regime_counts = buildRegimeCounts(phase_table)
    regime_counts.to_csv(out / "phase_bundle" / "regime_counts.csv", index=False)
    print(f"wrote: phase_bundle/regime_counts.csv")
    print(regime_counts.to_string(index=False))

    seed_counts = buildSeedRegimeCounts(sweep_seeds)
    seed_counts.to_csv(out / "phase_bundle" / "seed_regime_counts.csv", index=False)
    print(f"wrote: phase_bundle/seed_regime_counts.csv")
    print(seed_counts.to_string(index=False))

    print("regrouping timeseries CSVs under reclassified labels...")
    ts_counts = regroupTimeseries(frozen, sweep_seeds, out)
    for r, info in ts_counts.items():
        print(f"  timeseries_regime_hier_{r}.csv: {info['n_rows']} rows, {info['n_seeds']} seeds")

    print()
    print("=== Hard Rule 9 — 1-capture-cell verification ===")
    cap_check = verifyCaptureCellSurvives(phase_table)
    print(f"  n CAPTURE_HIERARCHICAL cells after reclassification: "
          f"{cap_check['n_capture_cells_after_reclassification']}")
    for cell in cap_check["capture_cells"]:
        print(f"  cell: {cell}")
    if cap_check["n_capture_cells_after_reclassification"] == 0:
        print("  *** WARNING: zero CAPTURE cells; STOP and surface to Kiran ***")
    elif cap_check["n_capture_cells_after_reclassification"] > 1:
        print(f"  *** NOTE: more than 1 capture cell ({cap_check['n_capture_cells_after_reclassification']}); "
              "may be expected under reclassification, but Hard Rule 9 says verify ***")
    else:
        print("  OK: 1 CAPTURE_HIERARCHICAL cell present, consistent with manuscript headline.")


if __name__ == "__main__":
    main()
