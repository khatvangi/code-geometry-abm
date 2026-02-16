#!/usr/bin/env python3
import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def classify_regime(exit_rate: float, prevalence: float, max_punish: float, capture_exit_cap: float) -> str:
    if exit_rate >= 0.90:
        return "COLLAPSE"
    if prevalence >= 0.10 and max_punish >= 0.10 and exit_rate <= capture_exit_cap:
        return "CAPTURE"
    if max_punish >= 0.10:
        return "MIXED"
    return "QUIET"


def top_share(values: np.ndarray, frac: float) -> float:
    x = np.asarray(values, dtype=float)
    total = float(np.sum(x))
    if x.size == 0 or total <= 0:
        return 0.0
    k = max(1, int(np.ceil(frac * x.size)))
    return float(np.sum(np.sort(x)[::-1][:k]) / total)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--capture-exit-cap", type=float, default=0.20)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    rows = []
    ts_rows = []

    for mpath in sorted(root.rglob("metrics.csv")):
        run_dir = mpath.parent
        apath = run_dir / "agent_summary.csv"
        if not apath.exists():
            continue
        parts = mpath.relative_to(root).parts
        try:
            eta = float(parts[0].split("_", 1)[1])
            delta0 = float(parts[1].split("_", 1)[1])
            sigma = float(parts[2].split("_", 1)[1])
            pi_reward = float(parts[3].split("_", 1)[1])
            seed = int(parts[4].split("_", 1)[1])
        except Exception:
            continue

        mdf = pd.read_csv(mpath)
        adf = pd.read_csv(apath)
        if mdf.empty:
            continue

        final = mdf.iloc[-1]
        prevalence = float(final.get("fund_prevalence", np.nan))
        exit_rate = float(final.get("exit_rate", np.nan))
        max_punish = float(mdf["punish_rate"].max()) if "punish_rate" in mdf.columns else np.nan
        final_delta = float(final.get("current_delta", final.get("delta_outside_degrade", np.nan)))
        regime = classify_regime(exit_rate, prevalence, max_punish, args.capture_exit_cap)

        punish = pd.to_numeric(adf.get("punish_issued", pd.Series(dtype=float)), errors="coerce").fillna(0.0).to_numpy(dtype=float)
        top5 = top_share(punish, 0.05)
        step_share = pd.to_numeric(
            mdf.get("enforcer_punish_share_step", pd.Series(dtype=float)), errors="coerce"
        ).replace([np.inf, -np.inf], np.nan)
        punish_rate = pd.to_numeric(mdf.get("punish_rate", pd.Series(dtype=float)), errors="coerce")
        active_steps = punish_rate > 0
        if active_steps.any():
            enforcer_share = float(step_share[active_steps].fillna(0.0).mean())
        else:
            enforcer_share = 0.0

        # Step where final-exit proxy first crosses capture threshold.
        cap_series = pd.to_numeric(mdf.get("exit_rate", pd.Series(dtype=float)), errors="coerce")
        crossed = mdf.loc[cap_series <= args.capture_exit_cap, "t"]
        time_to_capture = float(crossed.iloc[0]) if len(crossed) else np.nan

        rows.append(
            {
                "eta_delta_drift": eta,
                "delta0": delta0,
                "sigma": sigma,
                "pi_reward": pi_reward,
                "seed": seed,
                "regime": regime,
                "final_exit_rate": exit_rate,
                "final_fund_prevalence": prevalence,
                "max_punish": max_punish,
                "final_current_delta": final_delta,
                "time_to_capture": time_to_capture,
                "top5_punishment_share": top5,
                "enforcer_punish_share": float(np.clip(enforcer_share, 0.0, 1.0)),
                "run_dir": str(run_dir),
            }
        )

        if "current_delta" in mdf.columns:
            for r in mdf[["t", "current_delta", "exit_rate"]].itertuples(index=False):
                ts_rows.append(
                    {
                        "eta_delta_drift": eta,
                        "delta0": delta0,
                        "sigma": sigma,
                        "pi_reward": pi_reward,
                        "seed": seed,
                        "t": int(r.t),
                        "current_delta": float(r.current_delta),
                        "exit_rate": float(r.exit_rate),
                    }
                )

    seed_df = pd.DataFrame(rows).sort_values(["eta_delta_drift", "seed"])
    seed_df.to_csv(root / "emergence_seed_results.csv", index=False)

    summary = (
        seed_df.groupby(["eta_delta_drift", "delta0", "sigma", "pi_reward"], as_index=False)
        .agg(
            n_runs=("seed", "count"),
            n_capture=("regime", lambda s: int((s == "CAPTURE").sum())),
            n_mixed=("regime", lambda s: int((s == "MIXED").sum())),
            median_exit_rate=("final_exit_rate", "median"),
            median_final_delta=("final_current_delta", "median"),
            median_time_to_capture=("time_to_capture", "median"),
            median_top5_share=("top5_punishment_share", "median"),
            median_enforcer_share=("enforcer_punish_share", "median"),
        )
        .sort_values(["eta_delta_drift", "delta0", "sigma", "pi_reward"])
    )
    summary.to_csv(root / "emergence_summary.csv", index=False)

    ts_df = pd.DataFrame(ts_rows).sort_values(["eta_delta_drift", "seed", "t"])
    ts_df.to_csv(root / "delta_timeseries_by_seed.csv", index=False)

    lines = [
        "# v2.7 Emergence Ablation",
        f"n_seed_runs={len(seed_df)}",
        f"regime_counts={seed_df['regime'].value_counts().to_dict() if not seed_df.empty else {}}",
    ]
    if not summary.empty:
        lines.append("\n## By eta")
        lines.append(summary.to_string(index=False))
    (root / "RESULTS_V2_7_ABLATION_EMERGENCE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {root / 'emergence_seed_results.csv'}")
    print(f"Wrote {root / 'emergence_summary.csv'}")
    print(f"Wrote {root / 'delta_timeseries_by_seed.csv'}")
    print(f"Wrote {root / 'RESULTS_V2_7_ABLATION_EMERGENCE.md'}")


if __name__ == "__main__":
    main()
