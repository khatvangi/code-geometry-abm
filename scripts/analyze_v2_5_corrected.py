#!/usr/bin/env python3
import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd


def top_share(values: np.ndarray, frac: float) -> float:
    x = np.asarray(values, dtype=float)
    total = float(np.sum(x))
    if x.size == 0 or total <= 0:
        return 0.0
    k = max(1, int(math.ceil(frac * x.size)))
    return float(np.sum(np.sort(x)[::-1][:k]) / total)


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.size == 0 or b.size == 0:
        return float('nan')
    va = np.var(a, ddof=1) if a.size > 1 else 0.0
    vb = np.var(b, ddof=1) if b.size > 1 else 0.0
    denom = ((a.size - 1) * va + (b.size - 1) * vb)
    if denom <= 0 or (a.size + b.size - 2) <= 0:
        return float('nan')
    pooled_sd = math.sqrt(denom / (a.size + b.size - 2))
    if pooled_sd == 0:
        return float('nan')
    return float((np.mean(a) - np.mean(b)) / pooled_sd)


def classify_regime(exit_rate: float, prevalence: float, max_punish: float) -> str:
    if exit_rate >= 0.90:
        return 'COLLAPSE'
    if prevalence >= 0.90 and exit_rate <= 0.20:
        return 'CAPTURE'
    if max_punish >= 0.10:
        return 'MIXED'
    return 'QUIET'


def seed_from_dir(path: Path) -> int:
    name = path.name
    if name.startswith('seed_'):
        return int(name.split('_', 1)[1])
    return -1


def summarize_run(seed_dir: Path):
    mpath = seed_dir / 'metrics.csv'
    apath = seed_dir / 'agent_summary.csv'
    if not mpath.exists() or not apath.exists():
        return None

    mdf = pd.read_csv(mpath)
    adf = pd.read_csv(apath)
    if mdf.empty or adf.empty:
        return None

    final = mdf.iloc[-1]
    prevalence_active = float(final.get('fund_prevalence', np.nan))
    exit_rate = float(final.get('exit_rate', np.nan))
    max_punish = float(mdf['punish_rate'].max()) if 'punish_rate' in mdf.columns else float('nan')

    punish = pd.to_numeric(adf['punish_issued'], errors='coerce').fillna(0.0).to_numpy(dtype=float)
    enforcer = adf['is_enforcer'].astype(bool).to_numpy() if 'is_enforcer' in adf.columns else np.zeros_like(punish, dtype=bool)
    L = pd.to_numeric(adf['L'], errors='coerce').fillna(0.0).to_numpy(dtype=float) if 'L' in adf.columns else np.zeros_like(punish)

    total_p = float(np.sum(punish))
    enforcer_share = float(np.sum(punish[enforcer]) / total_p) if total_p > 0 else 0.0

    dL = cohens_d(L[enforcer], L[~enforcer]) if np.any(enforcer) and np.any(~enforcer) else float('nan')

    ncf = pd.to_numeric(mdf.get('n_cadre_fallback', pd.Series(np.zeros(len(mdf)))), errors='coerce').fillna(0).to_numpy(dtype=int)
    drop_t = np.nan
    for t in range(len(ncf)):
        if np.all(ncf[t:] == 0):
            drop_t = float(t)
            break

    row = {
        'seed': seed_from_dir(seed_dir),
        'run_dir': str(seed_dir),
        'final_exit_rate': exit_rate,
        'final_prevalence_active': prevalence_active,
        'max_punish_rate': max_punish,
        'top5_punish_share': top_share(punish, 0.05),
        'top10_punish_share': top_share(punish, 0.10),
        'enforcer_punish_share': enforcer_share,
        'literalism_enrichment_d': dL,
        'regime': classify_regime(exit_rate, prevalence_active, max_punish),
        'fallback_drop_t': drop_t,
    }

    ts = mdf[['t']].copy()
    ts['seed'] = row['seed']
    ts['fund_prevalence_active'] = pd.to_numeric(mdf.get('fund_prevalence', np.nan), errors='coerce')
    ts['n_cadre_fallback'] = pd.to_numeric(mdf.get('n_cadre_fallback', np.nan), errors='coerce')
    return row, ts


def summarize_folder(root: Path):
    rows = []
    ts_parts = []
    for seed_dir in sorted(root.glob('seed_*')):
        out = summarize_run(seed_dir)
        if out is None:
            continue
        row, ts = out
        rows.append(row)
        ts_parts.append(ts)
    if not rows:
        return pd.DataFrame(), pd.DataFrame()
    by_seed = pd.DataFrame(rows).sort_values('seed')
    ts_df = pd.concat(ts_parts, ignore_index=True)
    return by_seed, ts_df


def write_comparison(baseline_df: pd.DataFrame, ablation_df: pd.DataFrame, out_csv: Path):
    metrics = [
        'final_exit_rate',
        'final_prevalence_active',
        'max_punish_rate',
        'top5_punish_share',
        'top10_punish_share',
        'enforcer_punish_share',
        'literalism_enrichment_d',
    ]
    rows = []
    for m in metrics:
        b = pd.to_numeric(baseline_df[m], errors='coerce').dropna().to_numpy(dtype=float)
        a = pd.to_numeric(ablation_df[m], errors='coerce').dropna().to_numpy(dtype=float)
        b_med = float(np.median(b)) if b.size else float('nan')
        a_med = float(np.median(a)) if a.size else float('nan')
        rows.append({
            'metric': m,
            'baseline_median': b_med,
            'ablation_median': a_med,
            'difference': a_med - b_med if np.isfinite(a_med) and np.isfinite(b_med) else float('nan'),
            'cohens_d': cohens_d(a, b),
        })
    pd.DataFrame(rows).to_csv(out_csv, index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline-root', required=True)
    ap.add_argument('--ablation-root', required=True)
    ap.add_argument('--old-root', default='runs/batch_v2_5_monopoly_20260213_090212/bestparams')
    args = ap.parse_args()

    baseline_root = Path(args.baseline_root).resolve()
    ablation_root = Path(args.ablation_root).resolve()
    old_root = Path(args.old_root).resolve()

    baseline_df, baseline_ts = summarize_folder(baseline_root)
    ablation_df, ablation_ts = summarize_folder(ablation_root)
    old_df, _ = summarize_folder(old_root)

    if baseline_df.empty:
        raise SystemExit('No baseline runs found')
    if ablation_df.empty:
        raise SystemExit('No ablation runs found')

    baseline_df.to_csv(baseline_root / 'regime_by_seed.csv', index=False)
    ablation_df.to_csv(ablation_root / 'regime_by_seed.csv', index=False)
    baseline_df.to_csv(baseline_root / 'minority_by_seed.csv', index=False)
    ablation_df.to_csv(ablation_root / 'minority_by_seed.csv', index=False)
    baseline_ts.to_csv(baseline_root / 'fund_prevalence_active_timeseries.csv', index=False)
    ablation_ts.to_csv(ablation_root / 'fund_prevalence_active_timeseries.csv', index=False)

    # Task 5 regime comparison old vs corrected baseline.
    old_map = old_df.set_index('seed')['regime'].to_dict() if not old_df.empty else {}
    rows = []
    for _, r in baseline_df.iterrows():
        seed = int(r['seed'])
        old_reg = old_map.get(seed, np.nan)
        new_reg = r['regime']
        rows.append({
            'param_combo': f'bestparams_seed_{seed:02d}',
            'old_regime': old_reg,
            'new_regime': new_reg,
            'changed': bool(old_reg != new_reg) if pd.notna(old_reg) else np.nan,
        })
    pd.DataFrame(rows).to_csv(baseline_root / 'regime_comparison.csv', index=False)

    # Task 6 baseline vs ablation comparison table.
    write_comparison(baseline_df, ablation_df, ablation_root / 'ablation_comparison.csv')

    # Task 7 fallback analysis.
    drop = pd.to_numeric(baseline_df['fallback_drop_t'], errors='coerce')
    valid = drop.dropna()
    if not valid.empty:
        med = float(valid.median())
        rmin = float(valid.min())
        rmax = float(valid.max())
    else:
        med = rmin = rmax = float('nan')

    late_mask = drop.isna() | (drop > 50)
    late_frac = float(late_mask.mean()) if len(drop) > 0 else 0.0

    fallback_report = {
        'n_seeds': int(len(drop)),
        'fallback_drop_t_median': med,
        'fallback_drop_t_min': rmin,
        'fallback_drop_t_max': rmax,
        'late_or_never_drop_frac': late_frac,
        'late_or_never_drop_n': int(late_mask.sum()),
    }

    # If >10% late, recompute d excluding late/never seeds.
    d_recompute = np.nan
    if late_frac > 0.10:
        kept = baseline_df.loc[~late_mask, 'literalism_enrichment_d']
        d_recompute = float(pd.to_numeric(kept, errors='coerce').median()) if not kept.empty else float('nan')
    fallback_report['literalism_d_median_excluding_late_seeds'] = d_recompute

    pd.DataFrame([fallback_report]).to_csv(baseline_root / 'fallback_analysis.csv', index=False)

    with open(baseline_root / 'fallback_analysis.md', 'w', encoding='utf-8') as f:
        f.write('# Fallback Analysis\n\n')
        f.write(f"median drop-to-zero timestep: {med}\n")
        f.write(f"range: [{rmin}, {rmax}]\n")
        f.write(f"late (>50) or never drop fraction: {late_frac:.3f}\n")
        if late_frac > 0.10:
            f.write(f"recomputed literalism d median (excluding late/never seeds): {d_recompute}\n")

    print(f'Wrote {baseline_root / "regime_comparison.csv"}')
    print(f'Wrote {ablation_root / "ablation_comparison.csv"}')
    print(f'Wrote {baseline_root / "fallback_analysis.csv"}')


if __name__ == '__main__':
    main()
