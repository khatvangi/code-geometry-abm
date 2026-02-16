# RESULTS_V2_5_PHASE_BUNDLE

- root: `/storage/social-science/religion-code-geometry-abm/results/v2.5_corrected_three_regime_confirm`
- n_cells: 72
- n_seed_runs: 360
- legacy_regimes_found: ['COLLAPSE', 'MIXED', 'QUIET']
- hierarchical_regimes_found: ['CAPTURE_HIERARCHICAL', 'COLLAPSE', 'MIXED', 'QUIET']
- three_regimes_legacy: False
- three_regimes_hierarchical: True

## Files
- `/storage/social-science/religion-code-geometry-abm/results/v2.5_corrected_three_regime_confirm/phase_bundle/phase_table.csv`
- `/storage/social-science/religion-code-geometry-abm/results/v2.5_corrected_three_regime_confirm/phase_bundle/regime_counts.csv`
- `/storage/social-science/religion-code-geometry-abm/results/v2.5_corrected_three_regime_confirm/phase_bundle/seed_regime_counts.csv`
- `/storage/social-science/religion-code-geometry-abm/results/v2.5_corrected_three_regime_confirm/phase_bundle/phase_map_legacy.png`
- `/storage/social-science/religion-code-geometry-abm/results/v2.5_corrected_three_regime_confirm/phase_bundle/phase_map_hierarchical.png`

## Verified Cell Counts (hierarchical)
- QUIET: 26
- MIXED: 36
- COLLAPSE: 9
- CAPTURE_HIERARCHICAL: 1

Source: `phase_table.csv` (`regime_majority_hier`) and `regime_counts.csv`.

## Seed-Level Regime Counts (hierarchical)
- QUIET: 137
- MIXED: 166
- COLLAPSE: 45
- CAPTURE_HIERARCHICAL: 12

Source: `seed_regime_counts.csv`.

## Confirmatory Concentration Metrics (360 seed-runs)
From `sweep_seed_results.csv`:

- median top-5 punishment share: `0.856087`
- median top-10 punishment share: `0.970924`
- median enforcer punishment share: `0.919077`

From all run-level `agent_summary.csv` files:

- Cohen's d (L enrichment, pooled all runs): `1.959809`
- Cohen's d (L enrichment, pooled MIXED runs only): `2.168559`

Note: if a section is specifically about active enforcement dynamics, use the MIXED-only d; if it summarizes the whole confirmatory sweep, use the pooled-all d.
