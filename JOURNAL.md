# project journal

religion-code-geometry ABM: endogenous enforcement delegation in religious communities

---

## 2026-02-12 (day 1) — project bootstrap + rapid model evolution v0→v2.1

### session 1: scaffold and base model (15:25–17:01)
- created project structure: `src/`, `scripts/`, `runs/`
- first smoke runs: `runs/smoke/`, `runs/high_sigma/`, `runs/low_sigma/`
- wrote `scripts/aggregate.py` (16:31) — first aggregation pipeline

### session 2: base model v0 (18:48)
- `src/religion_fundamentalism_abm.py` — 356 lines
- costly signaling on scale-free network (Barabasi-Albert)
- agents have ITC (internal theological commitment) and EPC (external practice commitment)
- sigma=0.75 makes EPC account for 75% of moral perception
- ran batch: `batch_20260212_163212/`
- wrote `aggregate_enforcement_concentration.py` (18:50) — Gini + top-k punishment share

### session 3: v1.1 refinements (21:14)
- `src/religion_fundamentalism_abm_v1_1.py` — 376 lines
- minor parameter refinements
- ran phase sweep: `batch_v1_1_phase_20260212_211614/`
- sigma sweep analysis: `aggregate_sigma.py` (19:21)

### session 4: v2 heresy/apostasy + v2.1 exit friction (22:30–23:41)
- `src/religion_fundamentalism_abm_v2.py` — 554 lines (22:30)
  - added heresy detection and apostasy dynamics
  - agents can now exit the community
- ran heresy/apostasy batches (4 runs between 22:26–22:39)
- `scripts/aggregate_v2.py` (22:32) + `aggregate_v2_regimemap.py` (23:15)
- `src/religion_fundamentalism_abm_v2_1.py` — 575 lines (23:41)
  - added exit friction parameter
  - ran: `batch_v2_1_exitfriction_20260212_231418/`
  - `aggregate_v2_1.py` (23:42)

**day 1 total: 4 model versions (v0, v1.1, v2, v2.1), ~7 batch runs, base dynamics established**

---

## 2026-02-13 (day 2) — regime discovery + enforcement delegation v2.2→v2.5a

### session 5: v2.2 regime grid (03:20)
- `src/religion_fundamentalism_abm_v2_2.py` — 638 lines
- systematic regime grid exploration
- ran: `batch_v2_2_regimegrid_20260213_032227/`
- `aggregate_v2_2_regimegrid.py` (03:21)

### session 6: v2.3 mixed regime search (04:32)
- `src/religion_fundamentalism_abm_v2_3.py` — 667 lines
- searching for mixed regimes in parameter space
- ran: `batch_v2_3_search_*` (multiple), `batch_v2_3_confirm_*`
- `aggregate_v2_3_confirm.py` (04:34), `search_mixed_regime_v2_3.py` (04:35)

### session 7: v2.3.1 boundary refinement (06:17)
- `src/religion_fundamentalism_abm_v2_3_1.py` — 690 lines
- refined regime boundaries, minority/majority counting
- ran: `batch_v2_3_1_boundaries_20260213_062318/`
- `aggregate_v2_3_1_minority.py` + `aggregate_v2_3_1_boundaries.py` (06:20)

### session 8: v2.4 internal army / enforcer delegation (07:48)
- `src/religion_fundamentalism_abm_v2_4.py` — 803 lines (+113 lines from v2.3.1)
- **key addition: internal army / enforcer delegation mechanism**
- agents can now accumulate institutional capital and delegate punishment
- ran: `batch_v2_4_internal_army_20260213_075201/`
- `aggregate_v2_4_minority.py` (07:50)

### session 9: v2.5 monopoly on enforcement (09:01) — MAIN MANUSCRIPT MODEL
- `src/religion_fundamentalism_abm_v2_5.py` — 886 lines
- **monopoly-on-enforcement mechanism + literalism trait (L)**
- high-L agents become enforcers through patronage, concentrating >80% of punishment in <5% of population
- this is the model described in the paper
- ran: `batch_v2_5_monopoly_20260213_090212/`
- `aggregate_v2_5_minority.py` (09:01), `aggregate_v2_5_boundaries.py` (09:52)
- `reclassify_regimes_threshold_sensitivity.py` (09:53)

### session 10: v2.5a hardening probe (09:51)
- `src/religion_fundamentalism_abm_v2_5a.py` — 990 lines (variant with probing)
- hardening runs: `batch_v2_5a_hardening_20260213_095416/`
- `aggregate_v2_5a_minority.py` (09:51)

### session 11: independent code audit (09:41)
- `AUDIT_REPORT.md` — 518 lines
- independent verification of all theoretical claims against code
- verified: costly signaling (sigma=0.75), threat-enforcement linearity, exit barriers (exponent=2.5)
- verified: monopoly concentration — top-5 agents >80% punishment share, Cohen's d=2.241

**day 2 total: 5 model versions (v2.2→v2.5a), audit report, main manuscript model identified (v2.5)**

---

## 2026-02-14 (day 3) — confirmatory sweep + module extensions v2.6→v2.7

### session 12: v2.5 corrected confirmatory sweep (12:49–15:21)
- finalized `src/religion_fundamentalism_abm_v2_5.py` (12:49, minor corrections)
- `scripts/analyze_v2_5_corrected.py` (12:51)
- `scripts/run_v2_5_corrected_sweep.py` (13:15) — **72 cells x 5 seeds = 360 runs**
- produced results:
  - `results/v2.5_corrected_baseline/` (12:59) — 30-seed baseline
  - `results/v2.5_ablation_fixed_y0/` (12:59) — fixed-y0 ablation, 30 seeds
  - `results/v2.5_corrected_sweep/` (13:35)
  - `results/v2.5_corrected_sweep_regime_search/` (13:50)
  - `results/v2.5_corrected_sweep_regime_search_fast/` (14:11)
  - `results/v2.5_corrected_sweep_capture_probe/` (14:06) — capture-focused timeseries
- `scripts/build_v2_5_phase_bundle.py` (15:07) — phase table + regime maps
- `scripts/run_v2_5_corrected_sweep_regime_search.py` (15:07)
- **key result: three-regime confirm** → `results/v2.5_corrected_three_regime_confirm/`
  - hierarchical regimes found: QUIET (26 cells), MIXED (36), COLLAPSE (9), CAPTURE_HIERARCHICAL (1)
  - seed-level: QUIET=137, MIXED=166, COLLAPSE=45, CAPTURE=12
  - median top-5 punishment share: 0.856
  - median top-10 punishment share: 0.971
  - Cohen's d (literalism enrichment, all runs): 1.960
  - Cohen's d (literalism enrichment, MIXED only): 2.169

### session 13: v2.6 doctrinal retention module (16:05–17:00)
- `src/religion_fundamentalism_abm_v2_6.py` — 910 lines (16:10)
- added doctrinal retention / plasticity module (alpha parameter)
- `scripts/run_v2_6_retention_sweep.py` (16:05)
- `scripts/validate_v2_6.py` (16:06)
- `scripts/summarize_v2_6_ablation.py` (16:17), `compare_v2_6_v25_recovery.py` (16:17)
- results (all ~16:13–17:30):
  - `results/v2.6_validation/`
  - `results/v2.6_ablation_alpha_only/`, `v2.6_ablation_delta_only/`, `v2.6_ablation_v25_recovery/`
  - `results/v2.6_retention_sweep/`
  - `results/v2.6_delta_threshold_sweep/`

### session 14: v2.6b membership module (17:34–18:25)
- `src/religion_fundamentalism_abm_v2_6b.py` — 915 lines (17:34)
- added membership benefit module (mu parameter)
- `scripts/run_v2_6b_membership_sweep.py` (17:35)
- `scripts/validate_v2_6b.py` (17:36), `summarize_v2_6b_ablation.py` (17:36)
- results:
  - `results/v2.6b_validation/` (17:39)
  - `results/v2.6b_ablation_mu/` (18:17), `v2.6b_ablation_delta/` (18:20), `v2.6b_ablation_interaction/` (18:24)
  - `results/v2.6b_membership_sweep/` (18:25)

### session 15: v2.7 endogenous delta — experimental (19:37–23:29)
- `src/religion_fundamentalism_abm_v2_7.py` — 947 lines (21:59)
- endogenous delta: enforcement power evolves based on community dynamics
- `scripts/analyze_v2_7_emergence_ablation.py` (19:37)
- `scripts/summarize_v2_7_endogenous_delta.py` (19:58)
- `scripts/run_v2_7_endogenous_delta_sweep.py` (22:00)
- `scripts/validate_v2_7.py` (22:01)
- results:
  - `results/v2.7_ablation_emergence/` (21:51)
  - `results/v2.7_endogenous_delta_sweep/` (21:51)
  - `results/v2.7_validation/` (22:03)
  - `results/v2.7b_endogenous_delta_sweep_gated/` (23:29) — gated variant

**day 3 total: confirmatory sweep (360 runs), 3 new modules (v2.6, v2.6b, v2.7), all with ablations and validation**

---

## 2026-02-15 (day 4) — sigma check + phase bundle documentation

- `results/v2.5_sigma025_baseopp03_check/` (06:11) — targeted sigma=0.25 / base_opp=0.3 check
- `results/v2.5_corrected_three_regime_confirm/phase_bundle/RESULTS_V2_5_PHASE_BUNDLE.md` (22:31) — documented phase bundle results with verified cell counts and concentration metrics

---

## 2026-02-16 (day 5) — publication figures + project packaging

### session 16: figure generation (07:54–09:09)
- `scripts/build_v2_5_publication_figures.py` (07:55) — generates all 5 publication figures (PNG + PDF)
- generated figures in `results/v2.5_corrected_three_regime_confirm/figures_publication/`:
  - `fig1_phase_map_hierarchical` — phase diagram (4 regimes across 72 cells)
  - `fig2_regime_counts` — cell-majority and seed-level regime frequencies
  - `fig3_concentration_by_regime` — punishment concentration (Gini, top-5, top-10)
  - `fig4_regime_timeseries` — representative trajectory per regime
  - `fig5_literalism_enrichment` — Cohen's d distributions for enforcer L enrichment
  - `FIGURE_CAPTIONS.md` — full captions for all figures

### session 17: validation + packaging (09:04–09:09)
- `scripts/validate_figures_from_csv.py` (09:04) — CSV-only figure validation
- `requirements.txt` (09:03) — pinned all dependencies
- `LICENSE` (09:03) — MIT
- `Makefile` (09:04) — build automation
- `CITATION.cff` (09:06) — citation metadata
- `reproduce.sh` (09:09) — one-command reproduction from CSVs
- `README.md` (09:09) — final project documentation
- `MANIFEST.txt` (09:06) — figure manifest

**day 5 total: project is publication-ready. all figures, docs, and reproduction pipeline in place.**

---

## 2026-02-20 (day 9) — codex-mod: hotfix + scaleup experiments

### codex-mod/hotfix (16:59–17:00)
- staged v2.7 fixes in isolated `codex-mod/hotfix/` directory (no changes to main codebase)
- `hotfix/scripts/run_v2_7_endogenous_delta_sweep.py` (16:59)
- `hotfix/scripts/analyze_v2_7_emergence_ablation.py` (16:59)
- `hotfix/scripts/summarize_v2_7_endogenous_delta.py` (17:00)
- `hotfix/README.md` (17:00) — documented fixes:
  1. regime classification now uses `punish_intensity_step` over `punish_rate` fallback
  2. full capture condition: exit_rate<=0.20, fund_prevalence>=0.10, punishment>=0.10
  3. empty-result KeyError guard
  4. consistent consensus threshold (ceil)
  5. added `--verbose-subprocess` option

### codex-mod/scaleup (17:25–18:00)
- formal model spec: `spec/model_spec_v2_7_scaleup.md` (17:25)
- v2.8 multiplex spec: `spec/model_spec_v2_8_multiplex.md` (17:54)
- benchmark harness: `scripts/benchmark_v2_7.py` (17:41)
- ML surrogate pipeline: `scripts/build_surrogate_from_sweeps.py` (17:32)
- v2.8 multiplex simulator: `scripts/simulate_v2_8_multiplex.py` (17:54)
- v2.8 benchmark: `scripts/benchmark_v2_8_multiplex.py` (17:53)
- v2.8 sweep pipeline: `scripts/run_v2_8_multiplex_sweep.py` (17:58)
- v2.8 summarizer: `scripts/summarize_v2_8_multiplex.py` (17:59)
- `scaleup/README.md` (18:00)
- **vision**: scale from 300→10^4-10^5 agents, multiplex networks (peer/institutional/media layers), dynamic rewiring, ML surrogates for tipping-point detection

### dynamic-nt ideas (17:01)
- `perpleixy-ideas.txt` updated — frontier ABM methodology notes (GPU acceleration, FLAME GPU 2, LLM-augmented agents, mean-field limits)

**day 9 total: codex-mod scaffold complete. hotfix staged for v2.7, scaleup roadmap + v2.8 multiplex prototype built.**

---

## 2026-02-20 — repo audit (this session)

### audit findings
- **total repo size**: 9.5 GB (2.0 GB committed results, 4.9 GB gitignored runs, 1.7 GB codex-mod)
- **13 model versions** across `src/` (v0→v2.7), 9,307 lines total
- **50+ scripts** for sweeps, aggregation, validation, figures
- **24 versioned result directories** under `results/`
- main manuscript model: v2.5 (monopoly on enforcement, literalism trait)
- independent audit (`AUDIT_REPORT.md`) confirms all theoretical claims
- reproduction pipeline works from committed CSVs in ~30 seconds
- codex-mod (hotfix + scaleup) is isolated and untouched
- stack: Mesa 3.4.2, Python 3.12.4, NumPy, pandas, NetworkX, Matplotlib

### status
- **manuscript pipeline (v2.5)**: stable, reproducible, publication-ready
- **module extensions (v2.6, v2.6b)**: validated with ablations, committed
- **experimental (v2.7)**: hotfix staged in codex-mod, not merged
- **scaleup (v2.8)**: prototype in codex-mod, 50k agent benchmarks running

---

---

## 2026-02-20 — punish_rate denominator fix (session 2)

### bug identified
- `punish_rate` in `metrics()` computed over all agents including exited
- with exit rates of 0.59-0.86, this dilutes punishment intensity by 60-70%
- regime classifier threshold `max_punish >= 0.10` causes false QUIET classifications
- **same bug in all 4 model versions**: v2.5 (line 592), v2.6 (line 610), v2.6b (line 612), v2.7 (line 636)
- exited agents always have `punished = 0` (reset on exit), so numerator is correct — only denominator is wrong

### fix applied
- `punish_rate = float((punished[~exited] > 0).mean()) if (~exited).any() else 0.0`
- applied to all 4 versions: v2.5.1, v2.6.1, v2.6b.1, v2.7.1
- reconstruction formula for existing data: `active_punish_rate = punish_rate / (1 - exit_rate)`

### reclassification results (no simulations rerun)
- created `scripts/reclassify_regimes.py` — recomputes active-only punish_rate from existing CSVs
- **baseline 72-cell sweep (v2.5)**: 88/360 runs reclassified (24.4%), all QUIET→MIXED
  - cell-level: QUIET 26→8, MIXED 37→55, COLLAPSE 9→9
  - MIXED now 76% of cells (was 51%)
- **v2.7 drift sweep**: 0/1350 reclassified (already above threshold)
- **v2.7b gated sweep**: 0/1350 reclassified
- **v2.7 emergence ablation**: 0/60 reclassified
- cross-validation vs v2.7 `punish_intensity_step`: correlation=1.0000, MAE=0.000090

### validation
- 5 fresh runs with fixed v2.5.1 at affected params (sigma=0.75, pi=0.25, base_opp=3.0)
- all 5 report max_punish > 0.10, consistent with reclassification script

### manuscript impact
- **strengthens central claim**: enforcement concentration is MORE widespread than reported
- MIXED regime dominates phase map (76% vs 51% before)
- concentration metrics (top-5 share, enforcer share, Cohen's d) UNAFFECTED — computed from agent_summary.csv, not per-step metrics
- CAPTURE/COLLAPSE counts unchanged
- see `results/reclassification_report.md` for full analysis

### files produced
- `scripts/reclassify_regimes.py`
- `results/reclassification_report.md`
- `results/v2.5_corrected_three_regime_confirm/reclassified_seed_results.csv`
- `results/v2.5_corrected_three_regime_confirm/reclassified_summary.csv`
- `results/v2.7_endogenous_delta_sweep/reclassified_seed_results.csv`
- `results/v2.7_endogenous_delta_sweep/reclassified_summary.csv`
- `results/v2.7b_endogenous_delta_sweep_gated/reclassified_seed_results.csv`
- `results/v2.7b_endogenous_delta_sweep_gated/reclassified_summary.csv`
- `results/v2.7_ablation_emergence/reclassified_seed_results.csv`
- `results/v2.7_ablation_emergence/reclassified_summary.csv`
- `results/validation_fix_v2_5_1/` (5 validation runs)

---

## 2026-02-20 — codex-mod scaleup audit + bugs found (session 3)

### audit of codex-mod/scaleup outputs
- audited all code, specs, and results produced by codex in `codex-mod/scaleup/`
- v2.8 multiplex simulator works: 3-layer network, dynamic rewiring, vectorized NumPy
- ML surrogate trained on v2.7 data: 90.6% accuracy regime classifier
- **however, 3 critical bugs identified in the codex sweep:**

### bugs found in codex v2.8 sweep
1. **parameter mismatch** (critical): codex used default exit params, not v2.5's tuned BEST_PARAMS (exit_block_exponent=5.98 vs 2.5 default, exit_cost=1.0 vs 0.40, membership_benefit=0.063 vs 0.03). this caused universal COLLAPSE in Round 1 (all 270 runs). codex then spent 3 rounds manually tuning knobs to compensate.
2. **policing throughput mismatch** (critical): v2.8 scans 1 institutional neighbor per policing agent; v2.5 scans up to 3. this 3x reduction suppressed punishment intensity below the 0.10 MIXED threshold.
3. **CAPTURE threshold error**: v2.8 used fund_prevalence >= 0.10; v2.5 uses >= 0.90. all 180 "CAPTURE" runs in Round 4 would reclassify as MIXED under correct threshold.

### corrected v2.8 sweep (72 cells × 5 seeds = 360 runs)
- fixes applied to simulator: added BEST_PARAMS CLI args, 3x policing, correct threshold
- `scripts/run_v2_8_corrected_sweep.py` — new sweep script with hardcoded BEST_PARAMS
- parameter grid: sigma={0.25,0.75,0.95}, pi={0.05,0.25}, base_opp={0.3,0.6,0.9}, eta={0.0,0.2}, delta0={0.0,0.1}
- n=10,000, steps=450

### corrected results
- cell-level: QUIET 45 (62.5%), COLLAPSE 18 (25%), MIXED 9 (12.5%), CAPTURE 0
- **three regimes present at n=10,000** (COLLAPSE/MIXED/QUIET)
- MIXED requires eta=0.2 (endogenous delta) — no MIXED without lock-in
- enforcer share in MIXED runs: 98.5% (higher than v2.5's 91.9%)
- CAPTURE absent: fund_prevalence peaks at ~10%, far from 0.90 threshold
- sigma=0.95 always QUIET: high legibility enables self-policing

### key findings (corrected)
1. enforcement concentration survives at scale — enforcer share 98.5% on uniform-degree multiplex
2. endogenous delta is NECESSARY for enforcement at scale (not just amplifying as in v2.5)
3. CAPTURE does not occur at n=10k — enforcement exists without full radicalization
4. high legibility (σ=0.95) suppresses enforcement by enabling self-policing
5. intermediate legibility (σ=0.75) + low outside options + delta drift = MIXED

### files produced/modified
- `codex-mod/scaleup/scripts/simulate_v2_8_multiplex.py` — added CLI args + 3x policing fix
- `scripts/run_v2_8_corrected_sweep.py` — new corrected sweep script
- `results/v2.8_corrected_sweep/` — 360 runs with correct parameters
- `results/codex_scaleup_report.md` — rewritten from actual data (10 sections)

---

## 2026-02-20 — path B planning (session 3, continued)

### discussion: next direction after paper 1
- paper 1 (v2.5 manuscript) is closed — not being touched
- codex scaleup results are supplementary icing
- **path B selected**: apply CODE geometry framework to real-world systems
- goal: make ABM simulations credible to skeptical reviewers ("pundits")

### four credibility options identified (to be discussed)
1. **historical case studies** — calibrate model to specific systems (early Christianity, Soviet Marxism, Wahhabism)
2. **contemporary empirical** — survey/social media data for parameter estimation
3. **comparative typology** — map different canon systems to CODE parameter space
4. **policy/predictive** — diagnostic tool for organizational capture risk

### status: codex report written, awaiting Path B discussion

---

## 2026-02-20 (continued) — CAPTURE threshold bug fix + structural impossibility finding

### pervasive CAPTURE threshold bug (0.10 vs 0.90)
- the v2.6, v2.6b, v2.7, v2.7b, and v2.8 sweep scripts all used `fund_prevalence >= 0.10` for CAPTURE classification
- the correct threshold (used in v2.3, v2.4, v2.5) is `>= 0.90`
- this created 465 phantom "CAPTURE" runs in v2.7 and 466 in v2.7b — ALL actually MIXED
- the ML surrogate (90.6% accuracy) was trained on these wrong labels
- **fixed in 8 files**: all sweep/analysis scripts for v2.6, v2.6b, v2.7, v2.8 + codex copies

### structural CAPTURE impossibility — the real finding
- with the correct 0.90 threshold, CAPTURE has NEVER occurred in any model version at any scale
- max fund_prevalence across all runs: v2.5=0.157, v2.7=0.161, v2.8=0.105
- **root cause**: radicalization (r, b increase) only happens through the punishment feedback loop
- once enforcer monopoly activates, only the 8% enforcer class can punish → only they radicalize
- structural ceiling: fund_prevalence ≈ enforcer_quota_frac ≈ 8%
- agent-level evidence: enforcers reach r=1.0, b=1.0 (100%); non-enforcers max F=0.42 (0% above threshold)
- meanwhile practice (x) spreads perfectly: 98.7% of non-enforcers have x > 0.90
- **the model has no channel from high practice → high enforcement readiness**

### implication for v2.9
- CAPTURE requires a mass radicalization mechanism independent of the punishment feedback loop
- candidate: practice-to-enforcement spillover ("sunk-cost radicalization" — investment in practice creates intolerance of deviants)
- the conformity engine already works; it just needs to feed into enforcement readiness

### scaleup report updated
- section 5.3: ML surrogate caveat (phantom CAPTURE class)
- section 6.3: rewritten — structural impossibility, not scaling effect
- section 6.6: corrected — MIXED/QUIET boundary learnable
- section 8: limitations updated
- section 9: convergence corrections expanded (item 3 and new item 4)

---

*journal created 2026-02-20. retroactive entries reconstructed from filesystem timestamps.*
*all times are CST (UTC-6).*
