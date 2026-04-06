#!/usr/bin/env python3
"""reclassify regimes using active-only punishment rate.

the original punish_rate in metrics.csv divides by ALL agents (including
exited). with exit rates of 0.59-0.72, this dilutes punishment intensity
by 60-70%. this script recomputes active-only punishment rate from the
existing per-step data and reclassifies each run.

reconstruction formula:
  active_punish_rate = punish_rate / (1 - exit_rate)
  (valid because exited agents always have punished=0)

usage:
  python scripts/reclassify_regimes.py results/v2.5_corrected_three_regime_confirm/
  python scripts/reclassify_regimes.py results/v2.7_endogenous_delta_sweep/
"""

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ── regime classification (unchanged thresholds) ─────────────────────

LEGACY_ORDER = ["COLLAPSE", "CAPTURE", "MIXED", "QUIET"]
HIER_ORDER = ["COLLAPSE", "CAPTURE_HIERARCHICAL", "MIXED", "QUIET"]


def classify_legacy(exit_rate: float, prevalence: float, max_punish: float) -> str:
    if exit_rate >= 0.90:
        return "COLLAPSE"
    if prevalence >= 0.90 and exit_rate <= 0.20:
        return "CAPTURE"
    if max_punish >= 0.10:
        return "MIXED"
    return "QUIET"


def classify_hier(
    exit_rate: float,
    max_punish: float,
    enforcer_punish_share: float,
    capture_exit_cap: float = 0.20,
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


# ── detect sweep layout ─────────────────────────────────────────────

def detect_layout(root: Path) -> str:
    """detect directory structure from the first metrics.csv found.
    actual layouts observed:
      v2.5:          sigma_X/pi_X/base_opp_X/seed_XX                     (4 dirs)
      v2.5_extended: sigma_X/pi_X/base_opp_X/exit_threshold_X/seed_XX    (5 dirs)
      v2.7:          eta_X/delta0_X/sigma_X/pi_X/seed_XX                  (5 dirs)
    """
    for mpath in sorted(root.rglob("metrics.csv")):
        rel_parts = mpath.relative_to(root).parts[:-1]  # drop "metrics.csv"
        depth = len(rel_parts)
        if rel_parts[0].startswith("eta_"):
            return "v2.7"  # eta/delta0/sigma/pi/seed (5 levels)
        if depth >= 5 and rel_parts[0].startswith("sigma_"):
            return "v2.5_extended"  # sigma/pi/base_opp/exit_threshold/seed
        if depth >= 4 and rel_parts[0].startswith("sigma_"):
            return "v2.5"  # sigma/pi/base_opp/seed
    return "unknown"


def parse_path_v25(rel_parts: tuple) -> dict:
    """parse sigma_X/pi_X/base_opp_X/seed_XX."""
    sigma = float(rel_parts[0].split("_", 1)[1])
    pi = float(rel_parts[1].split("_", 1)[1])
    opp = float(rel_parts[2].split("_", 2)[2])
    seed = int(rel_parts[3].split("_", 1)[1])
    return {"sigma": sigma, "pi_reward": pi, "base_opp": opp, "seed": seed}


def parse_path_v25_extended(rel_parts: tuple) -> dict:
    """parse sigma_X/pi_X/base_opp_X/exit_threshold_X/seed_XX."""
    sigma = float(rel_parts[0].split("_", 1)[1])
    pi = float(rel_parts[1].split("_", 1)[1])
    opp = float(rel_parts[2].split("_", 2)[2])
    ex_th = float(rel_parts[3].split("_", 2)[2])
    seed = int(rel_parts[4].split("_", 1)[1])
    return {"sigma": sigma, "pi_reward": pi, "base_opp": opp, "exit_threshold": ex_th, "seed": seed}


def parse_path_v27(rel_parts: tuple) -> dict:
    """parse eta_X/delta0_X/sigma_X/pi_X/seed_XX."""
    eta = float(rel_parts[0].split("_", 1)[1])
    delta0 = float(rel_parts[1].split("_", 1)[1])
    sigma = float(rel_parts[2].split("_", 1)[1])
    pi = float(rel_parts[3].split("_", 1)[1])
    seed = int(rel_parts[4].split("_", 1)[1])
    return {
        "eta_delta_drift": eta, "delta0": delta0,
        "sigma": sigma, "pi_reward": pi, "seed": seed,
    }


PARSERS = {
    "v2.5": parse_path_v25,
    "v2.5_extended": parse_path_v25_extended,
    "v2.7": parse_path_v27,
}


# ── main reclassification logic ─────────────────────────────────────

def recompute_active_punish_rate(mdf: pd.DataFrame) -> float:
    """compute max active-only punish rate from per-step metrics.csv.

    active_punish_rate_t = punish_rate_t / (1 - exit_rate_t)
    returns max across all timesteps.
    """
    pr = pd.to_numeric(mdf.get("punish_rate", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
    er = pd.to_numeric(mdf.get("exit_rate", pd.Series(dtype=float)), errors="coerce").fillna(0.0)

    # active fraction; guard division by zero (all exited)
    active_frac = 1.0 - er
    active_pr = np.where(active_frac > 1e-9, pr / active_frac, 0.0)

    return float(np.max(active_pr)) if len(active_pr) > 0 else 0.0


def compute_enforcer_share(mdf: pd.DataFrame, adf: pd.DataFrame) -> float:
    """compute enforcer punishment share. uses enforcer_punish_share_step
    from metrics if available, otherwise falls back to agent_summary."""
    eps = 1e-9
    step_share = pd.to_numeric(
        mdf.get("enforcer_punish_share_step", pd.Series(dtype=float)), errors="coerce"
    ).replace([np.inf, -np.inf], np.nan)
    pr = pd.to_numeric(mdf.get("punish_rate", pd.Series(dtype=float)), errors="coerce")
    mask = pr > 0
    if mask.any() and not step_share.isna().all():
        enforcer_share = float(step_share[mask].fillna(0.0).mean())
    else:
        enforcer_share = 0.0
    return float(max(0.0, min(1.0, enforcer_share + eps)))


def process_run(mpath: Path, root: Path, layout: str, capture_exit_cap: float) -> dict | None:
    """process a single run: read CSVs, recompute active punish_rate, reclassify."""
    seed_dir = mpath.parent
    agent_path = seed_dir / "agent_summary.csv"
    if not agent_path.exists():
        return None

    rel_parts = mpath.relative_to(root).parts[:-1]  # drop "metrics.csv"
    parser = PARSERS.get(layout)
    if parser is None:
        return None
    try:
        params = parser(rel_parts)
    except (ValueError, IndexError):
        return None

    mdf = pd.read_csv(mpath)
    adf = pd.read_csv(agent_path)
    if mdf.empty:
        return None

    final = mdf.iloc[-1]
    prevalence = float(final.get("fund_prevalence", np.nan))
    exit_rate = float(final.get("exit_rate", np.nan))

    # original (diluted) max_punish
    old_max_punish = float(mdf["punish_rate"].max()) if "punish_rate" in mdf.columns else np.nan

    # corrected active-only max_punish
    new_max_punish = recompute_active_punish_rate(mdf)

    # cross-validate with punish_intensity_step if available (v2.7)
    if "punish_intensity_step" in mdf.columns:
        pis = pd.to_numeric(mdf["punish_intensity_step"], errors="coerce").fillna(0.0)
        max_pis = float(pis.max())
        params["max_punish_intensity_step"] = max_pis

    # enforcer share (needed for hierarchical classification)
    enforcer_share = compute_enforcer_share(mdf, adf)

    # punishment concentration from agent_summary (active agents only)
    punish_col = pd.to_numeric(
        adf.get("punish_issued", pd.Series(dtype=float)), errors="coerce"
    ).fillna(0.0).to_numpy(dtype=float)
    top5 = top_share(punish_col, 0.05)
    top10 = top_share(punish_col, 0.10)

    # old classification (using diluted max_punish)
    old_legacy = classify_legacy(exit_rate, prevalence, old_max_punish)
    old_hier = classify_hier(exit_rate, old_max_punish, enforcer_share, capture_exit_cap)

    # new classification (using active-only max_punish)
    new_legacy = classify_legacy(exit_rate, prevalence, new_max_punish)
    new_hier = classify_hier(exit_rate, new_max_punish, enforcer_share, capture_exit_cap)

    row = {
        **params,
        "run_dir": str(seed_dir),
        "final_fund_prevalence": prevalence,
        "final_exit_rate": exit_rate,
        "old_max_punish": old_max_punish,
        "new_max_punish": new_max_punish,
        "enforcer_punish_share": enforcer_share,
        "top5_punishment_share": top5,
        "top10_punishment_share": top10,
        "old_regime_legacy": old_legacy,
        "new_regime_legacy": new_legacy,
        "old_regime_hier": old_hier,
        "new_regime_hier": new_hier,
        "reclassified_legacy": old_legacy != new_legacy,
        "reclassified_hier": old_hier != new_hier,
        "reclassified": old_legacy != new_legacy or old_hier != new_hier,
    }
    return row


# ── cell-level summary with ceil consensus ───────────────────────────

def majority_regime(series: pd.Series, order: list) -> str:
    """consensus rule: if top count >= ceil(0.7 * n_seeds), use it.
    otherwise, plurality with tiebreak by order (most severe first)."""
    vc = series.value_counts()
    if vc.empty:
        return "QUIET"
    n_seeds = len(series)
    threshold = math.ceil(0.7 * n_seeds)
    topn = vc.max()
    if topn >= threshold:
        # consensus
        tied = sorted([r for r, n in vc.items() if n == topn], key=lambda r: order.index(r))
        return tied[0]
    # no consensus — plurality, tiebreak by severity (lower index = more severe)
    tied = sorted([r for r, n in vc.items() if n == topn], key=lambda r: order.index(r))
    return tied[0]


def build_cell_summary(df: pd.DataFrame, layout: str) -> pd.DataFrame:
    """aggregate seed-level results to cell-level summary with old and new regimes."""
    if layout == "v2.7":
        gcols = ["eta_delta_drift", "delta0", "sigma", "pi_reward", "base_opp", "exit_threshold"]
    elif layout in ("v2.5_extended", "emergence"):
        gcols = ["sigma", "pi_reward", "base_opp", "exit_threshold"]
        if layout == "emergence":
            gcols = ["component"] + gcols
    else:
        gcols = ["sigma", "pi_reward", "base_opp"]

    # filter to columns that exist
    gcols = [c for c in gcols if c in df.columns]
    if not gcols:
        return pd.DataFrame()

    rows = []
    for key, g in df.groupby(gcols, as_index=False):
        if not isinstance(key, tuple):
            key = (key,)
        row = dict(zip(gcols, key))
        row["n_seeds"] = int(len(g))

        # old cell-level majority
        row["old_regime_majority_legacy"] = majority_regime(g["old_regime_legacy"], LEGACY_ORDER)
        row["old_regime_majority_hier"] = majority_regime(g["old_regime_hier"], HIER_ORDER)

        # new cell-level majority
        row["new_regime_majority_legacy"] = majority_regime(g["new_regime_legacy"], LEGACY_ORDER)
        row["new_regime_majority_hier"] = majority_regime(g["new_regime_hier"], HIER_ORDER)

        # counts (new)
        for regime in LEGACY_ORDER:
            row[f"n_{regime.lower()}_legacy"] = int((g["new_regime_legacy"] == regime).sum())
        for regime in HIER_ORDER:
            rkey = regime.lower().replace("capture_hierarchical", "capture_hier")
            row[f"n_{rkey}_hier"] = int((g["new_regime_hier"] == regime).sum())

        # cell changed?
        row["cell_reclassified_legacy"] = row["old_regime_majority_legacy"] != row["new_regime_majority_legacy"]
        row["cell_reclassified_hier"] = row["old_regime_majority_hier"] != row["new_regime_majority_hier"]

        # median metrics (new)
        row["median_new_max_punish"] = float(g["new_max_punish"].median())
        row["median_old_max_punish"] = float(g["old_max_punish"].median())
        row["median_exit_rate"] = float(g["final_exit_rate"].median())
        row["median_top5_share"] = float(g["top5_punishment_share"].median())
        row["median_enforcer_punish_share"] = float(g["enforcer_punish_share"].median())

        rows.append(row)

    return pd.DataFrame(rows).sort_values(gcols)


# ── summary printing ─────────────────────────────────────────────────

def print_summary(df: pd.DataFrame, cell_df: pd.DataFrame, root: Path):
    n_total = len(df)
    n_reclass = int(df["reclassified"].sum())
    n_reclass_legacy = int(df["reclassified_legacy"].sum())
    n_reclass_hier = int(df["reclassified_hier"].sum())

    print(f"\n{'='*70}")
    print(f"RECLASSIFICATION SUMMARY: {root}")
    print(f"{'='*70}")
    print(f"total runs: {n_total}")
    print(f"runs reclassified (either schema): {n_reclass} ({100*n_reclass/max(1,n_total):.1f}%)")
    print(f"  legacy only: {n_reclass_legacy}")
    print(f"  hierarchical only: {n_reclass_hier}")

    # direction of reclassification
    for schema in ["legacy", "hier"]:
        changed = df[df[f"reclassified_{schema}"]].copy()
        if changed.empty:
            continue
        print(f"\n--- {schema} reclassification transitions ---")
        changed["transition"] = changed[f"old_regime_{schema}"] + " -> " + changed[f"new_regime_{schema}"]
        for trans, count in changed["transition"].value_counts().items():
            print(f"  {trans}: {count}")

    # old vs new regime counts (seed-level)
    print(f"\n--- seed-level regime counts ---")
    for schema, order in [("legacy", LEGACY_ORDER), ("hier", HIER_ORDER)]:
        print(f"\n  {schema}:")
        old_counts = df[f"old_regime_{schema}"].value_counts()
        new_counts = df[f"new_regime_{schema}"].value_counts()
        for r in order:
            old_n = int(old_counts.get(r, 0))
            new_n = int(new_counts.get(r, 0))
            delta = new_n - old_n
            marker = f" ({'+' if delta > 0 else ''}{delta})" if delta != 0 else ""
            print(f"    {r:25s}: {old_n:4d} -> {new_n:4d}{marker}")

    # cell-level summary
    if not cell_df.empty:
        n_cells = len(cell_df)
        print(f"\n--- cell-level regime counts ---")
        for schema, order in [("legacy", LEGACY_ORDER), ("hier", HIER_ORDER)]:
            old_col = f"old_regime_majority_{schema}"
            new_col = f"new_regime_majority_{schema}"
            reclass_col = f"cell_reclassified_{schema}"
            if old_col not in cell_df.columns:
                continue
            n_cell_reclass = int(cell_df[reclass_col].sum())
            print(f"\n  {schema} (n_cells={n_cells}, reclassified={n_cell_reclass}):")
            old_counts = cell_df[old_col].value_counts()
            new_counts = cell_df[new_col].value_counts()
            for r in order:
                old_n = int(old_counts.get(r, 0))
                new_n = int(new_counts.get(r, 0))
                delta = new_n - old_n
                marker = f" ({'+' if delta > 0 else ''}{delta})" if delta != 0 else ""
                print(f"    {r:25s}: {old_n:4d} -> {new_n:4d}{marker}")

            # show which cells changed
            if n_cell_reclass > 0:
                changed = cell_df[cell_df[reclass_col]].copy()
                changed["transition"] = changed[old_col] + " -> " + changed[new_col]
                print(f"\n    cell transitions ({schema}):")
                for _, row in changed.iterrows():
                    params = " ".join(
                        f"{c}={row[c]}" for c in ["sigma", "pi_reward", "base_opp", "exit_threshold"]
                        if c in row.index and pd.notna(row[c])
                    )
                    print(f"      {row['transition']:35s} | {params}")

    # cross-validation with punish_intensity_step (v2.7)
    if "max_punish_intensity_step" in df.columns:
        corr = df[["new_max_punish", "max_punish_intensity_step"]].dropna()
        if len(corr) > 1:
            r = float(corr["new_max_punish"].corr(corr["max_punish_intensity_step"]))
            mae = float((corr["new_max_punish"] - corr["max_punish_intensity_step"]).abs().mean())
            print(f"\n--- cross-validation vs punish_intensity_step ---")
            print(f"  correlation: {r:.4f}")
            print(f"  mean absolute error: {mae:.6f}")


# ── main ─────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="reclassify regimes using active-only punishment rate")
    ap.add_argument("root", type=Path, help="results directory to reclassify")
    ap.add_argument("--capture-exit-cap", type=float, default=0.20,
                    help="exit rate cap for CAPTURE classification (default: 0.20)")
    args = ap.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        sys.exit(1)

    layout = detect_layout(root)
    print(f"detected layout: {layout}")
    if layout == "unknown":
        print("error: could not detect sweep directory layout", file=sys.stderr)
        sys.exit(1)

    # collect all runs
    rows = []
    metrics_files = sorted(root.rglob("metrics.csv"))
    print(f"found {len(metrics_files)} metrics.csv files")

    for i, mpath in enumerate(metrics_files):
        row = process_run(mpath, root, layout, args.capture_exit_cap)
        if row is not None:
            rows.append(row)
        if (i + 1) % 50 == 0:
            print(f"  processed {i+1}/{len(metrics_files)}")

    if not rows:
        print("no valid runs found")
        sys.exit(1)

    df = pd.DataFrame(rows)
    print(f"processed {len(df)} runs")

    # save seed-level reclassification
    outpath = root / "reclassified_seed_results.csv"
    df.to_csv(outpath, index=False)
    print(f"wrote: {outpath}")

    # build and save cell-level summary
    cell_df = build_cell_summary(df, layout)
    if not cell_df.empty:
        cell_outpath = root / "reclassified_summary.csv"
        cell_df.to_csv(cell_outpath, index=False)
        print(f"wrote: {cell_outpath}")

    # print summary
    print_summary(df, cell_df, root)


if __name__ == "__main__":
    main()
