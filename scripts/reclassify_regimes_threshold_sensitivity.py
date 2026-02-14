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

VARIANTS = {
    'V0': {'exit': 0.90, 'prev': 0.90, 'exit_cap': 0.20, 'pun': 0.10},
    'V1': {'exit': 0.95, 'prev': 0.92, 'exit_cap': 0.15, 'pun': 0.12},
    'V2': {'exit': 0.85, 'prev': 0.85, 'exit_cap': 0.25, 'pun': 0.08},
}

REGIMES = ['QUIET', 'MIXED', 'CAPTURE', 'COLLAPSE']
REGIME_CODE = {r: i for i, r in enumerate(REGIMES)}
REGIME_COLOR = {
    'QUIET': '#bdbdbd',
    'MIXED': '#4daf4a',
    'CAPTURE': '#ff7f00',
    'COLLAPSE': '#377eb8',
}


def classify(exit_rate: float, prevalence: float, max_punish: float, t: dict) -> str:
    if exit_rate >= t['exit']:
        return 'COLLAPSE'
    if prevalence >= t['prev'] and exit_rate <= t['exit_cap']:
        return 'CAPTURE'
    if max_punish >= t['pun']:
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


def collect_runs(root: Path, sweep: str) -> pd.DataFrame:
    rows = []
    sweep_root = root / sweep
    if not sweep_root.exists():
        return pd.DataFrame()

    for mpath in sweep_root.rglob('metrics.csv'):
        parts = mpath.relative_to(root).parts
        seed = parse_seed(parts)
        quota = parse_float(parts, 'quota_')

        mdf = pd.read_csv(mpath)
        if mdf.empty:
            continue
        final = mdf.iloc[-1]

        prevalence_active = float(final.get('fund_prevalence_active', np.nan))
        prevalence_total = float(final.get('fund_prevalence', np.nan))
        prevalence = prevalence_active if np.isfinite(prevalence_active) else prevalence_total

        row = {
            'sweep': sweep,
            'quota': float(quota) if quota is not None else float('nan'),
            'seed': seed,
            'final_exit_rate': float(final.get('exit_rate', np.nan)),
            'final_prevalence': prevalence,
            'final_prevalence_active': prevalence_active,
            'final_prevalence_total': prevalence_total,
            'max_punish_rate': float(mdf['punish_rate'].max()) if 'punish_rate' in mdf.columns else np.nan,
        }
        if sweep == 'sweep1':
            row['x'] = parse_float(parts, 'threatCoeff_')
            row['y'] = parse_float(parts, 'shock_')
        else:
            row['x'] = parse_float(parts, 'membership_benefit_threat_')
            row['y'] = parse_float(parts, 'exit_opportunity_base_')
            # back-compat with existing naming
            if row['x'] is None:
                row['x'] = parse_float(parts, 'mbt_')
            if row['y'] is None:
                row['y'] = parse_float(parts, 'oppBase_')
        rows.append(row)

    return pd.DataFrame(rows)


def aggregate_cells(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    return (
        df.groupby(['sweep', 'quota', 'x', 'y'], as_index=False)
        .agg(
            n_runs=('seed', 'count'),
            final_exit_rate_median=('final_exit_rate', 'median'),
            final_prevalence_median=('final_prevalence', 'median'),
            max_punish_rate_median=('max_punish_rate', 'median'),
        )
        .sort_values(['sweep', 'quota', 'x', 'y'])
    )


def plot_regime(ax, df: pd.DataFrame, title: str):
    if df.empty:
        ax.set_axis_off()
        ax.set_title(title + ' (no data)')
        return
    xvals = sorted(df['x'].dropna().unique())
    yvals = sorted(df['y'].dropna().unique())
    grid = np.full((len(yvals), len(xvals)), np.nan)
    labels = [['' for _ in xvals] for _ in yvals]
    for _, r in df.iterrows():
        xi = xvals.index(r['x'])
        yi = yvals.index(r['y'])
        reg = r['regime']
        grid[yi, xi] = REGIME_CODE[reg]
        labels[yi][xi] = reg

    cmap = ListedColormap([REGIME_COLOR[r] for r in REGIMES])
    norm = BoundaryNorm(np.arange(-0.5, len(REGIMES) + 0.5, 1), cmap.N)
    ax.imshow(grid, origin='lower', aspect='auto', cmap=cmap, norm=norm)
    ax.set_xticks(np.arange(len(xvals)), [f'{x:.2f}' for x in xvals])
    ax.set_yticks(np.arange(len(yvals)), [f'{y:.2f}' for y in yvals])
    ax.set_title(title)
    short = {'QUIET': 'Q', 'MIXED': 'M', 'CAPTURE': 'C', 'COLLAPSE': 'X'}
    for yi in range(len(yvals)):
        for xi in range(len(xvals)):
            reg = labels[yi][xi]
            if reg:
                ax.text(xi, yi, short[reg], ha='center', va='center', fontsize=9, fontweight='bold')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--variants', nargs='*', default=['V0', 'V1', 'V2'])
    args = ap.parse_args()

    root = Path(args.root).resolve()
    summary_dir = root / 'summary'
    summary_dir.mkdir(parents=True, exist_ok=True)

    runs = pd.concat([
        collect_runs(root, 'sweep1'),
        collect_runs(root, 'sweep2'),
    ], ignore_index=True)
    if runs.empty:
        raise SystemExit(f'No sweep metrics found under {root}')

    cells = aggregate_cells(runs)
    variant_tables = {}

    for v in args.variants:
        if v not in VARIANTS:
            raise SystemExit(f'Unknown variant {v}')
        t = VARIANTS[v]
        out = cells.copy()
        out['variant'] = v
        out['regime'] = out.apply(
            lambda r: classify(
                float(r['final_exit_rate_median']),
                float(r['final_prevalence_median']),
                float(r['max_punish_rate_median']),
                t,
            ),
            axis=1,
        )
        variant_tables[v] = out
        out.to_csv(summary_dir / f'regime_map_variant_{v}.csv', index=False)

        fig, axes = plt.subplots(1, 2, figsize=(12, 5), dpi=140)
        s1 = out[out['sweep'] == 'sweep1']
        s2 = out[out['sweep'] == 'sweep2']
        if not s1.empty:
            q1 = float(sorted(s1['quota'].dropna().unique())[0])
            plot_regime(axes[0], s1[s1['quota'] == q1], f'{v} Sweep1 (quota={q1:.2f})')
            axes[0].set_xlabel('threatCoeff')
            axes[0].set_ylabel('shock_strength')
        else:
            axes[0].set_axis_off()

        if not s2.empty:
            q2 = float(sorted(s2['quota'].dropna().unique())[0])
            plot_regime(axes[1], s2[s2['quota'] == q2], f'{v} Sweep2 (quota={q2:.2f})')
            axes[1].set_xlabel('membership_benefit_threat')
            axes[1].set_ylabel('exit_opportunity_base')
        else:
            axes[1].set_axis_off()

        fig.tight_layout()
        fig.savefig(summary_dir / f'regime_map_{v}.png')
        plt.close(fig)

    base = variant_tables[args.variants[0]][['sweep', 'quota', 'x', 'y', 'regime']].rename(columns={'regime': args.variants[0]})
    piv = base.copy()
    for v in args.variants[1:]:
        right = variant_tables[v][['sweep', 'quota', 'x', 'y', 'regime']].rename(columns={'regime': v})
        piv = piv.merge(right, on=['sweep', 'quota', 'x', 'y'], how='outer')

    rows = []
    for i, va in enumerate(args.variants):
        for vb in args.variants[i + 1:]:
            valid = piv[[va, vb]].dropna()
            total = int(len(valid))
            changed = int((valid[va] != valid[vb]).sum())
            rows.append({
                'variant_a': va,
                'variant_b': vb,
                'cells_compared': total,
                'cells_changed': changed,
                'change_frac': float(changed / total) if total > 0 else 0.0,
            })
    shift = pd.DataFrame(rows)
    shift.to_csv(summary_dir / 'regime_shift_table.csv', index=False)

    print(f'Wrote {summary_dir / "regime_shift_table.csv"}')
    for v in args.variants:
        print(f'Wrote {summary_dir / f"regime_map_variant_{v}.csv"}')
        print(f'Wrote {summary_dir / f"regime_map_{v}.png"}')


if __name__ == '__main__':
    main()
