# Code-Geometry ABM: Endogenous Enforcement Delegation in Religious Communities

An agent-based model of how **geometric symmetry in costly signaling** produces **endogenous enforcement delegation** and **punishment concentration** in religious communities -- without pre-assigned enforcer roles.

Agents on a scale-free network cultivate internal belief (ITC) and visible ritual practice (EPC) under periodic external threat. When threat is high, institutional authority rises and a monopoly-on-enforcement mechanism activates: a small cadre of high-literalism agents emerges as enforcers through patronage and institutional capital accumulation, concentrating >80% of punishment acts in <5% of the population. This concentration is not designed in -- it arises from the interaction of costly signaling legibility, exit barriers, and threat-driven authority.

## Repository layout

```
src/                    model code (12 versions, v0 through v2.7)
scripts/                run scripts, sweep drivers, aggregation, validation
results/                committed result sets (CSV data + publication figures)
  v2.5_*/               confirmatory sweep, ablation, baseline (5 dirs)
  v2.6_*/               doctrinal retention module + ablations (5 dirs)
  v2.6b_*/              membership module + ablations (5 dirs)
  figures_publication/   publication-ready PNG + PDF figures
AUDIT_REPORT.md         independent code audit
```

### What is NOT in this repo

- `runs/` (raw simulation output, ~5 GB) -- gitignored; regenerate via scripts
- `tmp/` (scratch) -- gitignored
- `.venv/` (virtual environment) -- gitignored; recreate via `requirements.txt`
- `v2.7*` results -- experimental; not part of the current manuscript

## Quick reproduce (figures from committed CSV only)

This regenerates all publication figures from the committed CSV data.
No simulation reruns required. Takes ~30 seconds.

```bash
git clone https://github.com/khatvangi/code-geometry-abm.git
cd code-geometry-abm
./reproduce.sh
```

Or step by step:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/build_v2_5_publication_figures.py \
  --root results/v2.5_corrected_three_regime_confirm \
  --outdir results/v2.5_corrected_three_regime_confirm/figures_publication

python scripts/validate_figures_from_csv.py
```

**Note:** The figure build script reads `agent_summary.csv` paths from
`sweep_seed_results.csv`. These paths are rebased to the repo root
automatically by `reproduce.sh`. If running manually, ensure your working
directory is the repo root.

## Full rerun (expensive -- not required for review)

A full confirmatory sweep (72 parameter cells x 5 seeds = 360 runs)
takes ~4-6 hours on a 64-core machine. Each run produces ~450 timesteps
of 300 agents on a scale-free network.

```bash
# v2.5 confirmatory sweep
python scripts/run_v2_5_corrected_sweep.py

# v2.6 retention sweep + ablations
python scripts/run_v2_6_retention_sweep.py

# v2.6b membership sweep + ablations
python scripts/run_v2_6b_membership_sweep.py
```

**Do NOT rerun unless you need to verify stochastic reproducibility.**
All committed CSVs were generated with fixed seeds and are deterministic
for the pinned dependency versions.

## Key outputs

| Paper section | Result directory | Key file |
|---------------|-----------------|----------|
| Phase map (Fig 1) | `v2.5_corrected_three_regime_confirm/` | `phase_bundle/phase_table.csv` |
| Regime counts (Fig 2) | `v2.5_corrected_three_regime_confirm/` | `phase_bundle/regime_counts.csv` |
| Punishment concentration (Fig 3) | `v2.5_corrected_three_regime_confirm/` | `sweep_seed_results.csv` |
| Regime trajectories (Fig 4) | `v2.5_corrected_three_regime_confirm/` | `timeseries_regime_hier_*.csv` |
| Literalism enrichment (Fig 5) | `v2.5_corrected_three_regime_confirm/` | per-seed `agent_summary.csv` |
| Baseline (30 seeds) | `v2.5_corrected_baseline/` | `regime_by_seed.csv` |
| Fixed-y0 ablation | `v2.5_ablation_fixed_y0/` | `ablation_comparison.csv` |
| Retention module | `v2.6_validation/` | validation outputs |
| Membership module | `v2.6b_validation/` | validation outputs |

Publication figures: `results/v2.5_corrected_three_regime_confirm/figures_publication/`

## Model versions

| File | Key addition |
|------|-------------|
| `religion_fundamentalism_abm.py` | Base model (v0): costly signaling on networks |
| `_v1_1.py` | Minor refinements |
| `_v2.py` | Heresy/apostasy dynamics |
| `_v2_1.py` | Exit friction parameter |
| `_v2_2.py` | Regime grid exploration |
| `_v2_3.py` / `_v2_3_1.py` | Mixed regime search, boundary refinements |
| `_v2_4.py` | Internal army / enforcer delegation |
| `_v2_5.py` | **Monopoly on enforcement, literalism trait** (primary manuscript version) |
| `_v2_6.py` | Doctrinal retention module |
| `_v2_6b.py` | Membership benefit module |
| `_v2_7.py` | Endogenous delta (experimental) |

## Python version and dependencies

- **Python 3.12.4** (see `.python-version`)
- Dependencies pinned in `requirements.txt`
- Core stack: Mesa 3.4.2, NumPy 2.4.2, pandas 3.0.0, NetworkX 3.6.1, Matplotlib 3.10.8

## Citation

If you use this code, please cite:

```bibtex
@software{khatvangi2026codegeometry,
  author    = {Khatvangi, Kiran},
  title     = {Code-Geometry ABM: Endogenous Enforcement Delegation in Religious Communities},
  year      = {2026},
  url       = {https://github.com/khatvangi/code-geometry-abm},
  note      = {DOI forthcoming}
}
```

## License

MIT License. See [LICENSE](LICENSE).
