#!/usr/bin/env python3
import argparse
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Ablation root with sweep_seed_results.csv")
    ap.add_argument("--label", default="v2.6b ablation")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    seed_path = root / "sweep_seed_results.csv"
    if not seed_path.exists():
        raise SystemExit(f"Missing {seed_path}")

    df = pd.read_csv(seed_path)
    candidates = ["mu_membership_reward", "delta", "alpha", "sigma", "pi_reward"]
    varying = [c for c in candidates if c in df.columns and df[c].nunique() > 1]
    group_cols = varying if varying else [c for c in candidates if c in df.columns]

    out = (
        df.groupby(group_cols, as_index=False)
        .agg(
            n_runs=("seed", "count"),
            n_capture=("regime", lambda s: int((s == "CAPTURE").sum())),
            n_mixed=("regime", lambda s: int((s == "MIXED").sum())),
            median_exit_rate=("final_exit_rate", "median"),
            median_top5_share=("top5_punishment_share", "median"),
            median_enforcer_share=("enforcer_punish_share", "median"),
        )
        .sort_values(group_cols)
    )
    out.to_csv(root / "ablation_summary.csv", index=False)

    capture_rows = out[out["n_capture"] > 0]
    if capture_rows.empty:
        capture_line = "capture_threshold=none"
    else:
        first = capture_rows.iloc[0].to_dict()
        key_vals = ", ".join([f"{k}={first[k]}" for k in group_cols])
        capture_line = f"capture_threshold~{key_vals}"

    lines = [
        f"# {args.label}",
        "",
        f"- n_seed_runs: {len(df)}",
        f"- varying_dims: {group_cols}",
        f"- regime_counts: {df['regime'].value_counts().to_dict()}",
        f"- {capture_line}",
        "",
        "## Medians",
        out.to_string(index=False),
    ]
    (root / "ablation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {root / 'ablation_summary.csv'}")
    print(f"Wrote {root / 'ablation_report.md'}")


if __name__ == "__main__":
    main()
