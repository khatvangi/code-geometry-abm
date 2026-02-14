#!/usr/bin/env python3
import argparse
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
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


def summarize(df: pd.DataFrame, cols):
    out = []
    for c in cols:
        s = pd.to_numeric(df[c], errors='coerce').dropna()
        if s.empty:
            continue
        out.append({
            'metric': c,
            'mean': float(s.mean()),
            'sd': float(s.std(ddof=1)) if len(s) > 1 else 0.0,
            'q10': float(s.quantile(0.10)),
            'q50': float(s.quantile(0.50)),
            'q90': float(s.quantile(0.90)),
            'n': int(s.shape[0]),
        })
    return pd.DataFrame(out)


def seed_from_path(path: Path) -> str:
    for p in path.parts:
        if p.startswith('seed_'):
            return p.split('_', 1)[1]
    return 'unknown'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    summary_dir = root / 'summary'
    plots_dir = summary_dir / 'plots'
    summary_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    run_dirs = []
    for mpath in root.rglob('metrics.csv'):
        apath = mpath.parent / 'agent_summary.csv'
        if apath.exists():
            run_dirs.append(mpath.parent)

    if not run_dirs:
        raise SystemExit(f'No runs found under {root}')

    rows = []
    pooled_l = []
    pooled_pun = []
    pooled_service = []

    for run in sorted(run_dirs):
        adf = pd.read_csv(run / 'agent_summary.csv')
        mdf = pd.read_csv(run / 'metrics.csv')
        if mdf.empty:
            continue

        for col in ['punish_issued', 'service', 'L', 'cap', 'is_enforcer']:
            if col not in adf.columns:
                raise SystemExit(f'Missing required column {col} in {run / "agent_summary.csv"}')

        punish = pd.to_numeric(adf['punish_issued'], errors='coerce').fillna(0.0).to_numpy(dtype=float)
        service = pd.to_numeric(adf['service'], errors='coerce').fillna(0.0).to_numpy(dtype=float)
        L = pd.to_numeric(adf['L'], errors='coerce').fillna(0.0).to_numpy(dtype=float)
        cap = pd.to_numeric(adf['cap'], errors='coerce').fillna(0.0).to_numpy(dtype=float)
        enf = adf['is_enforcer'].astype(bool).to_numpy()

        total_pun = float(np.sum(punish))
        total_service = float(np.sum(service))

        enf_pun_share = float(np.sum(punish[enf]) / total_pun) if total_pun > 0 else 0.0
        enf_service_share = float(np.sum(service[enf]) / total_service) if total_service > 0 else 0.0

        L_enf = L[enf]
        L_oth = L[~enf]
        dL = cohens_d(L_enf, L_oth)

        s_pun = pd.Series(punish)
        s_service = pd.Series(service)
        s_L = pd.Series(L)
        s_cap = pd.Series(cap)

        rho_L_pun = float(s_L.corr(s_pun, method='spearman')) if s_pun.nunique() > 1 else float('nan')
        rho_L_cap = float(s_L.corr(s_cap, method='spearman')) if s_cap.nunique() > 1 else float('nan')
        rho_L_service = float(s_L.corr(s_service, method='spearman')) if s_service.nunique() > 1 else float('nan')

        final = mdf.iloc[-1]

        rows.append({
            'seed': seed_from_path(run),
            'run_dir': str(run),
            'total_punishments': total_pun,
            'total_service': total_service,
            'punish_top1_share': top_share(punish, 0.01),
            'punish_top5_share': top_share(punish, 0.05),
            'punish_top10_share': top_share(punish, 0.10),
            'service_top1_share': top_share(service, 0.01),
            'service_top5_share': top_share(service, 0.05),
            'service_top10_share': top_share(service, 0.10),
            'punish_gini_all': gini(punish),
            'punish_gini_nonzero': gini(punish[punish > 0]) if np.any(punish > 0) else 0.0,
            'service_gini_all': gini(service),
            'service_gini_nonzero': gini(service[service > 0]) if np.any(service > 0) else 0.0,
            'enforcer_punish_share': enf_pun_share,
            'enforcer_service_share': enf_service_share,
            'mean_L_enforcers': float(np.mean(L_enf)) if L_enf.size else float('nan'),
            'mean_L_others': float(np.mean(L_oth)) if L_oth.size else float('nan'),
            'cohens_d_L_enforcers_vs_others': dL,
            'spearman_L_vs_punish': rho_L_pun,
            'spearman_L_vs_cap': rho_L_cap,
            'spearman_L_vs_service': rho_L_service,
            'final_exit_rate': float(final.get('exit_rate', np.nan)),
            'final_prevalence': float(final.get('fund_prevalence', np.nan)),
            'max_punish_rate': float(mdf['punish_rate'].max()) if 'punish_rate' in mdf.columns else np.nan,
        })

        pooled_l.append(L)
        pooled_pun.append(punish)
        pooled_service.append(service)

    by_seed = pd.DataFrame(rows).sort_values('seed')
    if by_seed.empty:
        raise SystemExit('No valid runs found')

    by_seed_path = summary_dir / 'minority_metrics_by_seed.csv'
    by_seed.to_csv(by_seed_path, index=False)

    cols = [
        'total_punishments', 'total_service',
        'punish_top1_share', 'punish_top5_share', 'punish_top10_share',
        'service_top1_share', 'service_top5_share', 'service_top10_share',
        'punish_gini_all', 'punish_gini_nonzero',
        'service_gini_all', 'service_gini_nonzero',
        'enforcer_punish_share', 'enforcer_service_share',
        'mean_L_enforcers', 'mean_L_others', 'cohens_d_L_enforcers_vs_others',
        'spearman_L_vs_punish', 'spearman_L_vs_cap', 'spearman_L_vs_service',
        'final_exit_rate', 'final_prevalence', 'max_punish_rate'
    ]
    summary = summarize(by_seed, cols)
    summary_path = summary_dir / 'minority_metrics_summary.csv'
    summary.to_csv(summary_path, index=False)

    L_all = np.concatenate(pooled_l)
    P_all = np.concatenate(pooled_pun)
    S_all = np.concatenate(pooled_service)

    n = min(6000, len(L_all))
    idx = np.random.default_rng(1).choice(len(L_all), size=n, replace=False) if len(L_all) > n else np.arange(len(L_all))

    plt.figure(figsize=(6, 5), dpi=140)
    plt.scatter(L_all[idx], P_all[idx], s=8, alpha=0.25)
    plt.xlabel('Literalism L')
    plt.ylabel('Punish issued')
    plt.title('L vs Punishment (pooled)')
    plt.tight_layout()
    plt.savefig(plots_dir / 'scatter_L_vs_punish.png')
    plt.close()

    plt.figure(figsize=(6, 5), dpi=140)
    plt.scatter(L_all[idx], S_all[idx], s=8, alpha=0.25)
    plt.xlabel('Literalism L')
    plt.ylabel('Service')
    plt.title('L vs Service (pooled)')
    plt.tight_layout()
    plt.savefig(plots_dir / 'scatter_L_vs_service.png')
    plt.close()

    top5_med = float(by_seed['punish_top5_share'].median())
    top10_med = float(by_seed['punish_top10_share'].median())
    enf_share_med = float(by_seed['enforcer_punish_share'].median())
    d_med = float(by_seed['cohens_d_L_enforcers_vs_others'].median())
    rho_med = float(by_seed['spearman_L_vs_service'].median())

    memo = []
    memo.append('# RESULTS V2.4 MINORITY\n')
    memo.append(f'Run root: `{root}`')
    memo.append(f'Seeds analyzed: {len(by_seed)}')
    memo.append(f'Median punishment top-5 share: {top5_med:.3f}')
    memo.append(f'Median punishment top-10 share: {top10_med:.3f}')
    memo.append(f'Median enforcer punishment share: {enf_share_med:.3f}')
    memo.append(f"Median Cohen's d (L enforcers vs others): {d_med:.3f}")
    memo.append(f'Median Spearman rho(L, service): {rho_med:.3f}')
    memo.append('')
    memo.append('## Acceptance checks')
    memo.append(f"- top-5 punishment share >= 0.30: {'YES' if top5_med >= 0.30 else 'NO'}")
    memo.append(f"- or top-10 punishment share >= 0.50: {'YES' if top10_med >= 0.50 else 'NO'}")
    memo.append(f"- enforcer punishment share >= 0.70: {'YES' if enf_share_med >= 0.70 else 'NO'}")
    memo.append(f"- L enrichment d > 0.20: {'YES' if d_med > 0.20 else 'NO'}")

    (summary_dir / 'RESULTS_V2_4_MINORITY.md').write_text('\n'.join(memo) + '\n', encoding='utf-8')

    print(f'Wrote {by_seed_path}')
    print(f'Wrote {summary_path}')
    print(f'Wrote {summary_dir / "RESULTS_V2_4_MINORITY.md"}')
    print(f'Wrote plots to {plots_dir}')


if __name__ == '__main__':
    main()
