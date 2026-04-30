# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Mesa-based agent-based model of **endogenous enforcement delegation** in religious
communities under external threat. Companion code for a PLOS ONE submission.
The canonical manuscript model is `src/religion_fundamentalism_abm_v2_5.py`;
later versions (v2.6, v2.6b, v2.7+) are bolt-on modules tested via separate
sweeps and ablations.

Top-level numerical claim of the model: a small cadre of high-literalism agents
emerges as enforcers via patronage and institutional capital, concentrating
>80% of punishment acts in <5% of agents — without any pre-assigned roles.

## Environment

- **Python 3.12.4** (pinned via `.python-version`)
- Pinned dependencies in `requirements.txt` (Mesa 3.4.2, numpy 2.4.2,
  pandas 3.0.0, networkx 3.6.1, matplotlib 3.10.8). Versions are pinned so that
  committed CSVs reproduce bit-for-bit; do not bump them casually.
- Virtual env lives at `.venv/`. Activate with `source .venv/bin/activate`
  before running anything.

## Common commands

```bash
# one-shot: regenerate publication figures from committed CSVs (~30s)
./reproduce.sh
# or
make reproduce

# just figures (assumes venv + data already in place)
make figures

# validate that all expected figures + input CSVs exist
make validate
# == python scripts/validate_figures_from_csv.py

# run a single ABM simulation directly (one cell of the sweep grid)
.venv/bin/python src/religion_fundamentalism_abm_v2_5.py \
    --outdir runs/smoke --steps 450 --n 350 --graph scale_free \
    --seed 1 --sigma 0.75 --pi_reward 0.22 --no_movie

# full v2.5 confirmatory sweep (~4–6 h on 64 cores; 72 cells × 5 seeds)
python scripts/run_v2_5_corrected_sweep.py

# v2.6 / v2.6b module sweeps + ablations
python scripts/run_v2_6_retention_sweep.py
python scripts/run_v2_6b_membership_sweep.py
```

There is no test framework — "validation" means running
`scripts/validate_figures_from_csv.py` and the per-version
`scripts/validate_v2_*.py` scripts, which check that expected outputs exist
and are non-empty.

## Architecture

### Three-layer pipeline

```
src/religion_fundamentalism_abm_v*.py    ← single-run simulator (CLI)
        │  produces per-run metrics.csv + agent_summary.csv
        ▼
scripts/run_*_sweep.py                    ← grid runner; spawns workers
        │  ThreadPoolExecutor calls the model CLI as subprocess for
        │  each (sigma, pi_reward, exit_opportunity_base, seed) cell
        ▼
scripts/aggregate_*.py / build_*.py       ← collect → CSV summaries → figures
```

Each model `main()` writes exactly two files into `--outdir`:
`metrics.csv` (one row per timestep, ~32 columns) and
`agent_summary.csv` (one row per agent, ~17 columns). All downstream
analysis assumes that contract.

### Model versions are append-only

Old model files are NOT deprecated — they are reproducibility artifacts.

| File | Role |
|---|---|
| `religion_fundamentalism_abm_v2_5.py` | **Primary manuscript model.** Monopoly-on-enforcement + literalism trait. |
| `*_v2_6.py` | Adds doctrinal-retention module (alpha, delta). |
| `*_v2_6b.py` | Adds membership-benefit module (mu). |
| `*_v2_7.py`, `*_v2_9.py` | Experimental: endogenous delta, acquiescence calibration. NOT in manuscript. |
| `*_v2_5a.py`, `*_v2_3_1.py`, etc. | Frozen snapshots tied to specific sweeps in `results/`. |

**Do not edit old model files in place.** If a fix is needed for the active
manuscript model, edit `v2_5.py`, then rerun the relevant sweep into a new
result directory. Editing v2.4 would silently invalidate any committed CSV
that was produced from it.

### Results layout and what's committed

`runs/` and most of `results/` are gitignored. The repo whitelists specific
curated result directories via `!`-rules in `.gitignore` — those are the
final manuscript-grade outputs.

**Canonical methodology-paper directory** (the source for `manuscript/manuscript.tex`'s
figures, tables, and headline numbers):

```
results/v2.5_methodology_paper_canonical/
├── sweep_seed_results.csv          # one row per (cell, seed) under cap=0.20 + active-rate
├── sweep_summary.csv               # cell-level aggregates
├── phase_bundle/                   # phase table + regime counts → fig 1, 2
├── timeseries_regime_hier_*.csv    # per-seed-per-step rows tagged with regime → fig 4
└── sigma_*/pi_*/base_opp_*/seed_*/ # relative symlinks to the legacy frozen run dirs
```

This directory is built deterministically by
`scripts/build_methodology_paper_canonical.py` (no CLI flags) from the
immutable v2.5 confirmatory sweep run dirs at
`results/v2.5_corrected_three_regime_confirm/`. The legacy directory is
preserved as a frozen reproducibility artifact but is no longer the figure
source. The 2026-04-29 cap-divergence diagnosis (see
`synthesis/SYNTHESIS_WORKING_DOC.md` §15.3) explains why a canonical
rebuild was needed.

When adding a new sweep that should be committed, also add a matching
`!results/<your_dir>/**` line in `.gitignore`.

### Path portability quirk

`sweep_seed_results.csv` stores absolute paths from the original run
environment (the `run_dir` column points at
`/storage/social-science/religion-code-geometry-abm/...`).
`reproduce.sh` rewrites this prefix to the local clone path on first run via
`sed`, saving a `.csv.bak` backup. The numeric data is unchanged. If a fresh
sweep run is committed, regenerate this CSV with the new absolute paths
intact — downstream figure scripts (e.g. `build_v2_5_publication_figures.py`)
read per-seed `agent_summary.csv` files using `run_dir` as the base.

### Regime classification — the active-rate gotcha and cap divergence

Regimes are labelled `COLLAPSE`, `CAPTURE_HIERARCHICAL`, `MIXED`, `QUIET`.
Two corrections must be applied jointly:

1. **Active-rate.** The raw `punish_rate` in `metrics.csv` is
   `punished / N_total` and includes exited agents (always `punished = 0`).
   Use `active_punish_rate = punish_rate / max(1 - exit_rate, ε)` —
   this is the canonical statistic. `scripts/reclassify_regimes.py`
   computes it from existing metrics.csv files.
2. **`capture_exit_cap = 0.20`.** The hierarchical CAPTURE gate uses
   `exit_rate ≤ 0.20`, matching `manuscript/manuscript.tex` §6.10. The
   frozen v2.5 confirmatory sweep was launched with `--capture-exit-cap 0.30`
   (see `results/v2.5_corrected_three_regime_confirm/sweep_report.txt`),
   which loosened the gate and produced 1 spurious CAPTURE cell. Under
   the canonical 0.20 + active-rate the cell-majority counts are
   **0 CAPTURE / 55 MIXED / 8 QUIET / 9 COLLAPSE** (vs the manuscript-headline
   1 CAPTURE / 36 MIXED / 26 QUIET / 9 COLLAPSE under the legacy
   uncorrected counts).

The canonical pipeline `scripts/build_methodology_paper_canonical.py`
hard-codes both corrections so they cannot drift; downstream figures and
tables read from `results/v2.5_methodology_paper_canonical/`. The codex-mod
hotfix exists for the same reason on the v2.7 branch.

## Working conventions

- **Never run with synthetic data.** All committed CSVs come from real ABM
  runs with fixed seeds. Don't substitute placeholder numbers into figure
  scripts to "show what it would look like."
- **Sweep parameters that affect classification** (`capture_exit_cap`,
  active-rate corrections, regime thresholds) must be passed as explicit
  arguments to the aggregator, never set as function attributes or read
  from `getattr` defaults. Sweep-time parameter values must be recorded in
  `sweep_report.txt` at sweep launch, and downstream pipelines must hard-code
  the canonical values rather than read flags. The 2026-04-29 cap-divergence
  diagnosis showed how a non-default `--capture-exit-cap 0.30` flag silently
  produced a spurious "1 CAPTURE cell" headline that the manuscript text did
  not match.
- Append a Q&A entry to `HISTORY.md` (`## YYYY-MM-DD` then `**Q:**`/`**A:**`)
  per session per the global convention. `JOURNAL.md` is the longer-form
  development journal — read it for chronological context across model
  versions.
- Comments are lowercase; function names use `camelCase` for verbs
  (`findMeaning`, not `getMeaning` or `find_meaning`) per the user's global
  style — note that the existing simulation code uses snake_case throughout,
  so match the file you're editing.
- The codebase uses matplotlib directly (it predates the seaborn/plotly
  preference). When adding *new* analysis figures, prefer seaborn for static
  publication output and plotly for interactive notebooks. Don't migrate
  existing publication figures — they are frozen artifacts.

## What's outside the main pipeline

- `codex-mod/hotfix/` and `codex-mod/scaleup/` — experimental scaffolds
  (v2.7 hotfixes, surrogate models, multiplex extension). Self-contained;
  not used by `reproduce.sh`. Treat as a separate workspace.
- `manuscript/` — LaTeX sources for the PLOS ONE submission
  (`manuscript.tex`, `s1_text.tex`, `cover_letter.tex`) plus compiled PDFs.
- `data/cross_national_data.csv` — small cross-national regression dataset
  (WVS / RAS / World Bank GDP) used by revision-stage analyses, separate
  from the ABM runs.
- `AUDIT_REPORT.md` — independent code audit of v2.5 claims.
