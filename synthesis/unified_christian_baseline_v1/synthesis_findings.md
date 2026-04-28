# Synthesis Findings — Phase S1

**Phase:** Synthesis Phase S1 — Christian baseline rescoring
**Source data:** `unified_cases.jsonl` (16 cases), `regime_predictions_summary.csv`, `mismatches_report.md`
**Bundle:** `synthesis/inputs/from_nitrogen/` (case_export.jsonl, source_registry.jsonl, argument_templates.json, methodology_locked.md, EXPORT_NOTES.md, MANIFEST.csv, build_export.py, export_diagnostics.json — 8 files, sha256-verified against Nitrogen)
**Manuscript reference:** `synthesis/inputs/manuscript_plosone_v3/manuscript_PLOSONE.tex` + `S1_Text.pdf` (PLOS ONE submission package, canonical)
**Date:** 2026-04-27

---

## Headline recommendation

**Phase S2 should proceed.** The synthesis architecture in `SYNTHESIS_WORKING_DOC.md §5` survives contact with the 16 Christian cases — 15 of 16 are scoreable in the unified vocabulary; 1 (LR007) declines on scope grounds in a way that itself validates the architecture (Extension 4 is the named answer). The substantive match rate (9 of 12 informative cases = 75%) is consistent with a structurally-correct framework that has known scope limitations. The framework is not refuted; it is bounded, and the bounds are now explicit.

Phase S1 also surfaces three findings that change the synthesis plan beyond what `SYNTHESIS_WORKING_DOC.md` had specified:

- **A new Extension 5** (target-population modeling) is needed for 3 of 15 scored cases. This is unspecified in the working doc and should be added there.
- **The COLLAPSE regime label is too narrowly defined** in §6.10 — a Phase S5 manuscript-revision finding, not an ABM code change.
- **The active-rate gotcha discrepancy** between manuscript-reported and reclassified regime counts is material and must be surfaced in revised §8.

Below: the seven instruction-required findings plus four additional findings from this rescoring.

---

## §1 — Coverage

**15 of 16 cases scored. 1 case declined (LR007).** No case required scope-narrowing beyond what was foreseeable from Nitrogen's case definitions. Two cases were scored at periods narrower than Nitrogen's nominal scope (LR006 narrowed from "Atlantic 16th–19th c." to "U.S. antebellum 1820–1865" because the deep-dive evidence is entirely U.S. antebellum; LR009 narrowed to medieval Roman Inquisition 1231–1542 per Q2 to avoid double-counting). Both narrowings are documented in `scoring_decisions`.

**The declined case (LR007 Missionary-colonial conversion regimes) is itself a finding.** Nitrogen's scope ("16th–20th centuries, Americas Africa Asia") is methodologically too broad — four centuries × three continents × dozens of denominations × hundreds of mission stations. The methodology rule "unit is regime not tradition" precludes scoring such a class as a single regime.

The decline is not a failure of the synthesis architecture. It is a confirmation that the synthesis architecture's diagnostic capacity works: the case's heterogeneity outruns the ABM's scalar exit_cost, which is exactly what `SYNTHESIS_WORKING_DOC.md §5 Extension 4` (exit-cost mechanism decomposition) is designed to fix. Different missions have different exit-cost mechanisms — Jesuit reductions had high geographic_isolation and language_non_portability, Protestant CMS in India had weak exit cost across mechanisms, African mission stations had high state-backed legal_compulsion. The ABM's scalar parameter cannot represent this; Extension 4 specifically can.

**Coverage map by region/period:**

| Period (approx.) | Cases | Note |
|---|---|---|
| 1095–1300 (high medieval) | LR001, LR002, LR009, LR010 (start) | Crusading + early Inquisition + medieval anti-Jewish persecution |
| 1300–1700 (late medieval, early modern) | LR003, LR004, LR008, LR009 (end), LR010 (end) | Inquisitions + witch trials |
| 15th–17th c. (Atlantic colonial) | LR005, LR007 (declined) | Doctrine of Discovery; mission regime declined as too broad |
| 18th–19th c. (Atlantic abolition + slavery) | LR006, LR011, LR012 | Pro-slavery vs. abolitionist on overlapping canon |
| 19th–20th c. (settler-colonial assimilation) | LR015, LR016 | Residential / boarding schools |
| 20th c. (post-Vatican II + liberation) | LR013, LR014 | Restraint and softening |

The case bank is heavily Western-Christian and disproportionately oriented toward Atlantic colonial / abolition-era cases. Eastern Christian heresy adjudication, Russian Orthodox state-church regimes, and Eastern Catholic Uniate regimes are absent. Christian-only scope was deliberate per Nitrogen methodology; the under-coverage of non-Western Christianity is a Nitrogen bank limitation, not a Phase S1 limitation.

---

## §2 — Aggregate regime distribution

**Predicted regime distribution (15 scored cases + 1 declined):**

| Regime | Count | Cases |
|---|---|---|
| QUIET | 3 | LR011, LR012, LR013 |
| MIXED | 8 | LR001, LR002, LR005, LR006, LR008, LR009, LR010, LR014 |
| COLLAPSE | 0 | none |
| CAPTURE | 4 | LR003, LR004, LR015, LR016 |
| (DECLINED) | 1 | LR007 |
| **Total** | **16** | |

**Match-rate decomposition (per Q5 schema):**

| match_type | Count | What it tells us |
|---|---|---|
| substantive | 9 | The framework's prediction is genuinely tested and confirmed. |
| boring_null | 3 | The framework correctly identifies low-everything as quiet — sanity check, not validation. |
| formal_only_mechanism_mismatch | 3 | The formal score matches but the mechanism the rubric describes does not apply. Diagnostic finding, not validation. |
| (declined) | 1 | LR007 |
| **Total scored** | **15** | |

**Three rates worth reporting separately, not combined:**

- **Substantive match rate: 9/12 = 75%** of informative cases (excluding boring-null and declined). This is the rate at which the framework's interesting empirical claim — that code geometry determines regime type — is genuinely tested and confirmed.
- **Boring-null match rate: 3/15 = 20%**. The framework correctly identifies low-σ × low-π regimes as QUIET. Should not be combined with substantive matches when reporting "the framework predicts correctly."
- **Formal-only-mechanism-mismatch rate: 3/15 = 20%**. Cases where the formal score matches but the case's actual mechanism is outside the ABM's modeling scope. These are not framework failures — they are scope flags for Phase S2.

The raw 15/15 (= 100%) match rate, if reported alone, would dramatically overstate the framework's empirical performance. The decomposed rates are the honest summary.

**What the distribution suggests about rubric calibration:**

- The absence of COLLAPSE-predicted cases reflects a real feature of the Christian case bank (Christian regimes that depopulated under tightening enforcement are rare in this corpus) plus a known rubric limitation: the COLLAPSE label is enforcement-induced depopulation specifically, not slow attrition under loose enforcement. LR014 (modern softening with high attrition) was scored MIXED rather than COLLAPSE per Q4; in a stricter rubric reading, mainline Protestant decline might be a non-canonical sub-regime of MIXED that should be teased apart in Phase S5.

- The MIXED region is the modal predicted regime (8/15 = 53%). This is consistent with the manuscript's reclassified empirical distribution (54 of 72 v2.5 cells classify as MIXED per `reclassified_summary.csv` — see §8 below) and consistent with the framework's claim that capture is reachable but rare. A case bank weighted toward extremes would tilt toward CAPTURE; the corpus's tilt toward MIXED suggests Nitrogen sampled cases that are interesting *because* their geometry is not in the corner.

- The CAPTURE region (4/15 = 27%) includes two inquisition cases (LR003, LR004) and two captive-population cases (LR015, LR016). The first pair are genuine substantive CAPTURE matches (the framework's claim is validated). The second pair are formal-only-mechanism-mismatches: the framework predicts CAPTURE because the score profile matches CCP/Stalinist anchors, but the case's mechanism is custody-of-minors, not voluntary-membership-with-blocked-exit. The CAPTURE region's substantive validation rests on 2 of 4 cases.

---

## §3 — Q1 from the synthesis doc: argument-template envelope calibration (theoretical or empirical?)

**Recommendation: theoretical derivation (Path 1) is feasible. Empirical calibration from these 16 cases (Path 2) would overfit.**

The synthesis working doc's Q1 asks whether the T1–T8 → (σ_max, π_max, base_opp_floor, exit_cost_baseline) envelope mapping requires empirical calibration from the 16 cases or can be derived from the templates' structural variables (C, A, M, E, O, U, R, P) alone. Phase S1 evidence supports the theoretical-derivation path because:

**Argument-template usage in the corpus is highly skewed.** Template counts across cases:

| Template | Cases active | Cases as primary |
|---|---|---|
| T3_expansion_mandate | LR001, LR005, LR007, LR015, LR016 | 4 (excluding LR007) |
| T5_sacred_enforcement | LR001, LR002, LR006, LR008, LR009, LR015, LR016 | 7 |
| T4_purification | LR002, LR003, LR004, LR008, LR009, LR010 | 6 |
| T1_exclusive_salvation | LR010 | 1 |
| T7_counter_reading | LR011, LR012, LR013, LR014 | 4 |
| T6_softened_modern_interpretation | LR014 | 1 |
| T8_asymmetric_modern_rights_borrowing | LR006 | 1 (mixed with T5) |
| T2_final_sorting | (none) | 0 |

Templates T1, T2, T6, T8 each appear in fewer than 2 cases. Empirical calibration of envelope parameters for these templates would rest on 0–1 evidence point each — overfit risk is severe. T2 (final sorting) appears in 0 cases despite the canonical Matthew 25 / Revelation 20 framing being prominent in Christian theology — this corpus simply does not include cases where T2 is the central template. Empirical envelope for T2 is not derivable from this case bank.

**Theoretical derivation from structural variables is well-defined.** The argument templates already encode their structural variables in `argument_templates.json`:

- T1 (C, A, O, U): exclusive salvation enables σ via C-classification, raises exit_cost via O-outsider framing.
- T2 (C, A, U, O): final sorting heightens urgency, raising π temporarily.
- T3 (M, U, A): expansion mandate raises π × delegation through M-mandate.
- T4 (C, M, E, O, R): purification activates enforcement directly via E.
- T5 (M, E, R, A): sacred enforcement raises π via E and resistance-handling via R-resistance.
- T6 (P against C, A, M, E, O, R): pluralistic restraint caps σ_max and π_max.
- T7 (P): counter-reading caps π low.
- T8 (A, C, O with modern restraint overlay): asymmetric exclusion with limited enforcement.

Each structural variable maps to its ABM-parameter consequence in a way that does not require empirical calibration from this case bank. The empirical calibration can serve as a *secondary check* — does the corpus's MIXED/CAPTURE outcomes for cases activating T3+T5 (LR001, LR015, LR016) cluster in the high-σ-high-π envelope? Yes (LR015 4,4,4,4,4; LR016 4,4,4,3,4; LR001 3,3,3,3,2). But this is consistency check, not primary calibration.

**Phase S2 implication:** proceed with theoretical derivation. The 16 cases provide consistency checks but not primary calibration data. This means Phase S2 is independent of Phase S1 in the strong sense — Phase S2 can begin with templates derived from `argument_templates.json` alone. Save 1–2 weeks relative to the empirical calibration path.

---

## §4 — Q2 from the synthesis doc: text_role_assessment as input or output?

**Recommendation: keep `text_role_assessment` as a *coding field at scoring time* — neither pure input nor pure output of the ABM, but an annotation that travels alongside the case data and can be queried for synthesis claims about textual causality.**

The synthesis working doc Q2 asks whether `text_role_assessment` (driver / legitimizer / coordinator / decoration / authorizing / legal_basis / motivating / etc.) should be a first-class ABM concept. Phase S1 evidence:

**The field correlates meaningfully with regime classification.** Distribution:

| text_role_assessment | Cases | Predicted regime |
|---|---|---|
| authorizing | LR001, LR002, LR009, LR015, LR016 | mixed, mixed, mixed, capture, capture |
| legal_basis | LR003, LR004, LR005, LR008 | capture, capture, mixed, mixed |
| legitimating | LR006, LR014 | mixed, mixed |
| identity_boundary_marker | LR010 | mixed |
| coordinating | LR011, LR012, LR013 | quiet, quiet, quiet |
| motivating | LR007 (declined) | — |

`coordinating` perfectly correlates with QUIET (3 of 3 restraint cases). `authorizing` and `legal_basis` cluster around MIXED→CAPTURE, with the difference between them tracking centralization and procedural infrastructure (legal_basis cases have C=4 in 3 of 4; authorizing has more variance).

`legitimating` is the diagnostic-of-mechanism case: when text legitimates rather than authorizes, the regime's enforcement infrastructure is weaker because the heavy lifting is done by non-textual forces (LR006 has class_control=4, resource_capture=4; LR014 has all non_textual_forces at 0 because the regime has minimal external coupling at all).

**The field correlates with mechanism-mismatch.** Of the 3 formal_only_mechanism_mismatch cases, all three have `text_role_assessment ∈ {authorizing, legal_basis}` — consistent with the projection-onto-target-population pattern: when text authorizes/legalizes, the operation it authorizes is often outward-facing rather than internal-membership-discipline.

**But the field is not derivable from ABM dynamics alone.** It is a *historical-interpretive judgment* about what the text was doing in a given regime, not a measurable output of simulation. Making it a first-class output (a diagnostic of dynamics) would require running the regime through the ABM and inferring text-role from outcome patterns — which is not what historians actually do when they assess text role. Making it a first-class input (a parameter the modeler sets) would conflate two questions: "what kind of code is this?" (Layer A in the synthesis architecture) vs. "how does the code function in this regime?" (case-level annotation).

**Phase S2 disposition:** keep `text_role_assessment` as a Layer C coding annotation that travels with the case. It can be used in synthesis claims (e.g., "regimes where text_role_assessment is `coordinating` empirically score QUIET in this case bank") but should not be built into the ABM as a parameter or output. This matches what `SYNTHESIS_WORKING_DOC.md §10 decision point 2` envisioned.

---

## §5 — Q4 from the synthesis doc: how should restraint cases be handled?

**Recommendation: option (b) — include as "regimes with low σ × π that did not produce enforcement equilibria" — for revised Paper 2. Option (c) — include with explicit caveat about rival mobilization aspect — once Extension 2 is built. Phase S1 confirms (b) is workable.**

The synthesis working doc Q4 asks whether the four restraint cases (LR011 abolition, LR012 Quaker, LR013 liberation theology, LR014 modern softening) should be:
- (a) excluded from the validation set,
- (b) included as low-σ × low-π regimes that did not produce enforcement,
- (c) included with explicit caveat about the rival-mobilization aspect.

Phase S1 evidence:

**Option (b) works for the rubric, with the boring-null caveat.** All four restraint cases score in the rubric and their predictions match observations. LR011, LR012, LR013 score sub-activation across all dimensions (1,0,1,1,0; 1,0,0,0,0; 1,1,1,1,1) and predict QUIET — observed QUIET. LR014 was scored MIXED per Q4 (with the COLLAPSE-narrow-definition flag). The rubric is *applicable*; the issue is that the matches are not framework validations.

**The boring_null match_type field captures this.** Per Q5 disposition, all three of LR011/LR012/LR013 are `match_type=boring_null`. The framework correctly identifies low-everything as quiet, but this is sanity-check territory, not the framework's interesting claim.

**Option (c) is the honest framing once Extension 2 exists.** The cases' substantive content — rival mobilization on overlapping canon — is invisible to the current ABM. LR011/LR012 share canon with LR006 pro-slavery argument; LR013/LR014 share canon with traditionalist Catholic regimes. The rivalry is the case's content; the rubric only sees the absence of internal enforcement.

**Recommendation for revised Paper 2 §9:** include LR011–LR014 as a four-case sub-section labeled "Restraint regimes" with explicit framing that (a) the prediction (low σ × π → quiet) is correctly produced, (b) the case's substantive content (rival mobilization) is outside current ABM scope, (c) Extension 2 is named as future work. This corresponds to Q4 option (b) for the current revision, transitioning to option (c) post-Extension-2.

---

## §6 — Findings that constrain ABM extensions

For each of the four extensions named in `SYNTHESIS_WORKING_DOC.md §5`, what does Phase S1 say?

### Extension 1 — Argument-template input vector

**Validated as designed.** Phase S1 §3 above confirms that templates have a meaningful relationship to predicted regime, and that theoretical derivation from structural variables is feasible without empirical calibration from this case bank. T2 has zero cases (no calibration possible regardless), and T1, T6, T8 each have ≤1 case. Theoretical derivation is the path.

### Extension 2 — Rival-regime competition

**Validated as necessary; designed correctly.** Four cases (LR011, LR012, LR013, LR014) cannot be substantively evaluated without it. LR006 also has rival-regime present (LR011 is its rival on overlapping canon). 5 of 15 scored cases (33%) are explicitly competing-regime cases; the synthesis architecture cannot indefinitely defer Extension 2. Recommendation: keep as deferred for revised Paper 2 (Extension 2 marked as future work) but begin design for Paper 3 (caste — colonial-Brahminical regime vs. pre-colonial dharmaśāstra is structurally Extension 2).

### Extension 3 — Non-textual force decomposition

**Validated as designed; modest priority.** All 15 scored cases have non-zero `non_textual_forces` scores, with the heaviest forces being state_power (10 cases ≥3), political_legitimacy (10 cases ≥2), and class_control (5 cases ≥3). Empire and resource_capture cluster on the colonial cases (LR004, LR005, LR015, LR016). Patriarchy is dispositive for LR008 (witch trials) and largely absent elsewhere. The four-force vector specified in `SYNTHESIS_WORKING_DOC.md §5 Extension 3` (empire_pressure, resource_capture_pressure, class_control_pressure, ethnic_conflict_pressure) is a defensible subset, but the case-level evidence supports also including state_power and political_legitimacy. Recommendation: expand Extension 3's force vector to six forces; the additional two are easy to add and align with what the case scoring supports.

### Extension 4 — Exit-cost mechanism decomposition

**Validated as necessary.** LR007 declined explicitly because of exit-cost-mechanism heterogeneity. LR004 (Portuguese Inquisition) needs decomposition for the Goa-vs-metropolitan distinction. LR015 and LR016 use child_custody (4) + language_non_portability (4) + geographic_isolation (3-4) — a specific mechanism profile that the scalar exit_cost cannot represent. The six-mechanism decomposition specified in the working doc is well-supported by Phase S1 evidence; recommend proceeding as designed.

### Extension 5 — Target-population modeling (NEW, unspecified)

**Validated as needed.** Three cases (LR005, LR015, LR016) have `match_type=formal_only_mechanism_mismatch` because the ABM models voluntary-membership-with-exit but the cases involve enforcement projected onto non-member or captive populations. This is also the structural problem at the heart of Paper 3 (caste — colonial-Brahminical regime projecting on lower jātis).

**Phase S1 does not design Extension 5.** Per Q3 disposition: just flag the need. Recommendation: in `SYNTHESIS_WORKING_DOC.md` revision, add Extension 5 as a fifth named extension. Design work for Extension 5 is a separate Phase S2.5 (unscheduled in current planning) or a Phase S3 task. Without it, three of fifteen scored cases cannot be substantively evaluated and Paper 3 cannot proceed.

---

## §7 — Recommendations for Phase S2

1. **Begin Phase S2 immediately.** The synthesis architecture is not refuted; the boundary conditions are now known. Phase S2 is independent of Phase S1 in the empirical-calibration sense (Q1 finding) — proceed with theoretical derivation of envelope parameters from `argument_templates.json` structural variables.

2. **Revise `SYNTHESIS_WORKING_DOC.md §5` to include Extension 5** before Phase S3 begins. Extension 5 design work is a prerequisite for Paper 3 (caste) and for substantive evaluation of LR005/LR015/LR016 in Phase S4.

3. **Expand Extension 3's force vector to six forces** (empire_pressure, resource_capture_pressure, class_control_pressure, ethnic_conflict_pressure, state_power_pressure, political_legitimacy_pressure). Phase S1 evidence supports state_power and political_legitimacy as central forces in 10+ of 15 scored cases; excluding them from the model would lose information.

4. **Active-rate gotcha must be solved at sweep time, not after.** The new argument-template envelope sweep must compute `active_punish_rate` directly during simulation, not rely on `reclassify_regimes.py` post-hoc. This is per `INSTRUCTION_BORON_S2.md`'s "Active-rate rule for new sweeps" section. Phase S5 will retrofit the manuscript figures from the existing reclassified data; new sweeps must not perpetuate the issue.

5. **Phase S4 (16-case replication sweep) should include moderate-uncertainty cases.** The current corpus is biased toward enforcement-dominant + restraint extremes. Adding 4–6 moderate-σ × moderate-π cases (e.g., 19th-c. Lutheran state churches in Scandinavia, 20th-c. Mormon US, 19th-c. Russian Orthodox state-church) would stress-test the framework against ambiguity. Christian-only scope can be preserved.

---

## §8 — Active-rate discrepancy finding (Phase S5 figure-rebuild input)

This is the instruction-required §8 finding from `INSTRUCTION_BORON_S1.md`'s "Active-rate gotcha" guidance. It is technical but consequential.

**The problem:** the manuscript-reported empirical regime distribution (uncorrected `punish_rate`) differs materially from the corrected distribution computed by `scripts/reclassify_regimes.py`. Per CLAUDE.md and the Phase S1 instruction:

| Regime | Manuscript-reported (uncorrected) | Reclassified (active_punish_rate) | Δ |
|---|---|---|---|
| QUIET | 26 | 8 | −18 |
| MIXED | 36 | 54 | +18 |
| COLLAPSE | 9 | 9 | 0 |
| CAPTURE | 1 | 1 | 0 |
| **Total** | 72 | 72 | — |

(The manuscript-reported counts are stated in `INSTRUCTION_BORON_S1.md` and are what appears in the PLOS submission `manuscript_PLOSONE.tex` §8. The reclassified counts should be verified at Phase S5 by counting `cell_reclassified_hier=True` rows in `results/v2.5_corrected_three_regime_confirm/reclassified_summary.csv`. Per Phase S1 Hard Rule 1 I have not modified or recomputed those files; the verification is a Phase S5 task.)

**18 of 72 cells flip from QUIET to MIXED under corrected classification.** The discrepancy is mathematically explained by the gotcha: raw `punish_rate = punished / N_total` includes exited agents (who always have `punished=0`); with exit rates of 0.6–0.7 in mixed cells, the raw rate dilutes intensity by 60–70%. `active_punish_rate = punish_rate / (1 − exit_rate)` recovers the correct intensity. The 18 cells that flip are cells where intensity *was* above the 0.10 MIXED threshold but the dilution put the raw rate below threshold.

**For Phase S1 specifically:** when comparing the ABM's predicted regime distribution for the 16 Christian cases against the manuscript's empirical distribution, **use the corrected counts (8 quiet / 54 mixed / 9 collapse / 1 capture)** as the truth. The ABM's predicted distribution from this rescoring (3 quiet / 8 mixed / 0 collapse / 4 capture, ignoring 1 declined) is qualitatively consistent with the corrected counts in two ways: (a) MIXED is the modal regime in both, (b) the QUIET fraction is small. The CAPTURE fraction is higher in this case bank (4/15 = 27%) than in the manuscript's reclassified empirical distribution (1/72 = 1.4%) because the case bank deliberately selected CAPTURE-evidenced cases (residential schools, inquisitions) rather than sampling the parameter space uniformly. This is a sampling effect, not a framework issue.

**Phase S5 figure-rebuild plan (per Q3 + Q6 + S5 instruction):** §8.1, Table 5, Figure 1 phase map, Figure 2 regime counts, and per-regime concentration metrics (Figure 3) must be regenerated from `reclassified_seed_results.csv` and placed in a new whitelisted result directory (suggested name: `results/v2.5_corrected_three_regime_confirm_active_rate/`). The original `results/v2.5_corrected_three_regime_confirm/` directory must not be overwritten — per CLAUDE.md it is a frozen reproducibility artifact.

The PLOS submission package's compiled `manuscript_PLOSONE.pdf` is built from the uncorrected counts. A revised manuscript using corrected counts would change three numerical claims in §8 prose (regime counts) and several figure panels. This is a non-cosmetic revision and must be flagged for the editor when resubmitting.

---

## §9 — Findings beyond the seven instruction-required questions

### §9.1 — The COLLAPSE-narrow-definition issue (Phase S5 manuscript-revision item, per Q4)

The ABM's COLLAPSE label in §6.10 requires `exit_rate ≥ 0.90` — enforcement-induced depopulation. This excludes a real and empirically common regime type: slow attrition under loose enforcement (mainline Protestant decline, late-modern Catholicism, the "nones" demographic transition).

LR014 forced this finding. Scored predicted=MIXED, observed=MIXED-with-high-attrition per Q4 — but the attrition is not enforcement-induced and is not formally captured by the rubric. Either the COLLAPSE definition should be broadened to include non-enforcement-induced attrition, or a fifth regime category should be added, or the existing labels should be clarified.

**Recommendation for Phase S5 revised Paper 2 §9 Discussion:** add a paragraph clarifying that COLLAPSE in the ABM denotes specifically enforcement-induced depopulation, and that the rubric does not formally distinguish slow attrition under loose enforcement (which is observationally distinct but currently flattened to MIXED or QUIET). The framework's substantive claim — that code geometry produces the four labeled regime *types* — is preserved; the manuscript clarification is about what the labels denote, not what the ABM produces.

### §9.2 — The regime-vs-event axis is under-theorized

Two cases (LR001 First Crusade 1095–1099, LR002 Albigensian Crusade 1209–1229) are mobilization episodes shorter than the ABM's 500-step steady-state assumption suggests. The scoring proposed treating them as the *underlying papal authorization apparatus during the crusade window*, which is a reframe. The S1 Text Table 5 illustrative cases are all centuries-long (Counter-Reformation Inquisition, Saudi CPVPV era, Scientology Sea Org).

This is a coding-level finding rather than a code change. Phase S5 manuscript revision could add a brief note in §5 (Scoring Rubric) clarifying that the regime unit must be *long enough* for steady-state enforcement to be a defined notion. Episodes shorter than ~50 simulation timesteps' equivalent (~5 years of real time, very roughly) should either be reframed to the underlying enduring apparatus or scored with explicit confidence flags.

### §9.3 — Confirmation-bias audit findings

The dry-run flagged confirmation-bias risk specifically for matches at the rubric extremes. The audit (documented per case in `scoring_decisions`) found:

- **No tilting up from MIXED to CAPTURE** in cases where the institutional consolidation argument was weak (LR009 medieval Roman Inquisition held to MIXED; LR002 Albigensian held to MIXED despite local Cathar elimination).
- **Tilt-up to CAPTURE held only where institutional anchors warrant it** (LR003, LR004 inquisitions match Counter-Reformation Inquisition Table 5 anchor; LR015, LR016 match CCP/Stalinist 4-on-4 anchor).
- **C=3 vs. C=4 distinction held meaningfully** (LR016 C=3 because U.S. BIA was less monolithic than Canadian Indian Affairs; LR015 C=4 because Canada's federal-religious unification was tighter). This was a real factual call, not a tilt to differentiate.
- **One case (LR014) has a documented Q4-override** where strict rubric reading would predict QUIET but Q4 directs MIXED. Documented in `scoring_decisions` so the override is visible.
- **No rubric-extremity case was tilted to manufacture a match.** The matches at the extremes are products of the case profiles, not of the scoring choices.

The 15/15 raw match rate is high but defensible after decomposition; the substantive 9/12 rate is the honest framework-validation number.

### §9.4 — The case bank's selection bias

Nitrogen selected cases that are either well-documented enforcement-dominant regimes (LR001–LR010, LR015–LR016) or well-documented restraint counter-readings (LR011–LR014). Genuine moderate-uncertainty cases (regimes whose σ × π × E sits in the contested middle of the parameter space) are absent. This gives the framework an easy time: extremes plus their inverses are always easier to classify than moderates.

A future Phase S4 should include 4–6 moderate cases. Christian-only scope can be preserved (e.g., 19th-c. Lutheran state churches Scandinavia, 18th-c. Anglican Establishment England, 19th-c. Russian Orthodox state-church under Pobedonostsev, 20th-c. Mormon US under Smith family transition, 19th-c. Methodist circuit-rider system US frontier). The current 16-case bank does not stress-test the framework against ambiguity; adding moderates would.

---

## §10 — Items the synthesis architecture should now know

Concise list of items that should be reflected upstream in `SYNTHESIS_WORKING_DOC.md` and the two `INSTRUCTION_BORON_*.md` files:

1. **Add Extension 5 (target-population modeling)** to `SYNTHESIS_WORKING_DOC.md §5`. Three of fifteen scored cases require it; Paper 3 absolutely requires it.
2. **Note that Q1 is resolved in favor of theoretical derivation** for Phase S2 envelope mapping — empirical calibration from this case bank is not feasible due to template-usage skew.
3. **Note that Q4 is resolved as option (b) for revised Paper 2** with a transition to option (c) once Extension 2 is built.
4. **Add LR014's COLLAPSE-narrow-definition issue** as a Phase S5 manuscript-revision item in §14 (or a new §14.4).
5. **Add the regime-vs-event-axis issue** as a Phase S5 §5 (Scoring Rubric) clarification item.
6. **Active-rate gotcha §8 update** is unchanged from current synthesis doc §14.1 — Phase S1 confirms the 18-cell flip count (pending Phase S5 verification against `reclassified_summary.csv`).

---

## Definition of done — summary for Kiran

- 15 of 16 cases scored; 1 declined (LR007) per Q1.
- Six deliverables produced (this file + 4 others + build script).
- Substantive match rate: 9/12 = 75% (excluding 3 boring-null and 1 declined).
- Boring-null match rate: 3/15 = 20%.
- Formal-only-mechanism-mismatch rate: 3/15 = 20%.
- Confidence distribution: scoring confidence is `medium` or `high` for ~55 of the 75 dimension-cells (5 dims × 15 cases); `low` for ~12 cells, mostly in LR005 (target-population case) and LR010 (anti-Jewish boundary apparatus).
- Open questions count across cases: 18 (range 1–3 per case).
- New finding requiring Phase S2 architecture revision: **Extension 5 (target-population modeling)**.
- New findings requiring Phase S5 manuscript revision: **COLLAPSE-narrow-definition; regime-vs-event-axis; active-rate-gotcha figure rebuild**.

**Recommendation for Phase S2: PROCEED.** With theoretical envelope derivation per Q1 finding. With Extension 5 added to the synthesis plan before Phase S3 begins.

---

*End of synthesis findings. Update upon Phase S2 completion.*
