# Final Results Manifest

This repository snapshot includes final code and the key result sets used for the v2.5 corrected analysis.

Included result directories:

- `results/v2.5_corrected_three_regime_confirm/`
  - Final 5-seed confirmation sweep for three-regime demonstration.
  - Contains `sweep_summary.csv`, `sweep_seed_results.csv`, regime time series, and `phase_bundle/` outputs.
- `results/v2.5_corrected_baseline/`
  - Corrected baseline (30 seeds) outputs and comparison artifacts.
- `results/v2.5_ablation_fixed_y0/`
  - Fixed-`y0` ablation (30 seeds) outputs and comparison artifacts.
- `results/v2.5_corrected_sweep_regime_search_fast/`
  - Focused regime-search sweep used to identify collapse/capture-hierarchical boundary behavior.
- `results/v2.5_corrected_sweep_capture_probe/`
  - Capture-focused probe sweep and summaries.

Additional module results (v2.6/v2.6b):

- `results/v2.6_validation/` -- doctrinal retention module validation
- `results/v2.6_retention_sweep/` -- retention parameter sweep
- `results/v2.6_ablation_alpha_only/` -- alpha-only ablation
- `results/v2.6_ablation_delta_only/` -- delta-only ablation
- `results/v2.6_ablation_v25_recovery/` -- v2.5 recovery ablation
- `results/v2.6_delta_threshold_sweep/` -- delta threshold confirmation
- `results/v2.6b_validation/` -- membership module validation
- `results/v2.6b_membership_sweep/` -- membership parameter sweep
- `results/v2.6b_ablation_mu/` -- mu ablation
- `results/v2.6b_ablation_delta/` -- delta ablation
- `results/v2.6b_ablation_interaction/` -- interaction ablation

NOT included in this submission artifact:

- `v2.7*` results (endogenous delta, experimental) -- not part of the current manuscript
- `v2.5_corrected_sweep/`, `v2.5_corrected_sweep_regime_search/` -- intermediate exploratory runs
- `.log` and `.pid` files -- runtime artifacts, gitignored

Primary publication-ready files:

- `results/v2.5_corrected_three_regime_confirm/phase_bundle/phase_table.csv`
- `results/v2.5_corrected_three_regime_confirm/phase_bundle/regime_counts.csv`
- `results/v2.5_corrected_three_regime_confirm/phase_bundle/seed_regime_counts.csv`
- `results/v2.5_corrected_three_regime_confirm/phase_bundle/phase_map_legacy.png`
- `results/v2.5_corrected_three_regime_confirm/phase_bundle/phase_map_hierarchical.png`
- `results/v2.5_corrected_three_regime_confirm/phase_bundle/RESULTS_V2_5_PHASE_BUNDLE.md`

Publication figure set (cleaned + captioned):

- `results/v2.5_corrected_three_regime_confirm/figures_publication/fig1_phase_map_hierarchical.png`
- `results/v2.5_corrected_three_regime_confirm/figures_publication/fig2_regime_counts.png`
- `results/v2.5_corrected_three_regime_confirm/figures_publication/fig3_concentration_by_regime.png`
- `results/v2.5_corrected_three_regime_confirm/figures_publication/fig4_regime_timeseries.png`
- `results/v2.5_corrected_three_regime_confirm/figures_publication/fig5_literalism_enrichment.png`
- `results/v2.5_corrected_three_regime_confirm/figures_publication/FIGURE_CAPTIONS.md`
