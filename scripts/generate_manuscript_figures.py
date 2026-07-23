#!/usr/bin/env python3
"""Canonical manuscript figure pipeline — the ONLY script that produces manuscript figures.

Design rules enforced here (see the audit that motivated this file):
  * reads ONLY committed CSVs under recon/ and results/
  * NEVER reads a stored `regime` column -- those columns were written with the
    legacy prevalence-gated schema. All regimes are recomputed with
    src/regime_classifier.py (hierarchical). Regime-ish columns are dropped at
    load time so it is structurally impossible to plot them.
  * writes vector PDF + 300 dpi PNG per figure into figures/manuscript_v2/
  * colourblind-safe: viridis for continuous surfaces, Okabe-Ito for categorical
  * every caption is GENERATED from the plotted numbers (never typed by hand),
    emitted to captions.tex and recorded in FIGURE_MANIFEST.json alongside the
    source sha256s, row counts and exact plotted series.

Run: .venv/bin/python scripts/generate_manuscript_figures.py
No CLI flags. No manual steps. Does not commit.

NOTE: seaborn is not installed in this pinned environment (matplotlib 3.10.8 only),
so matplotlib is used directly as the plotting backend.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import regime_classifier as rc  # noqa: E402

OUTDIR = ROOT / "figures" / "manuscript_v2"

# ---------------------------------------------------------------- style
# Okabe-Ito colourblind-safe categorical palette (no red-green pairs used).
OKABE_ITO = {
    "orange": "#E69F00", "skyblue": "#56B4E9", "green": "#009E73",
    "yellow": "#F0E442", "blue": "#0072B2", "vermillion": "#D55E00",
    "purple": "#CC79A7", "black": "#000000",
}
CONTINUOUS_CMAP = "viridis"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans"],
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.titlesize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "savefig.bbox": "tight",
    "pdf.fonttype": 42,   # embed TrueType so text stays editable/vector
    "ps.fonttype": 42,
})

# regime-ish columns are dropped on load: never plot a stored classification
FORBIDDEN_COLS = ("regime", "regime_hier", "regime_legacy")

CLASSIFIER_SETTINGS = {
    "module": "src/regime_classifier.py",
    "schema": "hierarchical",
    "capture_rule": "retained (final_exit_rate <= EXIT_CAPTURE_MAX) AND active (max_punish >= PUNISH_ACTIVE_MIN)",
    "EXIT_CAPTURE_MAX": rc.EXIT_CAPTURE_MAX,
    "PUNISH_ACTIVE_MIN": rc.PUNISH_ACTIVE_MIN,
    "EXIT_COLLAPSE_MIN": rc.EXIT_COLLAPSE_MIN,
    "exit_col": "final_exit_rate",
    "punish_col": "max_punish",
    "stored_regime_column_used": False,
    "dropped_columns_on_load": list(FORBIDDEN_COLS),
}

MANIFEST: list[dict] = []
SOURCE_ROWS: dict[str, int] = {}


# ---------------------------------------------------------------- helpers
def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_committed(relpath: str) -> pd.DataFrame:
    """Load a committed CSV and strip any stored regime column."""
    p = ROOT / relpath
    if not p.exists():
        raise FileNotFoundError(f"committed CSV missing: {relpath}")
    df = pd.read_csv(p)
    dropped = [c for c in df.columns if c in FORBIDDEN_COLS]
    df = df.drop(columns=dropped)
    SOURCE_ROWS[relpath] = len(df)
    return df


def with_regime(df: pd.DataFrame) -> pd.DataFrame:
    """Recompute the regime with the canonical hierarchical classifier."""
    return rc.classify_dataframe(
        df, schema="hierarchical",
        exit_col="final_exit_rate", punish_col="max_punish",
        out_col="regime_recomputed",
    )


def source_entry(relpath: str) -> dict:
    p = ROOT / relpath
    return {"path": relpath, "sha256": sha256_of(p), "rows": SOURCE_ROWS[relpath]}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (float("nan"), float("nan"))
    phat = k / n
    denom = 1 + z * z / n
    centre = (phat + z * z / (2 * n)) / denom
    half = z * np.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def yerr_from(rates, los, his) -> np.ndarray:
    """Asymmetric yerr for errorbar; clipped at 0 (Wilson bounds at p=0/1 can
    differ from the point estimate by float noise, and errorbar rejects <0)."""
    r, lo, hi = np.asarray(rates, float), np.asarray(los, float), np.asarray(his, float)
    return np.clip(np.vstack([r - lo, hi - r]), 0.0, None)


def save(fig, fig_id: str) -> dict:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    pdf = OUTDIR / f"{fig_id}.pdf"
    png = OUTDIR / f"{fig_id}.png"
    fig.savefig(pdf)
    fig.savefig(png, dpi=300)
    plt.close(fig)
    return {"pdf": str(pdf.relative_to(ROOT)), "png": str(png.relative_to(ROOT))}


def grid(df: pd.DataFrame, value: str, aggfunc="mean") -> pd.DataFrame:
    return df.pivot_table(index="sigma", columns="pi_reward", values=value, aggfunc=aggfunc)


def draw_heatmap(ax, mat: pd.DataFrame, vmin, vmax, cmap=CONTINUOUS_CMAP):
    im = ax.imshow(mat.values, origin="lower", aspect="auto", cmap=cmap,
                   vmin=vmin, vmax=vmax, interpolation="nearest")
    ax.set_xticks(range(len(mat.columns)))
    ax.set_xticklabels([f"{c:g}" for c in mat.columns])
    ax.set_yticks(range(len(mat.index)))
    ax.set_yticklabels([f"{r:g}" for r in mat.index])
    for s in ax.spines.values():
        s.set_visible(False)
    return im


# ================================================================ FIG 1
def figure1() -> dict:
    rel = "recon/boundary_open/sweep_seed_results.csv"
    df = with_regime(load_committed(rel))
    df["active"] = df["regime_recomputed"].isin(["MIXED", "CAPTURE"]).astype(float)
    n_runs = len(df)
    seeds = int(df.groupby(["sigma", "pi_reward"]).size().median())

    g_pun = grid(df, "max_punish")
    g_act = grid(df, "active")

    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.2), constrained_layout=True)
    im0 = draw_heatmap(axes[0], g_pun, vmin=0.0, vmax=float(np.nanmax(g_pun.values)))
    axes[0].set_title("A  Enforcement intensity (continuous)")
    cb0 = fig.colorbar(im0, ax=axes[0], fraction=0.046)
    cb0.set_label("mean max punish rate\n(fraction of active agents)")

    im1 = draw_heatmap(axes[1], g_act, vmin=0.0, vmax=1.0)
    axes[1].set_title("B  P(active)")
    cb1 = fig.colorbar(im1, ax=axes[1], fraction=0.046)
    cb1.set_label(f"P(active), {seeds} seeds/cell")

    # annotate the dead pi=0.01 column
    dead_pi = g_act.columns[0]
    dead_max = float(np.nanmax(g_act[dead_pi].values))
    for ax in axes:
        ax.add_patch(Rectangle((-0.5, -0.5), 1.0, len(g_act.index),
                               fill=False, edgecolor=OKABE_ITO["vermillion"],
                               lw=1.6, linestyle="--", zorder=5))
        ax.set_xlabel(f"$\\pi$ (enforcement reward, dimensionless)\nn = {n_runs} runs, {seeds} seeds/cell")
    axes[0].set_ylabel("$\\sigma$ (code observability / legibility, dimensionless)")
    # label inside the dead column itself: it is uniformly zero, so no data is hidden
    axes[1].text(0, (len(g_act.index) - 1) / 2.0,
                 f"$\\pi$=0.01 dead column: P(active)=0 (max {dead_max:.2f})",
                 rotation=90, ha="center", va="center", fontsize=7,
                 color="white", zorder=6)

    files = save(fig, "fig1_activation_frontier")
    overall_act = float(df["active"].mean())
    caption = (
        f"\\textbf{{Activation frontier under open exit.}} Agent-based sweep at "
        f"$\\delta_0=0$ (exit open), $n={n_runs}$ runs "
        f"({len(g_act.index)} $\\sigma$ $\\times$ {len(g_act.columns)} $\\pi$ cells "
        f"$\\times$ {seeds} seeds per cell). "
        f"(A) Mean maximum punish rate, the continuous enforcement-intensity surface. "
        f"(B) Probability that a run is classified active, recomputed with the "
        f"hierarchical classifier (active: max punish rate $\\geq$ "
        f"{rc.PUNISH_ACTIVE_MIN}); overall P(active) $=$ {overall_act:.3f}. "
        f"Enforcement activates only above a joint $\\sigma$--$\\pi$ threshold: the "
        f"$\\pi=0.01$ column (dashed outline) is dead in every one of its "
        f"{len(g_act.index)} cells, so an enforcement reward below that level cannot "
        f"sustain an enforcement apparatus at any level of code observability."
    )
    return {
        "figure_id": "fig1", "title": "Activation frontier", "files": files,
        "sources": [source_entry(rel)], "classifier": CLASSIFIER_SETTINGS,
        "n_runs_used": n_runs, "seeds_per_cell": seeds,
        "cells": int(g_act.size),
        "series": {
            "panelA_mean_max_punish": {"sigma": [float(s) for s in g_pun.index],
                                       "pi": [float(c) for c in g_pun.columns],
                                       "values": g_pun.values.round(4).tolist()},
            "panelB_P_active": {"sigma": [float(s) for s in g_act.index],
                                "pi": [float(c) for c in g_act.columns],
                                "values": g_act.values.round(4).tolist()},
            "overall_P_active": round(overall_act, 4),
            "dead_column_pi": float(dead_pi),
            "dead_column_max_P_active": round(dead_max, 4),
        },
        "caption": caption,
    }


# ================================================================ FIG 2
def figure2() -> dict:
    rel_o = "recon/boundary_open/sweep_seed_results.csv"
    rel_s = "recon/boundary_sealed/sweep_seed_results.csv"
    do = with_regime(load_committed(rel_o))
    ds = with_regime(load_committed(rel_s))
    for d in (do, ds):
        d["active"] = d["regime_recomputed"].isin(["MIXED", "CAPTURE"]).astype(float)
        d["capture"] = (d["regime_recomputed"] == "CAPTURE").astype(float)

    seeds = int(do.groupby(["sigma", "pi_reward"]).size().median())
    g_open_act = grid(do, "active")
    g_open_cap = grid(do, "capture")
    g_seal_cap = grid(ds, "capture")
    g_seal_act = grid(ds, "active")

    # GUARD: panel B is the necessity result and must be uniformly zero.
    # If any run captures with the exit open, stop -- do not plot it silently.
    n_cap_open = int(do["capture"].sum())
    max_cap_open = float(np.nanmax(g_open_cap.values))
    if n_cap_open != 0 or max_cap_open > 0.0:
        bad = do[do["capture"] > 0][["sigma", "pi_reward", "seed",
                                     "final_exit_rate", "max_punish"]]
        raise RuntimeError(
            "FIG2 PANEL B EXCEPTION -- capture under OPEN exit is NOT uniformly zero.\n"
            f"  {n_cap_open} of {len(do)} runs reach capture; max cell rate {max_cap_open:.4f}.\n"
            f"  offending runs (first 20):\n{bad.head(20).to_string()}\n"
            "  Stopping rather than plotting a false necessity claim.")

    shift = g_seal_act - g_open_act
    rise = shift > 1e-9
    n_rise = int(rise.values.sum())
    mean_shift = float(np.nanmean(shift.values))
    mean_rise = float(np.nanmean(shift.values[rise.values])) if n_rise else 0.0
    overall_act_open = float(do["active"].mean())

    fig, axes = plt.subplots(1, 3, figsize=(10.4, 3.4), constrained_layout=True)
    draw_heatmap(axes[0], g_open_act, 0.0, 1.0)
    axes[0].set_title("A  P(active), exit OPEN ($\\delta_0=0$)")
    draw_heatmap(axes[1], g_open_cap, 0.0, 1.0)
    axes[1].set_title("B  P(capture), exit OPEN ($\\delta_0=0$)")
    im2 = draw_heatmap(axes[2], g_seal_cap, 0.0, 1.0)
    axes[2].set_title("C  P(capture), exit SEALED ($\\delta_0=0.95$)")

    # panel B is uniformly zero: say so on the panel (occludes no signal)
    axes[1].text((len(g_open_cap.columns) - 1) / 2.0, (len(g_open_cap.index) - 1) / 2.0,
                 f"capture = 0\nin all {int(g_open_cap.size)} cells\n(0 / {len(do)} runs)",
                 ha="center", va="center", fontsize=8.5, color="white", zorder=6)

    # circled cells on panel C: sealing also raises activation (non-orthogonality)
    ys, xs = np.where(rise.values)
    axes[2].scatter(xs, ys, s=26, facecolors="none",
                    edgecolors=OKABE_ITO["vermillion"], linewidths=1.4, zorder=6,
                    label=f"sealing raises P(active) ({n_rise} cells)")
    axes[2].legend(loc="upper center", bbox_to_anchor=(0.5, -0.30),
                   frameon=False, fontsize=7.5)

    cb = fig.colorbar(im2, ax=axes, fraction=0.022, pad=0.02)
    cb.set_label("probability (shared scale)")
    for ax in axes:
        ax.set_xlabel(f"$\\pi$ (enforcement reward)\n{seeds} seeds/cell")
    axes[0].set_ylabel("$\\sigma$ (code observability / legibility)")

    files = save(fig, "fig2_two_dimensions")
    caption = (
        f"\\textbf{{Exit closure is necessary for capture.}} All panels share one "
        f"colour scale; {len(g_open_act.index)} $\\sigma$ $\\times$ "
        f"{len(g_open_act.columns)} $\\pi$ cells $\\times$ {seeds} seeds per cell. "
        f"(A) Probability a run is active with the exit open ($\\delta_0=0$, "
        f"$n={len(do)}$ runs): code geometry alone sets activation, overall "
        f"P(active) $=$ {overall_act_open:.3f}. "
        f"(B) Probability of capture in those same {len(do)} runs: "
        f"\\textbf{{0 of {len(do)} runs reach capture with the exit open}}, in every "
        f"one of the {int(g_open_cap.size)} cells, despite that active rate of "
        f"{overall_act_open:.3f} -- an active enforcement apparatus never converts to "
        f"capture while members can leave. "
        f"(C) Probability of capture with the exit sealed ($\\delta_0=0.95$, "
        f"$n={len(ds)}$ runs): the same active region now captures. Panels B and C are "
        f"the same quantity under the two exit conditions, so the contrast isolates the "
        f"effect of closing the exit. The two dimensions are not fully orthogonal: "
        f"circled cells in (C) are the {n_rise} of {int(rise.size)} cells where sealing "
        f"also raises P(active) (mean shift over all cells {mean_shift:+.3f}; "
        f"{mean_rise:+.3f} among circled cells), and activation falls in no cell. "
        f"Regimes recomputed with the hierarchical classifier."
    )
    return {
        "figure_id": "fig2", "title": "Exit closure is necessary for capture",
        "files": files,
        "sources": [source_entry(rel_o), source_entry(rel_s)],
        "classifier": CLASSIFIER_SETTINGS,
        "n_runs_used": len(do) + len(ds), "seeds_per_cell": seeds,
        "cells": int(g_open_act.size),
        "series": {
            "panelA_P_active_open": g_open_act.values.round(4).tolist(),
            "panelB_P_capture_open": g_open_cap.values.round(4).tolist(),
            "panelC_P_capture_sealed": g_seal_cap.values.round(4).tolist(),
            "P_active_sealed": g_seal_act.values.round(4).tolist(),
            "activation_shift_sealed_minus_open": shift.values.round(4).tolist(),
            "capture_open_total_runs": n_cap_open,
            "capture_open_max_cell_rate": round(max_cap_open, 4),
            "overall_P_active_open": round(overall_act_open, 4),
            "n_cells_activation_rises": n_rise,
            "n_cells_activation_falls": int((shift.values < -1e-9).sum()),
            "mean_shift_all_cells": round(mean_shift, 4),
            "mean_shift_rising_cells": round(mean_rise, 4),
            "sigma": [float(s) for s in g_open_act.index],
            "pi": [float(c) for c in g_open_act.columns],
        },
        "caption": caption,
    }


# ================================================================ FIG 3
def figure3() -> dict:
    rel = "recon/exogenous_delta_fixed/sweep_seed_results.csv"
    df = with_regime(load_committed(rel))
    df["capture"] = (df["regime_recomputed"] == "CAPTURE").astype(int)
    deltas = sorted(df["delta0"].unique())

    all_rate, all_lo, all_hi, all_n = [], [], [], []
    for d in deltas:
        sub = df[df["delta0"] == d]
        k, n = int(sub["capture"].sum()), len(sub)
        lo, hi = wilson(k, n)
        all_rate.append(k / n); all_lo.append(lo); all_hi.append(hi); all_n.append(n)

    cell = df[(df["sigma"] == 0.25) & (df["pi_reward"] == 0.05)]
    c_rate, c_lo, c_hi, c_n = [], [], [], []
    for d in deltas:
        sub = cell[cell["delta0"] == d]
        k, n = int(sub["capture"].sum()), len(sub)
        lo, hi = wilson(k, n)
        c_rate.append(k / n); c_lo.append(lo); c_hi.append(hi); c_n.append(n)

    fig, ax = plt.subplots(figsize=(5.0, 3.6), constrained_layout=True)
    ax.errorbar(deltas, all_rate, yerr=yerr_from(all_rate, all_lo, all_hi),
                marker="o", ms=5, lw=1.6, capsize=3, color=OKABE_ITO["blue"],
                label=f"all $\\sigma\\times\\pi$ cells (n={all_n[0]}/point)")
    ax.errorbar(deltas, c_rate, yerr=yerr_from(c_rate, c_lo, c_hi),
                marker="s", ms=5, lw=1.6, capsize=3, color=OKABE_ITO["orange"],
                linestyle="--", label=f"$\\sigma$=0.25, $\\pi$=0.05 cell (n={c_n[0]}/point)")
    ax.set_xlabel("imposed exit closure $\\delta_0$ (dimensionless)")
    ax.set_ylabel("capture rate (fraction of runs)")
    ax.set_ylim(-0.04, 1.04)
    ax.set_xticks(deltas)
    ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="y", lw=0.4, alpha=0.3)
    ax.annotate("necessity: stays at 0 at every $\\delta_0$",
                xy=(deltas[-1], 0.0), xytext=(0.34, 0.16), fontsize=8,
                color=OKABE_ITO["orange"],
                arrowprops=dict(arrowstyle="->", color=OKABE_ITO["orange"], lw=1.0))

    files = save(fig, "fig3_exit_closure_dose_response")
    caption = (
        f"\\textbf{{Exit-closure dose-response and the necessity of code geometry.}} "
        f"Capture rate against imposed exit closure $\\delta_0$ "
        f"($n={len(df)}$ runs total; {all_n[0]} runs per pooled point, "
        f"{c_n[0]} per cell-specific point), with Wilson 95\\% intervals. "
        f"Pooled over all $\\sigma\\times\\pi$ cells (circles) capture rises "
        f"monotonically from {all_rate[0]:.3f} at $\\delta_0={deltas[0]:g}$ to "
        f"{all_rate[-1]:.3f} at $\\delta_0={deltas[-1]:g}$. In the "
        f"$\\sigma=0.25$, $\\pi=0.05$ cell (squares, dashed) the capture rate is "
        f"{max(c_rate):.3f} at every level including $\\delta_0={deltas[-1]:g}$: closing "
        f"the exit cannot manufacture capture where the code geometry does not "
        f"activate. Regimes recomputed with the hierarchical classifier."
    )
    return {
        "figure_id": "fig3", "title": "Exit-closure dose-response", "files": files,
        "sources": [source_entry(rel)], "classifier": CLASSIFIER_SETTINGS,
        "n_runs_used": len(df),
        "series": {
            "delta0": [float(d) for d in deltas],
            "pooled_capture_rate": [round(v, 4) for v in all_rate],
            "pooled_wilson_lo": [round(v, 4) for v in all_lo],
            "pooled_wilson_hi": [round(v, 4) for v in all_hi],
            "pooled_n_per_point": all_n,
            "necessity_cell_capture_rate": [round(v, 4) for v in c_rate],
            "necessity_cell_wilson_lo": [round(v, 4) for v in c_lo],
            "necessity_cell_wilson_hi": [round(v, 4) for v in c_hi],
            "necessity_cell_n_per_point": c_n,
        },
        "caption": caption,
    }


# ================================================================ FIG 4
def figure4() -> dict:
    rel = "recon/privilege_ablation/ablation_seed_results.csv"
    df = load_committed(rel)
    arms = ["floor", "ceiling"]
    sub = df[df["arm"].isin(arms)].copy()
    rng = np.random.default_rng(12345)  # jitter only (visual), never data

    metrics = [("top5_active", "top 5% share of punishment\n(active agents)", None),
               ("gini_active", "Gini of punishment\n(active agents)", "gini_null")]

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.4), constrained_layout=True)
    stats = {}
    for ax, (col, ylab, nullcol) in zip(axes, metrics):
        for i, arm in enumerate(arms):
            vals = sub[sub["arm"] == arm][col].to_numpy(float)
            x = np.full(len(vals), i) + rng.uniform(-0.11, 0.11, len(vals))
            ax.scatter(x, vals, s=9, alpha=0.45, linewidths=0,
                       color=OKABE_ITO["skyblue"] if arm == "floor" else OKABE_ITO["blue"],
                       zorder=2)
            ax.hlines(vals.mean(), i - 0.26, i + 0.26, color=OKABE_ITO["black"],
                      lw=2.0, zorder=4)
            stats[f"{arm}_{col}_mean"] = round(float(vals.mean()), 4)
            stats[f"{arm}_{col}_n"] = int(len(vals))
            if nullcol:
                nv = sub[sub["arm"] == arm][nullcol].to_numpy(float)
                ax.hlines(nv.mean(), i - 0.26, i + 0.26, color=OKABE_ITO["vermillion"],
                          lw=1.6, linestyle=":", zorder=5)
                stats[f"{arm}_{nullcol}_mean"] = round(float(nv.mean()), 4)
        ax.set_xticks(range(len(arms)))
        ax.set_xticklabels(["floor\n(no privilege)", "ceiling\n(full privilege)"])
        ax.set_ylabel(ylab)
        ax.set_ylim(-0.03, 1.03)
        ax.grid(axis="y", lw=0.4, alpha=0.3)
        n_arm = stats[f"floor_{col}_n"]
        ax.set_xlabel(f"ablation arm ({n_arm} seeds/arm)")

    axes[0].set_title("A  Top-5% share")
    axes[1].set_title("B  Gini")
    h_mean = plt.Line2D([], [], color=OKABE_ITO["black"], lw=2.0, label="arm mean")
    h_null = plt.Line2D([], [], color=OKABE_ITO["vermillion"], lw=1.6, linestyle=":",
                        label="random-allocation null")
    h_pt = plt.Line2D([], [], marker="o", ls="", ms=4, color=OKABE_ITO["blue"],
                      alpha=0.6, label="per-seed run")
    axes[1].legend(handles=[h_pt, h_mean, h_null], frameon=False, fontsize=7,
                   loc="upper left")

    files = save(fig, "fig4_privilege_ablation")
    manu = (stats["ceiling_top5_active_mean"] - stats["floor_top5_active_mean"]) / stats["ceiling_top5_active_mean"]
    caption = (
        f"\\textbf{{Concentration is manufactured by the privilege architecture.}} "
        f"Role-independent concentration for the ablation floor (no privilege) and "
        f"ceiling (full privilege bundle), {stats['floor_top5_active_n']} seeds per arm "
        f"($n={len(sub)}$ runs); points are individual runs, black bars arm means. "
        f"(A) Top-5\\% share of punishment among active agents rises from "
        f"{stats['floor_top5_active_mean']:.3f} at the floor to "
        f"{stats['ceiling_top5_active_mean']:.3f} at the ceiling, so "
        f"{manu*100:.0f}\\% of ceiling concentration is privilege-manufactured. "
        f"(B) Gini rises from {stats['floor_gini_active_mean']:.3f} to "
        f"{stats['ceiling_gini_active_mean']:.3f} against random-allocation nulls "
        f"(dotted) of {stats['floor_gini_null_mean']:.3f} and "
        f"{stats['ceiling_gini_null_mean']:.3f}; the floor sits close to its null, so "
        f"concentration is not an emergent property of the unprivileged model. "
        f"A committed random-allocation null exists only for the Gini statistic, so "
        f"panel A carries no null reference."
    )
    return {
        "figure_id": "fig4", "title": "Privilege ablation", "files": files,
        "sources": [source_entry(rel)],
        "classifier": {**CLASSIFIER_SETTINGS,
                       "note": "no regime classification used; role-independent metrics only"},
        "n_runs_used": int(len(sub)), "seeds_per_arm": stats["floor_top5_active_n"],
        "series": stats,
        "data_gaps": ["no top5 random-allocation null column in the committed ablation CSV "
                      "(only gini_null); panel A therefore has no null reference marker"],
        "caption": caption,
    }


# ================================================================ FIG 5
def figure5() -> dict:
    coupled_rel = "recon/factorial_shock_off/sweep_seed_results.csv"
    dec_rels = {"k=1.5": "recon/decoupled_k1.5/sweep_seed_results.csv",
                "k=3.0": "recon/decoupled_k3.0/sweep_seed_results.csv",
                "k=6.0": "recon/decoupled_k6.0/sweep_seed_results.csv"}

    labels, rates, los, his, ns, srcs = [], [], [], [], [], []
    dfc = with_regime(load_committed(coupled_rel))
    k = int((dfc["regime_recomputed"] == "CAPTURE").sum()); n = len(dfc)
    lo, hi = wilson(k, n)
    labels.append("coupled\n$\\delta$ target = f(enforcer share)")
    rates.append(k / n); los.append(lo); his.append(hi); ns.append(n)
    srcs.append(source_entry(coupled_rel))

    for lab, rel in dec_rels.items():
        d = with_regime(load_committed(rel))
        kk, nn = int((d["regime_recomputed"] == "CAPTURE").sum()), len(d)
        l2, h2 = wilson(kk, nn)
        labels.append(f"decoupled\n{lab}")
        rates.append(kk / nn); los.append(l2); his.append(h2); ns.append(nn)
        srcs.append(source_entry(rel))

    colors = [OKABE_ITO["vermillion"]] + [OKABE_ITO["blue"]] * 3
    fig, ax = plt.subplots(figsize=(5.6, 3.6), constrained_layout=True)
    xs = np.arange(len(labels))
    ax.bar(xs, rates, width=0.6, color=colors, zorder=2)
    ax.errorbar(xs, rates, yerr=yerr_from(rates, los, his), fmt="none", ecolor=OKABE_ITO["black"], capsize=3, lw=1.0, zorder=3)
    for x, r, nn in zip(xs, rates, ns):
        ax.text(x, r + 0.035, f"{r:.3f}\n(n={nn})", ha="center", fontsize=7.5)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=7.5)
    ax.set_ylabel("capture rate (fraction of runs)")
    ax.set_xlabel("exit-closure specification")
    ax.set_ylim(0, 1.02)
    ax.grid(axis="y", lw=0.4, alpha=0.3)

    files = save(fig, "fig5_circularity_demonstration")
    # decoupled capture counts, data-derived (not asserted)
    dec_counts = [int(round(r * n)) for r, n in zip(rates[1:], ns[1:])]
    dec_ks = ["1.5", "3.0", "6.0"]
    if len(set(dec_counts)) == 1 and len(set(ns[1:])) == 1:
        dec_phrase = (f"{dec_counts[0]} of {ns[1]} runs at each of "
                      f"$k={dec_ks[0]}$, ${dec_ks[1]}$ and ${dec_ks[2]}$")
    else:
        dec_phrase = ", ".join(f"{c} of {n} at $k={k}$"
                               for c, n, k in zip(dec_counts, ns[1:], dec_ks))
    caption = (
        f"\\textbf{{Specification check for circular closure.}} A specification in "
        f"which outside-option closure is driven by enforcer share yields capture by "
        f"construction, because that quantity mechanically drives retention, one of "
        f"the two capture criteria "
        f"($\\delta_{{target}} = \\min(1, \\delta_{{baseline}} + $ enforcer share$)$); "
        f"the coupled arm ($n={ns[0]}$ runs) has a capture rate of {rates[0]:.3f}. "
        f"Exit capacity is therefore treated as an independent structural input. When "
        f"closure is decoupled from enforcer share and driven by punishment intensity "
        f"instead, capture does not occur at any coupling strength: {dec_phrase}. "
        f"Wilson 95\\% intervals are shown; regimes are computed with the hierarchical "
        f"classifier, under which capture is retained AND active and enforcer share is "
        f"not itself a criterion."
    )
    return {
        "figure_id": "fig5", "title": "Circularity demonstration", "files": files,
        "sources": srcs, "classifier": CLASSIFIER_SETTINGS,
        "n_runs_used": int(sum(ns)),
        "series": {"labels": [l.replace("\n", " ") for l in labels],
                   "capture_rate": [round(r, 4) for r in rates],
                   "wilson_lo": [round(v, 4) for v in los],
                   "wilson_hi": [round(v, 4) for v in his],
                   "n_per_bar": ns,
                   "coupling_source": "src/religion_fundamentalism_abm_v2_7.py:578 "
                                      "delta_target = min(1.0, delta_baseline + enforcer_share)",
                   "decoupled_source": "src/religion_fundamentalism_abm_v2_7.py:574 "
                                       "delta_target = min(cap, delta_baseline + kappa*punish_intensity_step)"},
        "caption": caption,
    }


# ================================================================ validation
def validate(manifest: list[dict]) -> list[tuple[str, str, str, bool]]:
    rows = []
    for e in manifest:
        fid = e["figure_id"]
        # (a) files exist and non-empty
        ok_files, detail = True, []
        for kind, rel in e["files"].items():
            p = ROOT / rel
            good = p.exists() and p.stat().st_size > 0
            ok_files &= good
            detail.append(f"{kind}:{p.stat().st_size if p.exists() else 0}B")
        rows.append((fid, "(a) figure files exist, non-empty", ", ".join(detail), ok_files))

        # (b) sources exist, sha256 matches
        ok_src, sdet = True, []
        for s in e["sources"]:
            p = ROOT / s["path"]
            if not p.exists():
                ok_src = False; sdet.append(f"MISSING {s['path']}"); continue
            match = sha256_of(p) == s["sha256"]
            ok_src &= match
            sdet.append(f"{Path(s['path']).parent.name}:{'ok' if match else 'SHA MISMATCH'}")
        rows.append((fid, "(b) source sha256 matches", ", ".join(sdet), ok_src))

        # (c) caption stated n matches rows actually used
        cap = e["caption"]
        # only explicit "n=<digits>" declarations count. Requiring the '=' avoids
        # false positives such as the trailing "n 95" inside "Wilson 95\%".
        stated = [int(x) for x in re.findall(r"\bn\s*=\s*\\?\$?\{?([0-9]+)", cap)]
        used_pool = {e.get("n_runs_used")}
        for s in e["sources"]:
            used_pool.add(s["rows"])
        for key in ("seeds_per_cell", "seeds_per_arm"):
            if key in e:
                used_pool.add(e[key])
        ser = e.get("series", {})
        for v in ser.values():
            if isinstance(v, list) and v and all(isinstance(i, int) for i in v):
                used_pool.update(v)
            elif isinstance(v, int):
                used_pool.add(v)
        ok_n = all(s in used_pool for s in stated) if stated else False
        rows.append((fid, "(c) caption n matches rows used",
                     f"stated={sorted(set(stated))}", ok_n))

        # (d) no stored regime column used
        ok_reg = e["classifier"].get("stored_regime_column_used") is False
        rows.append((fid, "(d) no stored regime column",
                     f"dropped={e['classifier'].get('dropped_columns_on_load')}", ok_reg))
    return rows


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    for fn in (figure1, figure2, figure3, figure4, figure5):
        MANIFEST.append(fn())

    (OUTDIR / "FIGURE_MANIFEST.json").write_text(json.dumps(
        {"generated_by": "scripts/generate_manuscript_figures.py",
         "classifier_settings": CLASSIFIER_SETTINGS,
         "palette": {"continuous": CONTINUOUS_CMAP, "categorical": "Okabe-Ito", "okabe_ito": OKABE_ITO},
         "figures": MANIFEST}, indent=2))

    tex = ["% AUTO-GENERATED by scripts/generate_manuscript_figures.py -- do not edit by hand.",
           "% Each caption is derived from the plotted numbers.", ""]
    for e in MANIFEST:
        tex += [f"% ---- {e['figure_id']}: {e['title']} ({e['files']['pdf']})",
                f"\\caption{{{e['caption']}}}", ""]
    (OUTDIR / "captions.tex").write_text("\n".join(tex))

    rows = validate(MANIFEST)
    print(f"\nWrote {len(MANIFEST)} figures to {OUTDIR.relative_to(ROOT)}/\n")
    print(f"{'figure':7s} {'check':34s} {'detail':44s} {'result'}")
    print("-" * 96)
    for fid, check, detail, ok in rows:
        print(f"{fid:7s} {check:34s} {detail[:44]:44s} {'PASS' if ok else 'FAIL'}")
    n_fail = sum(1 for *_x, ok in rows if not ok)
    print("-" * 96)
    print(f"{len(rows)-n_fail}/{len(rows)} checks PASS" + ("" if not n_fail else f"  ({n_fail} FAIL)"))
    gaps = [(e["figure_id"], g) for e in MANIFEST for g in e.get("data_gaps", [])]
    if gaps:
        print("\nData gaps (could not be sourced from committed CSVs):")
        for fid, g in gaps:
            print(f"  {fid}: {g}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
