#!/usr/bin/env python3
import argparse
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def gini(values: np.ndarray) -> float:
    x = np.asarray(values, dtype=float)
    if x.size == 0:
        return 0.0
    if np.any(x < 0):
        x = x - np.min(x)
    s = float(np.sum(x))
    if s <= 0:
        return 0.0
    x = np.sort(x)
    n = x.size
    idx = np.arange(1, n + 1)
    return float((2.0 * np.sum(idx * x) / (n * s)) - (n + 1.0) / n)


def top_share(values: np.ndarray, frac: float) -> float:
    x = np.asarray(values, dtype=float)
    total = float(np.sum(x))
    if x.size == 0 or total <= 0:
        return 0.0
    k = max(1, int(math.ceil(frac * x.size)))
    x_sorted = np.sort(x)[::-1]
    return float(np.sum(x_sorted[:k]) / total)


def lorenz_curve(values: np.ndarray, n_points: int = 101):
    x = np.asarray(values, dtype=float)
    if x.size == 0:
        q = np.linspace(0.0, 1.0, n_points)
        return q, q
    x = np.sort(np.clip(x, 0.0, None))
    total = float(np.sum(x))
    q = np.linspace(0.0, 1.0, n_points)
    if total <= 0:
        return q, np.zeros_like(q)
    cum = np.cumsum(x) / total
    pop = np.arange(1, x.size + 1) / x.size
    pop = np.concatenate(([0.0], pop))
    cum = np.concatenate(([0.0], cum))
    y = np.interp(q, pop, cum)
    return q, y


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.size == 0 or b.size == 0:
        return float("nan")
    va = np.var(a, ddof=1) if a.size > 1 else 0.0
    vb = np.var(b, ddof=1) if b.size > 1 else 0.0
    pooled_denom = ((a.size - 1) * va + (b.size - 1) * vb)
    if pooled_denom <= 0 or (a.size + b.size - 2) <= 0:
        return float("nan")
    pooled_sd = math.sqrt(pooled_denom / (a.size + b.size - 2))
    if pooled_sd == 0:
        return float("nan")
    return float((np.mean(a) - np.mean(b)) / pooled_sd)


def find_seed(path: Path) -> str:
    for part in path.parts:
        if part.startswith("seed_"):
            return part.split("_", 1)[1]
    return "unknown"


def summarize_columns(df: pd.DataFrame, cols):
    rows = []
    for c in cols:
        s = pd.to_numeric(df[c], errors="coerce").dropna()
        if s.empty:
            continue
        rows.append(
            {
                "metric": c,
                "mean": float(s.mean()),
                "sd": float(s.std(ddof=1)) if len(s) > 1 else 0.0,
                "q10": float(s.quantile(0.10)),
                "q50": float(s.quantile(0.50)),
                "q90": float(s.quantile(0.90)),
                "n": int(s.shape[0]),
            }
        )
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=str)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    summary_dir = root / "summary"
    plots_dir = summary_dir / "plots"
    summary_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    run_dirs = []
    for metrics_path in root.rglob("metrics.csv"):
        run_dir = metrics_path.parent
        agent_path = run_dir / "agent_summary.csv"
        if agent_path.exists():
            run_dirs.append(run_dir)

    if not run_dirs:
        raise SystemExit(f"No runs with metrics.csv + agent_summary.csv found under {root}")

    rows = []
    lorenz_curves = []
    pooled_scatter = []
    pooled_box = []

    for run_dir in sorted(run_dirs):
        metrics = pd.read_csv(run_dir / "metrics.csv")
        agents = pd.read_csv(run_dir / "agent_summary.csv")
        if "punish_issued" not in agents.columns or "L" not in agents.columns:
            continue

        seed = find_seed(run_dir)
        punish = pd.to_numeric(agents["punish_issued"], errors="coerce").fillna(0.0).to_numpy(dtype=float)
        total_pun = float(np.sum(punish))

        top1 = top_share(punish, 0.01)
        top5 = top_share(punish, 0.05)
        top10 = top_share(punish, 0.10)
        g_all = gini(punish)
        g_nonzero = gini(punish[punish > 0]) if np.any(punish > 0) else 0.0

        n = len(agents)
        k = max(1, int(math.ceil(0.10 * n)))
        positive_count = int(np.sum(punish > 0))
        if positive_count > 0 and positive_count <= k:
            enforcer_mask = punish > 0
            enforcer_rule = "positive_only"
        else:
            order = np.argsort(-punish)
            enforcer_mask = np.zeros(n, dtype=bool)
            enforcer_mask[order[:k]] = True
            enforcer_rule = "top10pct"

        Lvals = pd.to_numeric(agents["L"], errors="coerce").fillna(0.0).to_numpy(dtype=float)
        L_enf = Lvals[enforcer_mask]
        L_other = Lvals[~enforcer_mask]

        mean_L_enf = float(np.mean(L_enf)) if L_enf.size else float("nan")
        mean_L_other = float(np.mean(L_other)) if L_other.size else float("nan")
        d_L = cohens_d(L_enf, L_other)

        punish_series = pd.Series(punish)
        L_series = pd.Series(Lvals)
        rho_L = float(L_series.corr(punish_series, method="spearman")) if punish_series.nunique() > 1 else float("nan")

        degree_col = None
        if "degree_at_end" in agents.columns:
            degree_col = "degree_at_end"
        elif "degree" in agents.columns:
            degree_col = "degree"

        rho_degree = float("nan")
        if degree_col is not None:
            deg = pd.to_numeric(agents[degree_col], errors="coerce")
            if deg.nunique(dropna=True) > 1 and punish_series.nunique() > 1:
                rho_degree = float(deg.corr(punish_series, method="spearman"))

        q, y = lorenz_curve(punish)
        lorenz_curves.append((q, y))

        pooled_scatter.append(pd.DataFrame({"seed": seed, "L": Lvals, "punish_issued": punish}))
        pooled_box.append(pd.DataFrame({"seed": seed, "group": np.where(enforcer_mask, "enforcers", "others"), "L": Lvals}))

        final = metrics.iloc[-1]
        rows.append(
            {
                "seed": seed,
                "run_dir": str(run_dir),
                "total_punishments": total_pun,
                "top1_share": top1,
                "top5_share": top5,
                "top10_share": top10,
                "gini_including_zeros": g_all,
                "gini_excluding_zeros": g_nonzero,
                "enforcer_rule": enforcer_rule,
                "mean_L_enforcers": mean_L_enf,
                "mean_L_others": mean_L_other,
                "delta_L_enforcers_minus_others": float(mean_L_enf - mean_L_other) if not np.isnan(mean_L_enf) and not np.isnan(mean_L_other) else float("nan"),
                "cohens_d_L_enforcers_vs_others": d_L,
                "spearman_L_vs_punish": rho_L,
                "spearman_degree_vs_punish": rho_degree,
                "final_exit_rate": float(final.get("exit_rate", np.nan)),
                "final_prevalence": float(final.get("fund_prevalence", np.nan)),
                "max_punish_rate": float(metrics["punish_rate"].max()) if "punish_rate" in metrics.columns else np.nan,
            }
        )

    by_seed = pd.DataFrame(rows).sort_values("seed")
    if by_seed.empty:
        raise SystemExit("No valid runs had both punish_issued and L in agent_summary.csv")

    by_seed_path = summary_dir / "minority_metrics_by_seed.csv"
    by_seed.to_csv(by_seed_path, index=False)

    summary_cols = [
        "total_punishments",
        "top1_share",
        "top5_share",
        "top10_share",
        "gini_including_zeros",
        "gini_excluding_zeros",
        "mean_L_enforcers",
        "mean_L_others",
        "delta_L_enforcers_minus_others",
        "cohens_d_L_enforcers_vs_others",
        "spearman_L_vs_punish",
        "spearman_degree_vs_punish",
        "final_exit_rate",
        "final_prevalence",
        "max_punish_rate",
    ]
    summary = summarize_columns(by_seed, summary_cols)
    summary_path = summary_dir / "minority_metrics_summary.csv"
    summary.to_csv(summary_path, index=False)

    # Median Lorenz curve across seeds.
    q_ref = np.linspace(0.0, 1.0, 101)
    ys = []
    for q, y in lorenz_curves:
        ys.append(np.interp(q_ref, q, y))
    y_med = np.median(np.vstack(ys), axis=0)

    plt.figure(figsize=(6, 5), dpi=140)
    plt.plot(q_ref, y_med, label="Median Lorenz", linewidth=2)
    plt.plot([0, 1], [0, 1], linestyle="--", linewidth=1, label="Equality")
    plt.xlabel("Population share")
    plt.ylabel("Punishment share")
    plt.title("Lorenz Curve: Punishment Issuance")
    plt.legend()
    plt.tight_layout()
    plt.savefig(plots_dir / "lorenz_punish_issued.png")
    plt.close()

    scatter_df = pd.concat(pooled_scatter, ignore_index=True)
    if len(scatter_df) > 5000:
        scatter_df = scatter_df.sample(5000, random_state=1)
    plt.figure(figsize=(6, 5), dpi=140)
    plt.scatter(scatter_df["L"], scatter_df["punish_issued"], s=8, alpha=0.25)
    plt.xlabel("Literalism L")
    plt.ylabel("Punish issued")
    plt.title("L vs Punishment Issuance (pooled)")
    plt.tight_layout()
    plt.savefig(plots_dir / "scatter_L_vs_punish.png")
    plt.close()

    box_df = pd.concat(pooled_box, ignore_index=True)
    groups = [box_df.loc[box_df["group"] == "others", "L"].to_numpy(), box_df.loc[box_df["group"] == "enforcers", "L"].to_numpy()]
    plt.figure(figsize=(6, 5), dpi=140)
    plt.boxplot(groups, labels=["others", "enforcers"], showfliers=False)
    plt.ylabel("Literalism L")
    plt.title("L Distribution: Enforcers vs Others")
    plt.tight_layout()
    plt.savefig(plots_dir / "box_L_enforcers_vs_others.png")
    plt.close()

    top5_med = float(by_seed["top5_share"].median())
    top5_mean = float(by_seed["top5_share"].mean())
    d_med = float(by_seed["cohens_d_L_enforcers_vs_others"].median())
    rho_med = float(by_seed["spearman_L_vs_punish"].median())

    memo = []
    memo.append("# RESULTS MINORITY\n")
    memo.append(f"Run root: `{root}`")
    memo.append(f"Seeds analyzed: {len(by_seed)}")
    memo.append(f"Median top-5% punishment share: {top5_med:.3f} (mean {top5_mean:.3f})")
    memo.append(f"Top-5% share exceeds 0.30: {'YES' if top5_med > 0.30 else 'NO'}")
    memo.append(f"Median L Cohen's d (enforcers - others): {d_med:.3f}")
    memo.append(f"Median Spearman rho(L, punish_issued): {rho_med:.3f}")
    memo.append("\n## Interpretation")
    if top5_med > 0.30:
        memo.append("Punishment issuance is concentrated enough to support a minority-driving pattern.")
    else:
        memo.append("Punishment issuance concentration is below the 0.30 top-5% threshold.")
    if np.isfinite(d_med) and d_med > 0:
        memo.append("Enforcers are enriched in literalism L relative to others.")
    else:
        memo.append("No positive literalism enrichment signal among enforcers at current settings.")

    (summary_dir / "RESULTS_MINORITY.md").write_text("\n".join(memo) + "\n", encoding="utf-8")

    print(f"Wrote {by_seed_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {summary_dir / 'RESULTS_MINORITY.md'}")
    print(f"Wrote plots to {plots_dir}")


if __name__ == "__main__":
    main()
