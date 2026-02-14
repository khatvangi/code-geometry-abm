#!/usr/bin/env python3
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def parse_context(path: Path) -> dict:
    parts = path.parts
    sigma = np.nan
    seed = np.nan
    suite = None

    for i, part in enumerate(parts):
        if part in {"sigma_sweep", "sigma_refine"}:
            suite = part
        if part.startswith("sigma_"):
            try:
                sigma = float(part.split("_", 1)[1])
            except ValueError:
                pass
        if part.startswith("seed_"):
            try:
                seed = int(part.split("_", 1)[1])
            except ValueError:
                pass

    return {"suite": suite, "sigma": sigma, "seed": seed}


def gini_nonneg(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    if x.size == 0:
        return 0.0
    if np.allclose(x, 0.0):
        return 0.0
    x = np.sort(np.clip(x, 0.0, None))
    n = x.size
    cum = np.cumsum(x)
    return float((n + 1 - 2 * np.sum(cum) / cum[-1]) / n)


def top_share(values: np.ndarray, frac: float) -> float:
    vals = np.asarray(values, dtype=float)
    total = float(vals.sum())
    if total <= 0.0:
        return 0.0
    k = max(1, int(np.ceil(frac * vals.size)))
    top = np.sort(vals)[-k:].sum()
    return float(top / total)


def lorenz_curve(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    vals = np.sort(np.clip(np.asarray(values, dtype=float), 0.0, None))
    if vals.size == 0:
        return np.array([0.0, 1.0]), np.array([0.0, 1.0])
    total = vals.sum()
    x = np.linspace(0.0, 1.0, vals.size + 1)
    if total <= 0:
        y = np.zeros(vals.size + 1)
        y[-1] = 1.0
        return x, y
    y = np.concatenate([[0.0], np.cumsum(vals) / total])
    return x, y


def first_sigma_over(curve: pd.DataFrame, col: str, threshold: float) -> float | None:
    if curve.empty:
        return None
    c = curve.sort_values("sigma")
    m = c[col] > threshold
    if not m.any():
        return None
    return float(c.loc[m, "sigma"].iloc[0])


def choose_nearest(existing: np.ndarray, target: float) -> float | None:
    if existing.size == 0:
        return None
    idx = int(np.argmin(np.abs(existing - target)))
    return float(existing[idx])


def fmt(v: float | None) -> str:
    return "n/a" if v is None or np.isnan(v) else f"{v:.3f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Root does not exist: {root}")

    summary_dir = root / "summary"
    plots_dir = summary_dir / "plots"
    summary_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    all_values_by_sigma: dict[float, list[np.ndarray]] = {}

    for path in sorted(root.rglob("agent_summary.csv")):
        df = pd.read_csv(path)
        if df.empty or "punish_issued" not in df.columns:
            continue

        punish = df["punish_issued"].to_numpy(dtype=float)
        total = float(punish.sum())
        ctx = parse_context(path)

        spearman_degree = np.nan
        if "degree" in df.columns and df["degree"].nunique() > 1 and df["punish_issued"].nunique() > 1:
            spearman_degree = float(df["degree"].corr(df["punish_issued"], method="spearman"))

        spearman_bet = np.nan
        if "betweenness" in df.columns:
            bet = df["betweenness"]
            if bet.notna().sum() > 1 and bet.nunique(dropna=True) > 1 and df["punish_issued"].nunique() > 1:
                spearman_bet = float(bet.corr(df["punish_issued"], method="spearman"))

        row = {
            "agent_summary_path": str(path),
            "suite": ctx["suite"],
            "sigma": ctx["sigma"],
            "seed": ctx["seed"],
            "n_agents": int(df.shape[0]),
            "total_punishments": total,
            "top1_share": top_share(punish, 0.01),
            "top5_share": top_share(punish, 0.05),
            "top10_share": top_share(punish, 0.10),
            "gini_punish_issued": gini_nonneg(punish),
            "spearman_degree_vs_punish": spearman_degree,
            "spearman_betweenness_vs_punish": spearman_bet,
        }
        rows.append(row)

        sigma = row["sigma"]
        if not np.isnan(sigma):
            all_values_by_sigma.setdefault(float(sigma), []).append(punish)

    if not rows:
        raise RuntimeError("No agent_summary.csv files found with punish_issued data")

    out_df = pd.DataFrame(rows)
    out_path = summary_dir / "enforcement_concentration.csv"
    out_df.to_csv(out_path, index=False)

    # Plot: concentration by sigma (top5 share)
    sigma_df = out_df.dropna(subset=["sigma"]).copy()
    if not sigma_df.empty:
        grp = (
            sigma_df.groupby("sigma", as_index=False)
            .agg(top5_mean=("top5_share", "mean"), top5_sd=("top5_share", "std"), n_runs=("top5_share", "size"))
            .sort_values("sigma")
        )

        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.errorbar(grp["sigma"], grp["top5_mean"], yerr=grp["top5_sd"].fillna(0.0), marker="o", capsize=2)
        ax.set_xlabel("sigma")
        ax.set_ylabel("top 5% punishment share (mean +/- sd)")
        ax.set_title("Enforcement Concentration by Sigma")
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(plots_dir / "concentration_by_sigma.png", dpi=170)
        plt.close(fig)

    # Plot: Lorenz curve for high sigma regime
    high_vals = []
    for sigma, arrs in all_values_by_sigma.items():
        if abs(sigma - 0.80) < 1e-9:
            for arr in arrs:
                high_vals.extend(arr.tolist())
    if high_vals:
        x, y = lorenz_curve(np.asarray(high_vals, dtype=float))
        fig, ax = plt.subplots(figsize=(5.5, 5.5))
        ax.plot(x, y, label="High sigma (0.80)")
        ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Equality")
        ax.set_xlabel("Cumulative share of agents")
        ax.set_ylabel("Cumulative share of punishments")
        ax.set_title("Lorenz Curve of Punishment Issuance")
        ax.legend()
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(plots_dir / "lorenz_high_sigma.png", dpi=170)
        plt.close(fig)

    # Load sigma curves (prefer refined for thresholds if available)
    curve_ref = summary_dir / "sigma_refine_curve.csv"
    curve_coarse = summary_dir / "sigma_curve.csv"
    curve = pd.read_csv(curve_ref) if curve_ref.exists() else pd.read_csv(curve_coarse)
    sigma_star_02 = first_sigma_over(curve, "fund_prevalence_mean", 0.2)
    sigma_star_05 = first_sigma_over(curve, "fund_prevalence_mean", 0.5)

    width = None
    if sigma_star_02 is not None and sigma_star_05 is not None:
        width = max(0.0, sigma_star_05 - sigma_star_02)

    # Regime stats for required sigma points.
    existing = np.array(sorted(sigma_df["sigma"].dropna().unique())) if not sigma_df.empty else np.array([])
    target_specs = [("low_sigma", 0.15), ("high_sigma", 0.80)]
    if sigma_star_05 is not None:
        target_specs.extend(
            [
                ("sigma_star_minus_0p02", max(0.0, round(sigma_star_05 - 0.02, 2))),
                ("sigma_star", round(sigma_star_05, 2)),
                ("sigma_star_plus_0p02", min(1.0, round(sigma_star_05 + 0.02, 2))),
            ]
        )

    regime_rows = []
    for label, target in target_specs:
        chosen = choose_nearest(existing, target)
        if chosen is None:
            regime_rows.append({"label": label, "target_sigma": target, "chosen_sigma": np.nan})
            continue
        sub = sigma_df[np.isclose(sigma_df["sigma"], chosen)]
        regime_rows.append(
            {
                "label": label,
                "target_sigma": target,
                "chosen_sigma": chosen,
                "n_runs": int(sub.shape[0]),
                "top5_share_mean": float(sub["top5_share"].mean()),
                "top5_share_sd": float(sub["top5_share"].std(ddof=1)) if sub.shape[0] > 1 else 0.0,
                "gini_mean": float(sub["gini_punish_issued"].mean()),
                "gini_sd": float(sub["gini_punish_issued"].std(ddof=1)) if sub.shape[0] > 1 else 0.0,
                "punishments_mean": float(sub["total_punishments"].mean()),
                "spearman_degree_mean": float(sub["spearman_degree_vs_punish"].mean()),
            }
        )

    regime_df = pd.DataFrame(regime_rows)
    regime_path = summary_dir / "enforcement_regime_stats.csv"
    regime_df.to_csv(regime_path, index=False)

    # Build RESULTS_V1.md
    lines: list[str] = []
    lines.append("# RESULTS V1")
    lines.append("")
    lines.append(f"Batch root: `{root}`")
    lines.append("")
    lines.append("## Sigma Phase Diagram")
    lines.append(f"- Estimated sigma* (fund_prevalence > 0.2): {fmt(sigma_star_02)}")
    lines.append(f"- Estimated sigma* (fund_prevalence > 0.5): {fmt(sigma_star_05)}")
    if width is None:
        lines.append("- Transition width (sigma*_0.5 - sigma*_0.2): n/a")
        lines.append("- Sharp transition (< 0.05 width): n/a")
    else:
        lines.append(f"- Transition width (sigma*_0.5 - sigma*_0.2): {width:.3f}")
        lines.append(f"- Sharp transition (< 0.05 width): {'yes' if width < 0.05 else 'no'}")

    lines.append("")
    lines.append("## Enforcement Concentration")
    if not regime_df.empty:
        for _, r in regime_df.iterrows():
            if pd.isna(r.get("chosen_sigma", np.nan)):
                lines.append(f"- {r['label']}: no matching runs.")
                continue
            lines.append(
                f"- {r['label']} (sigma={r['chosen_sigma']:.2f}, n={int(r['n_runs'])}): "
                f"top5 share={r['top5_share_mean']:.3f}, gini={r['gini_mean']:.3f}, "
                f"mean total punishments={r['punishments_mean']:.1f}."
            )

    high = regime_df[regime_df["label"] == "high_sigma"]
    minority_drives = None
    if not high.empty and not pd.isna(high["top5_share_mean"].iloc[0]):
        minority_drives = float(high["top5_share_mean"].iloc[0]) > 0.30
    lines.append(
        f"- Minority-drives criterion (top 5% share > 0.30 in high sigma): "
        f"{'yes' if minority_drives else ('no' if minority_drives is not None else 'n/a')}."
    )

    lines.append("")
    lines.append("## Outputs")
    lines.append(f"- `summary/sigma_curve.csv`")
    if (summary_dir / "sigma_refine_curve.csv").exists():
        lines.append(f"- `summary/sigma_refine_curve.csv`")
    lines.append(f"- `summary/enforcement_concentration.csv`")
    lines.append(f"- `summary/enforcement_regime_stats.csv`")
    lines.append(f"- `summary/plots/sigma_vs_prevalence.png`")
    lines.append(f"- `summary/plots/sigma_vs_punishrate.png`")
    lines.append(f"- `summary/plots/concentration_by_sigma.png`")
    lines.append(f"- `summary/plots/lorenz_high_sigma.png`")

    results_path = summary_dir / "RESULTS_V1.md"
    results_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {out_path}")
    print(f"Wrote {regime_path}")
    print(f"Wrote {results_path}")


if __name__ == "__main__":
    main()
