#!/usr/bin/env python3
"""aggregate the v3.0 envelope sweep — Phase S2 §5.3.

inputs:  results/v3_0_envelope_sweep/<template>/grid_<i>/seed_<s>/metrics.csv
                                                                /agent_summary.csv
outputs (in same root):
    sweep_seed_results.csv         — 1200 rows, one per seed
    sweep_summary.csv              — 40 rows, one per (template, grid) cell
    template_regime_counts.csv     — per-template regime distribution
    phase_map_v3_0.png             — 8-panel σ×π regime map

regime classification uses `active_punish_rate` directly per §4.1 / §5.3
of INSTRUCTION_BORON_S2.md — no post-hoc reclassification. thresholds
match manuscript §6.10:
    COLLAPSE: exit_rate >= 0.90
    CAPTURE:  fund_prevalence >= 0.90 AND exit_rate <= 0.20
    MIXED:    max(active_punish_rate) >= 0.10 AND not collapse/capture
    QUIET:    residual

cell-level regime by majority vote across the 30 seeds.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

REPO_ROOT = Path(__file__).resolve().parent.parent
SWEEP_ROOT = REPO_ROOT / "results" / "v3_0_envelope_sweep"
sys.path.insert(0, str(REPO_ROOT / "src"))
import religion_fundamentalism_abm_v3_0 as v30  # noqa: E402

REGIME_ORDER = ("QUIET", "MIXED", "COLLAPSE", "CAPTURE")
REGIME_COLORS = {
    "QUIET":    "#9AA0A6",
    "MIXED":    "#0072B2",
    "COLLAPSE": "#D55E00",
    "CAPTURE":  "#009E73",
}
REGIME_TO_CODE = {r: i for i, r in enumerate(REGIME_ORDER)}


def classifyRegime(exit_rate: float, fund_prevalence: float, max_apr: float) -> str:
    """active-rate-aware regime classifier (manuscript §6.10 with active_punish_rate)."""
    if exit_rate >= 0.90:
        return "COLLAPSE"
    if fund_prevalence >= 0.90 and exit_rate <= 0.20:
        return "CAPTURE"
    if max_apr >= 0.10:
        return "MIXED"
    return "QUIET"


def topShare(values, frac: float) -> float:
    """top-frac concentration share (matches v2.5 aggregator semantics)."""
    x = np.asarray(values, dtype=float)
    total = float(np.sum(x))
    if x.size == 0 or total <= 0:
        return 0.0
    k = max(1, int(np.ceil(frac * x.size)))
    return float(np.sum(np.sort(x)[::-1][:k]) / total)


def collectSeedRows() -> pd.DataFrame:
    """walk SWEEP_ROOT and produce one row per (template, grid, seed)."""
    rows = []
    for metrics_path in sorted(SWEEP_ROOT.rglob("metrics.csv")):
        seed_dir = metrics_path.parent
        agent_path = seed_dir / "agent_summary.csv"
        if not agent_path.exists():
            continue

        # parse path: results/v3_0_envelope_sweep/T1/grid_0/seed_01/
        parts = metrics_path.relative_to(SWEEP_ROOT).parts
        template = parts[0]
        grid_idx = int(parts[1].replace("grid_", ""))
        seed = int(parts[2].replace("seed_", ""))

        m = pd.read_csv(metrics_path)
        a = pd.read_csv(agent_path)

        # terminal state
        last = m.iloc[-1]
        exit_rate = float(last["exit_rate"])
        fund_prev = float(last["fund_prevalence"])
        max_apr = float(m["active_punish_rate"].max())
        max_pr = float(m["punish_rate"].max())
        regime = classifyRegime(exit_rate, fund_prev, max_apr)

        # concentration on agent_summary punish_issued
        punish_issued = a["punish_issued"].values if "punish_issued" in a.columns else np.zeros(0)
        top5 = topShare(punish_issued, 5.0 / len(punish_issued)) if len(punish_issued) > 0 else 0.0
        top10 = topShare(punish_issued, 10.0 / len(punish_issued)) if len(punish_issued) > 0 else 0.0

        # enforcer share
        if "is_enforcer" in a.columns and len(punish_issued) > 0:
            enf_mask = a["is_enforcer"].astype(bool).values
            enf_total = float(punish_issued[enf_mask].sum())
            grand_total = float(punish_issued.sum())
            enforcer_share = enf_total / grand_total if grand_total > 0 else 0.0
        else:
            enforcer_share = 0.0

        # envelope ceilings for context
        sigma_max, pi_max, base_opp_floor, exit_cost_baseline = v30.ENVELOPE_TABLE[template]

        rows.append({
            "template": template,
            "grid": grid_idx,
            "seed": seed,
            "sigma_max": sigma_max,
            "pi_max": pi_max,
            "base_opp_floor": base_opp_floor,
            "exit_cost_baseline": exit_cost_baseline,
            "exit_rate": exit_rate,
            "fund_prevalence": fund_prev,
            "max_active_punish_rate": max_apr,
            "max_punish_rate": max_pr,
            "regime": regime,
            "top5_share": top5,
            "top10_share": top10,
            "enforcer_share": enforcer_share,
            "run_dir": str(seed_dir),
        })
    return pd.DataFrame(rows)


def cellSummary(seeds: pd.DataFrame) -> pd.DataFrame:
    """40-row cell summary: one row per (template, grid) cell, majority-vote regime."""
    rows = []
    for (t, g), grp in seeds.groupby(["template", "grid"], sort=True):
        regime_counts = grp["regime"].value_counts().reindex(REGIME_ORDER, fill_value=0)
        majority = regime_counts.idxmax()
        rows.append({
            "template": t,
            "grid": g,
            "n_seeds": len(grp),
            "sigma_max": float(grp["sigma_max"].iloc[0]),
            "pi_max": float(grp["pi_max"].iloc[0]),
            # cell-level (sigma, pi) — same across seeds
            "sigma_cell": float(grp["sigma_max"].iloc[0] *
                                (0.500 + 0.125 * g)),
            "pi_cell":    float(grp["pi_max"].iloc[0] *
                                (0.200 + 0.200 * g)),
            "regime_majority": majority,
            **{f"n_{r}": int(regime_counts[r]) for r in REGIME_ORDER},
            "median_exit_rate": float(grp["exit_rate"].median()),
            "median_max_apr": float(grp["max_active_punish_rate"].median()),
            "median_top5_share": float(grp["top5_share"].median()),
            "median_enforcer_share": float(grp["enforcer_share"].median()),
        })
    return pd.DataFrame(rows)


def templateRegimeCounts(seeds: pd.DataFrame) -> pd.DataFrame:
    """per-template per-grid regime distribution. 40 rows × (4 regime cols + meta)."""
    pivot = (seeds.groupby(["template", "grid", "regime"], sort=True)
             .size().unstack(fill_value=0).reindex(columns=REGIME_ORDER, fill_value=0)
             .reset_index())
    return pivot


def plotPhaseMap(seeds: pd.DataFrame, summary: pd.DataFrame, out_path: Path) -> None:
    """8-panel σ×π phase map. one panel per template; cell color = majority regime."""
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "savefig.dpi": 200,
    })

    templates = sorted(summary["template"].unique())
    fig, axes = plt.subplots(2, 4, figsize=(16, 8), sharex=False, sharey=False)
    axes = axes.flatten()

    cmap = ListedColormap([REGIME_COLORS[r] for r in REGIME_ORDER])

    for idx, t in enumerate(templates):
        ax = axes[idx]
        sub = summary[summary["template"] == t].sort_values("grid")
        sigma_max = sub["sigma_max"].iloc[0]
        pi_max = sub["pi_max"].iloc[0]

        # plot each cell as a colored marker
        regime_codes = sub["regime_majority"].map(REGIME_TO_CODE).values
        ax.scatter(
            sub["sigma_cell"], sub["pi_cell"],
            c=regime_codes, cmap=cmap, vmin=0, vmax=3,
            s=400, edgecolors="black", linewidths=1.0,
        )
        # annotate each point with grid index
        for _, r in sub.iterrows():
            ax.annotate(f"g{int(r['grid'])}", (r["sigma_cell"], r["pi_cell"]),
                        fontsize=7, ha="center", va="center", color="white")

        ax.set_xlim(0, max(0.7, sigma_max * 1.1))
        ax.set_ylim(0, max(0.5, pi_max * 1.2))
        ax.set_xlabel(r"$\sigma$ (legibility)", fontsize=9)
        ax.set_ylabel(r"$\pi$ (enforcement reward)", fontsize=9)
        ax.set_title(f"{t}  envelope: σ≤{sigma_max:.2f}  π≤{pi_max:.2f}", fontsize=10)
        ax.tick_params(labelsize=8)

    # legend
    handles = [plt.Line2D([0], [0], marker="o", color="w",
                          markerfacecolor=REGIME_COLORS[r],
                          markeredgecolor="black", markersize=10, label=r)
               for r in REGIME_ORDER]
    fig.legend(handles=handles, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.02),
               fontsize=10, frameon=False)
    fig.suptitle("v3.0 envelope sweep: regime by template × grid (majority across 30 seeds)",
                 fontsize=12, y=1.00)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    print(f"aggregating sweep at {SWEEP_ROOT}")
    seeds = collectSeedRows()
    print(f"collected {len(seeds)} seed rows ({seeds['template'].nunique()} templates × "
          f"{seeds['grid'].nunique()} grids × {seeds['seed'].nunique()} seeds)")

    seeds_path = SWEEP_ROOT / "sweep_seed_results.csv"
    seeds.to_csv(seeds_path, index=False)
    print(f"wrote {seeds_path} ({seeds_path.stat().st_size} bytes, {len(seeds)} rows)")

    summary = cellSummary(seeds)
    summary_path = SWEEP_ROOT / "sweep_summary.csv"
    summary.to_csv(summary_path, index=False)
    print(f"wrote {summary_path} ({summary_path.stat().st_size} bytes, {len(summary)} rows)")

    counts = templateRegimeCounts(seeds)
    counts_path = SWEEP_ROOT / "template_regime_counts.csv"
    counts.to_csv(counts_path, index=False)
    print(f"wrote {counts_path} ({counts_path.stat().st_size} bytes, {len(counts)} rows)")

    phase_path = SWEEP_ROOT / "phase_map_v3_0.png"
    plotPhaseMap(seeds, summary, phase_path)
    print(f"wrote {phase_path} ({phase_path.stat().st_size} bytes)")

    print("\n--- diagnostics ---")
    print("regime distribution by template:")
    by_template = seeds.groupby("template")["regime"].value_counts().unstack(fill_value=0)
    by_template = by_template.reindex(columns=REGIME_ORDER, fill_value=0)
    print(by_template.to_string())
    print()
    print("cell-level majority regime by template × grid:")
    pivot = summary.pivot(index="template", columns="grid", values="regime_majority")
    print(pivot.to_string())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
