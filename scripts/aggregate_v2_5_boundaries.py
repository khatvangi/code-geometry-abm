#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
import pandas as pd

REGIME_ORDER = ['QUIET', 'MIXED', 'CAPTURE', 'CAPTURE_HIERARCHICAL', 'COLLAPSE']
REGIME_CODE = {r: i for i, r in enumerate(REGIME_ORDER)}
REGIME_COLOR = {
    'QUIET': '#bdbdbd',
    'MIXED': '#4daf4a',
    'CAPTURE': '#ff7f00',
    'CAPTURE_HIERARCHICAL': '#e41a1c',
    'COLLAPSE': '#377eb8',
}


def classify_regime(exit_rate: float, prevalence: float, max_punish: float, enforcer_share: float) -> str:
    if exit_rate >= 0.90:
        return 'COLLAPSE'
    if prevalence >= 0.90 and exit_rate <= 0.20 and enforcer_share >= 0.70:
        return 'CAPTURE_HIERARCHICAL'
    if prevalence >= 0.90 and exit_rate <= 0.20:
        return 'CAPTURE'
    if max_punish >= 0.10:
        return 'MIXED'
    return 'QUIET'


def parse_seed(parts):
    for p in parts:
        if p.startswith('seed_'):
            return int(p.split('_', 1)[1])
    return -1


def parse_float(parts, prefix):
    for p in parts:
        m = re.match(rf'^{re.escape(prefix)}(.+)$', p)
        if m:
            return float(m.group(1))
    return None


def run_enforcer_punish_share(agent_path: Path) -> float:
    if not agent_path.exists():
        return float('nan')
    adf = pd.read_csv(agent_path)
    if 'punish_issued' not in adf.columns or 'is_enforcer' not in adf.columns:
        return float('nan')
    punish = pd.to_numeric(adf['punish_issued'], errors='coerce').fillna(0.0)
    total = float(punish.sum())
    if total <= 0:
        return 0.0
    enf = adf['is_enforcer'].astype(bool)
    return float(punish[enf].sum() / total)


def collect_runs(root: Path, sweep: str) -> pd.DataFrame:
    rows = []
    sweep_root = root / sweep
    if not sweep_root.exists():
        return pd.DataFrame()

    for mpath in sweep_root.rglob('metrics.csv'):
        run_dir = mpath.parent
        parts = mpath.relative_to(root).parts
        quota = parse_float(parts, 'quota_')
        seed = parse_seed(parts)

        mdf = pd.read_csv(mpath)
        if mdf.empty:
            continue
        final = mdf.iloc[-1]
        prevalence_active = float(final.get('fund_prevalence_active', np.nan))
        prevalence_total = float(final.get('fund_prevalence', np.nan))
        row = {
            'run_dir': str(run_dir),
            'seed': seed,
            'quota': float(quota) if quota is not None else float('nan'),
            'final_exit_rate': float(final.get('exit_rate', np.nan)),
            'final_prevalence': prevalence_active if np.isfinite(prevalence_active) else prevalence_total,
            'final_prevalence_active': prevalence_active,
            'final_prevalence_total': prevalence_total,
            'max_punish_rate': float(mdf['punish_rate'].max()) if 'punish_rate' in mdf.columns else np.nan,
            'enforcer_punish_share': run_enforcer_punish_share(run_dir / 'agent_summary.csv'),
        }

        if sweep == 'sweep1':
            row['threat_coeff'] = parse_float(parts, 'threatCoeff_')
            row['shock_strength'] = parse_float(parts, 'shock_')
        else:
            row['membership_benefit_threat'] = parse_float(parts, 'mbt_')
            row['exit_opportunity_base'] = parse_float(parts, 'oppBase_')
        rows.append(row)

    return pd.DataFrame(rows)


def aggregate_cells(df: pd.DataFrame, keys):
    if df.empty:
        return pd.DataFrame()
    agg = (
        df.groupby(keys, as_index=False)
        .agg(
            n_runs=('seed', 'count'),
            final_exit_rate_median=('final_exit_rate', 'median'),
            final_prevalence_median=('final_prevalence', 'median'),
            max_punish_rate_median=('max_punish_rate', 'median'),
            enforcer_punish_share_median=('enforcer_punish_share', 'median'),
            final_exit_rate_mean=('final_exit_rate', 'mean'),
            final_prevalence_mean=('final_prevalence', 'mean'),
            max_punish_rate_mean=('max_punish_rate', 'mean'),
            enforcer_punish_share_mean=('enforcer_punish_share', 'mean'),
        )
        .sort_values(keys)
    )
    agg['regime'] = agg.apply(
        lambda r: classify_regime(
            float(r['final_exit_rate_median']),
            float(r['final_prevalence_median']),
            float(r['max_punish_rate_median']),
            float(r['enforcer_punish_share_median']),
        ),
        axis=1,
    )
    agg['regime_code'] = agg['regime'].map(REGIME_CODE).astype(int)
    return agg


def heatmap_numeric(df: pd.DataFrame, xcol: str, ycol: str, vcol: str, title: str, out_path: Path):
    xvals = sorted(df[xcol].dropna().unique())
    yvals = sorted(df[ycol].dropna().unique())
    grid = np.full((len(yvals), len(xvals)), np.nan)
    for _, r in df.iterrows():
        xi = xvals.index(r[xcol])
        yi = yvals.index(r[ycol])
        grid[yi, xi] = r[vcol]

    plt.figure(figsize=(7, 5), dpi=140)
    im = plt.imshow(grid, origin='lower', aspect='auto')
    plt.xticks(np.arange(len(xvals)), [f'{x:.2f}' for x in xvals])
    plt.yticks(np.arange(len(yvals)), [f'{y:.2f}' for y in yvals])
    plt.xlabel(xcol)
    plt.ylabel(ycol)
    plt.title(title)
    plt.colorbar(im, label=vcol)
    for yi in range(len(yvals)):
        for xi in range(len(xvals)):
            v = grid[yi, xi]
            if np.isfinite(v):
                plt.text(xi, yi, f'{v:.2f}', ha='center', va='center', fontsize=7)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def heatmap_regime(df: pd.DataFrame, xcol: str, ycol: str, title: str, out_path: Path):
    xvals = sorted(df[xcol].dropna().unique())
    yvals = sorted(df[ycol].dropna().unique())
    grid = np.full((len(yvals), len(xvals)), np.nan)
    labels = [['' for _ in xvals] for _ in yvals]
    for _, r in df.iterrows():
        xi = xvals.index(r[xcol])
        yi = yvals.index(r[ycol])
        grid[yi, xi] = r['regime_code']
        labels[yi][xi] = r['regime']

    cmap = ListedColormap([REGIME_COLOR[r] for r in REGIME_ORDER])
    norm = BoundaryNorm(np.arange(-0.5, len(REGIME_ORDER) + 0.5, 1), cmap.N)

    plt.figure(figsize=(7, 5), dpi=140)
    plt.imshow(grid, origin='lower', aspect='auto', cmap=cmap, norm=norm)
    plt.xticks(np.arange(len(xvals)), [f'{x:.2f}' for x in xvals])
    plt.yticks(np.arange(len(yvals)), [f'{y:.2f}' for y in yvals])
    plt.xlabel(xcol)
    plt.ylabel(ycol)
    plt.title(title)

    short = {'QUIET': 'Q', 'MIXED': 'M', 'CAPTURE': 'C', 'CAPTURE_HIERARCHICAL': 'H', 'COLLAPSE': 'X'}
    for yi in range(len(yvals)):
        for xi in range(len(xvals)):
            if labels[yi][xi]:
                plt.text(xi, yi, short[labels[yi][xi]], ha='center', va='center', fontsize=9, fontweight='bold')

    cbar = plt.colorbar(ticks=np.arange(len(REGIME_ORDER)))
    cbar.ax.set_yticklabels(REGIME_ORDER)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def regime_counts_line(df: pd.DataFrame, sweep_name: str, quota: float) -> str:
    counts = df['regime'].value_counts().to_dict()
    return f'{sweep_name} quota={quota:.2f} regime counts: {counts}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    summary_dir = root / 'summary'
    plots_dir = summary_dir / 'plots'
    summary_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    s1_runs = collect_runs(root, 'sweep1')
    s2_runs = collect_runs(root, 'sweep2')

    s1_cell = aggregate_cells(s1_runs, ['quota', 'threat_coeff', 'shock_strength'])
    s2_cell = aggregate_cells(s2_runs, ['quota', 'membership_benefit_threat', 'exit_opportunity_base'])

    s1_csv = summary_dir / 'sweep1_cell_medians.csv'
    s2_csv = summary_dir / 'sweep2_cell_medians.csv'
    s1_cell.to_csv(s1_csv, index=False)
    s2_cell.to_csv(s2_csv, index=False)

    memo = ['# RESULTS V2.5 BOUNDARIES\n', f'Root: `{root}`', '']

    for quota in sorted(s1_cell['quota'].dropna().unique()) if not s1_cell.empty else []:
        qdf = s1_cell[s1_cell['quota'] == quota].copy()
        qtag = f'q{quota:.2f}'.replace('.', '_')
        heatmap_regime(qdf, 'threat_coeff', 'shock_strength', f'Sweep1 Regime Map (quota={quota:.2f})', plots_dir / f'sweep1_{qtag}_regime_map.png')
        heatmap_numeric(qdf, 'threat_coeff', 'shock_strength', 'final_exit_rate_median', f'Sweep1 Exit Rate (q={quota:.2f})', plots_dir / f'sweep1_{qtag}_exit_rate.png')
        heatmap_numeric(qdf, 'threat_coeff', 'shock_strength', 'final_prevalence_median', f'Sweep1 Prevalence (q={quota:.2f})', plots_dir / f'sweep1_{qtag}_prevalence.png')
        heatmap_numeric(qdf, 'threat_coeff', 'shock_strength', 'max_punish_rate_median', f'Sweep1 Max Punish (q={quota:.2f})', plots_dir / f'sweep1_{qtag}_max_punish.png')
        heatmap_numeric(qdf, 'threat_coeff', 'shock_strength', 'enforcer_punish_share_median', f'Sweep1 Enforcer Punish Share (q={quota:.2f})', plots_dir / f'sweep1_{qtag}_enforcer_share.png')
        memo.append(regime_counts_line(qdf, 'sweep1', quota))

    for quota in sorted(s2_cell['quota'].dropna().unique()) if not s2_cell.empty else []:
        qdf = s2_cell[s2_cell['quota'] == quota].copy()
        qtag = f'q{quota:.2f}'.replace('.', '_')
        heatmap_regime(qdf, 'membership_benefit_threat', 'exit_opportunity_base', f'Sweep2 Regime Map (quota={quota:.2f})', plots_dir / f'sweep2_{qtag}_regime_map.png')
        heatmap_numeric(qdf, 'membership_benefit_threat', 'exit_opportunity_base', 'final_exit_rate_median', f'Sweep2 Exit Rate (q={quota:.2f})', plots_dir / f'sweep2_{qtag}_exit_rate.png')
        heatmap_numeric(qdf, 'membership_benefit_threat', 'exit_opportunity_base', 'final_prevalence_median', f'Sweep2 Prevalence (q={quota:.2f})', plots_dir / f'sweep2_{qtag}_prevalence.png')
        heatmap_numeric(qdf, 'membership_benefit_threat', 'exit_opportunity_base', 'max_punish_rate_median', f'Sweep2 Max Punish (q={quota:.2f})', plots_dir / f'sweep2_{qtag}_max_punish.png')
        heatmap_numeric(qdf, 'membership_benefit_threat', 'exit_opportunity_base', 'enforcer_punish_share_median', f'Sweep2 Enforcer Punish Share (q={quota:.2f})', plots_dir / f'sweep2_{qtag}_enforcer_share.png')
        memo.append(regime_counts_line(qdf, 'sweep2', quota))

    (summary_dir / 'RESULTS_V2_5_BOUNDARIES.md').write_text('\n'.join(memo) + '\n', encoding='utf-8')

    print(f'Wrote {s1_csv}')
    print(f'Wrote {s2_csv}')
    print(f'Wrote {summary_dir / "RESULTS_V2_5_BOUNDARIES.md"}')
    print(f'Wrote plots into {plots_dir}')


if __name__ == '__main__':
    main()
