#!/usr/bin/env python3
import argparse
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v26-root", required=True, help="results/v2.6_ablation_v25_recovery")
    ap.add_argument("--v25-root", default="results/v2.5_corrected_three_regime_confirm")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    v26_root = Path(args.v26_root).resolve()
    v25_root = Path(args.v25_root).resolve()
    outdir = Path(args.out).resolve() if args.out else v26_root
    outdir.mkdir(parents=True, exist_ok=True)

    v26 = pd.read_csv(v26_root / "sweep_seed_results.csv")
    v26 = v26[(v26["alpha"] == 0.0) & (v26["delta"] == 0.0)].copy()
    v26 = v26.rename(columns={"regime": "regime_v26"})
    v26 = v26[["sigma", "pi_reward", "seed", "regime_v26"]]

    v25 = pd.read_csv(v25_root / "sweep_seed_results.csv")
    v25 = v25[(v25["base_opp"] == 0.3) & (v25["exit_threshold"] == -1.0)].copy()
    # Compare against the v2.5 hierarchical schema used in final reporting.
    v25 = v25.rename(columns={"regime_hier": "regime_v25"})
    v25 = v25[["sigma", "pi_reward", "seed", "regime_v25"]]

    m = v25.merge(v26, on=["sigma", "pi_reward", "seed"], how="inner")
    m["changed"] = m["regime_v25"] != m["regime_v26"]
    m.to_csv(outdir / "v25_recovery_comparison.csv", index=False)

    summary = pd.DataFrame(
        [
            {
                "n_compared": int(len(m)),
                "n_changed": int(m["changed"].sum()),
                "change_rate": float(m["changed"].mean()) if len(m) else 0.0,
            }
        ]
    )
    summary.to_csv(outdir / "v25_recovery_summary.csv", index=False)

    lines = [
        "# v2.6 v2.5 Recovery Comparison",
        "",
        f"- n_compared: {int(len(m))}",
        f"- n_changed: {int(m['changed'].sum())}",
        f"- change_rate: {float(m['changed'].mean()) if len(m) else 0.0:.6f}",
        f"- regime_v25_counts: {m['regime_v25'].value_counts().to_dict()}",
        f"- regime_v26_counts: {m['regime_v26'].value_counts().to_dict()}",
    ]
    (outdir / "v25_recovery_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {outdir / 'v25_recovery_comparison.csv'}")
    print(f"Wrote {outdir / 'v25_recovery_summary.csv'}")
    print(f"Wrote {outdir / 'v25_recovery_report.md'}")


if __name__ == "__main__":
    main()
