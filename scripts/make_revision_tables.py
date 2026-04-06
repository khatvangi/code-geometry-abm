#!/usr/bin/env python3
"""produce the four summary tables for the PLOS ONE revision."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent / "results"


def table_1_monopoly():
    path = ROOT / "ablation_monopoly_comparison.csv"
    if not path.exists():
        print("TABLE 1: MISSING (run run_ablation_monopoly.py first)")
        return
    df = pd.read_csv(path)
    print("=" * 80)
    print("TABLE 1: Monopoly ON vs OFF — concentration metrics at matched parameter points")
    print("=" * 80)
    cols = ["sigma", "pi_reward", "base_opp", "condition", "n_seeds",
            "median_top5_share", "median_top10_share", "median_enforcer_share",
            "median_max_punish", "median_fund_prevalence", "median_exit_rate"]
    print(df[cols].to_string(index=False, float_format="%.3f"))
    print()


def table_2_quota():
    path = ROOT / "ablation_quota" / "summary_by_quota.csv"
    if not path.exists():
        print("TABLE 2: MISSING (run run_ablation_quota.py first)")
        return
    df = pd.read_csv(path)
    print("=" * 80)
    print("TABLE 2: Concentration by cadre quota fraction")
    print(f"         (fixed: sigma=0.75, pi=0.25, base_opp=0.30)")
    print("=" * 80)
    print(df.to_string(index=False, float_format="%.3f"))
    print()


def table_3_gate():
    path = ROOT / "ablation_gate" / "summary_by_floor.csv"
    if not path.exists():
        print("TABLE 3: MISSING (run run_ablation_gate.py first)")
        return
    df = pd.read_csv(path)
    print("=" * 80)
    print("TABLE 3: Regime counts and median delta by intensity gate floor")
    print(f"         (drift spec: sigma=0.95, pi=0.25, eta=0.10, delta0=0.2)")
    print("=" * 80)
    print(df.to_string(index=False, float_format="%.3f"))
    print()


def table_4_bootstrap():
    path = ROOT / "bootstrap_regression" / "summary.txt"
    if not path.exists():
        print("TABLE 4: MISSING (run run_bootstrap_regression.py first)")
        return
    print("=" * 80)
    print("TABLE 4: Bootstrap CI on R-squared ratio (cross-national regression)")
    print("=" * 80)
    print(path.read_text(encoding="utf-8"))
    print()


def main():
    print()
    table_1_monopoly()
    table_2_quota()
    table_3_gate()
    table_4_bootstrap()

    print("=" * 80)
    print("PLACEMENT GUIDE")
    print("=" * 80)
    print("  Table 1 → Supplementary Table S3 + §8.10 paragraph")
    print("  Table 2 → Supplementary Table S4 + §8.2 sentence")
    print("  Table 3 → Supplementary Table S5")
    print("  Table 4 → Supplementary Table S6 + §9.8 CI update")
    print()


if __name__ == "__main__":
    main()
