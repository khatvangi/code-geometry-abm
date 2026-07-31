# Code-Geometry ABM: Enforcement Activation and Exit Foreclosure in Codified Moral Communities

An agent-based model that separates two structural conditions for durable capture in rule-governed communities: **activation** of an enforcement apparatus, and **foreclosure** of members' exit. Companion code for the manuscript *"Activation and Foreclosure: Separating Screening from Exit Costs in Codified Moral Communities."*

Agents on a scale-free network observe conduct, sanction deviation, and decide whether to remain. An enforcement apparatus forms only where conduct is observable and enforcement is rewarded; the threshold is joint, and neither condition alone suffices. Punishment then concentrates in a small cadre, but that concentration is a product of institutional design rather than of differences among agents: the top 5% of active agents deliver **0.580** of all punishment under the full privilege architecture and **0.091** without it. An active apparatus retains members only where exit is foreclosed -- with exit open, no run reaches capture in any of the 63 parameter cells despite an activation rate of 0.598, while imposed exit closure raises capture to **0.889**.

## Repository layout

```
src/                                model code (12 versions, v0 through v2.7)
scripts/                            run scripts, sweep drivers, aggregation, validation
results/                            committed result sets (CSV data)
  v2.5_methodology_paper_canonical/ canonical methodology-paper artifacts (built deterministically)
  v2.5_corrected_three_regime_confirm/ legacy frozen reproducibility artifact (preserved unchanged)
  v2.5_*/                           ablation, baseline (other v2.5 dirs)
  v2.6_*/                           doctrinal retention module + ablations
  v2.6b_*/                          membership module + ablations
figures/                            publication-ready PDF figures + LaTeX tables
AUDIT_REPORT.md                     independent code audit
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

python scripts/build_methodology_paper_canonical.py
python scripts/build_methodology_paper_figures.py
python scripts/validate_methodology_figures.py
```

### Path portability note

The legacy `results/v2.5_corrected_three_regime_confirm/sweep_seed_results.csv`
stores absolute paths from the original run environment in its `run_dir`
column. `reproduce.sh` rewrites these prefixes to the local clone path on
first run; this affects paths only, not numeric data. The canonical
methodology-paper directory uses repo-relative paths from the start, so this
rewrite is needed only for the legacy directory.

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
| Phase map (Fig 1) | `v2.5_methodology_paper_canonical/` | `phase_bundle/phase_table.csv` |
| Regime counts (Fig 2) | `v2.5_methodology_paper_canonical/` | `phase_bundle/regime_counts.csv` |
| Punishment concentration (Fig 3) | `v2.5_methodology_paper_canonical/` | `sweep_seed_results.csv` |
| Regime trajectories (Fig 4) | `v2.5_methodology_paper_canonical/` | `timeseries_regime_hier_*.csv` |
| Regime metrics (Table 5) | `v2.5_methodology_paper_canonical/` | `sweep_seed_results.csv` (Cohen's d via per-seed `agent_summary.csv`) |
| Baseline (30 seeds) | `v2.5_corrected_baseline/` | `regime_by_seed.csv` |
| Fixed-y0 ablation | `v2.5_ablation_fixed_y0/` | `ablation_comparison.csv` |
| Retention module | `v2.6_validation/` | validation outputs |
| Membership module | `v2.6b_validation/` | validation outputs |

Methodology paper headline counts (canonical hierarchical schema, cap=0.20,
active-rate corrected): **0 CAPTURE / 55 MIXED / 8 QUIET / 9 COLLAPSE** across
72 cells. The MIXED regime is characterized by within-cell concentration:
the top 5% of agents execute >80% of punishments, with literalism-enrichment
Cohen's $d \approx 2.1$ for enforcers vs non-enforcers.

Publication figures: `figures/figure{1..4}*.pdf`, `figures/table5_regime_metrics.tex`.

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
  title     = {Code-Geometry ABM: Enforcement Activation and Exit Foreclosure in Codified Moral Communities},
  year      = {2026},
  url       = {https://github.com/khatvangi/code-geometry-abm},
  note      = {DOI forthcoming}
}
```

## License

MIT License. See [LICENSE](LICENSE).
