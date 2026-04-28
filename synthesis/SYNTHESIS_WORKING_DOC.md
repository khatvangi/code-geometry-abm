# Synthesis Working Document

**Project:** Code-Geometry ABM (Boron) ↔ Christianity Application (Nitrogen)
**Status:** Internal alignment doc. Not for publication. Phase S1 complete (2026-04-27); folded findings below. Phase S2 in planning.
**Date:** 2026-04-27
**Author/owner:** Kiran Boggavarapu

---

## 1. Purpose

The two repositories — `code-geometry-abm` (Boron, the methodology) and `violence-abrahamic` (Nitrogen, the Christianity application) — were developed in parallel and use different vocabularies. Each contains methodological elements the other lacks. The ABM is unpublished; therefore the right move is not unilateral translation but synthesis: extend the ABM in light of what the Nitrogen work uncovered, and rescore the Christian cases in the resulting unified vocabulary.

This document specifies what the synthesis requires, in what order, and what each step costs. It is a planning artifact, not a paper.

## 2. The mismatch, stated precisely

The ABM models a regime as a parameter set — `(σ, π, κ, λ, q, A, base_opp, δ, η, block_exponent)` — and asks which equilibrium the parameter values produce. It treats the *content* of the code as exogenous and irrelevant: §7 ("Scope and Limitations") explicitly says two systems with identical code geometry but different theological content should produce similar enforcement dynamics.

Nitrogen scores 16 Christian regimes on six variables — `(T, L, I, C, MCI, R)` — plus several categorical fields (`text_role_assessment`, `non_textual_forces`, `argument_template`). It treats text content as central and asks how the text functions in the regime: does it drive, legitimize, coordinate, or merely decorate?

These are not the same question. The ABM asks "what regime does this institution produce?" Nitrogen asks "what role does this text play in this regime?" Both are valid. Neither is reducible to the other.

The synthesis must hold both questions open simultaneously without collapsing either into the other.

## 3. What each side has that the other lacks

### What the ABM has and Nitrogen lacks

| ABM element | Why it matters |
|---|---|
| Falsifiable regime classification (quiet / mixed / collapse / capture) | Replaces Nitrogen's unjustified additive composite with a behavioral typology. |
| Continuous structural parameters (σ, π, exit cost, capital compounding) | Connects intuitive case features to a closed dynamical system whose equilibria are derivable rather than asserted. |
| Endogenous δ-drift mechanism | Models the feedback by which an enforcement apparatus degrades the perceived outside option (epistemic violence, narrative darkening) without postulating external propaganda. |
| Null results for α (sanctified suffering) and µ (membership reward) | Distinguishes inward-facing retention from outward-facing closure. Disciplines the analysis against folk-sociological "they retain because community is warm" stories. |
| Five-link causal chain (geometry → delegation → drift → exit collapse → capture) | Tells you *how* a regime moves between equilibria, not just where it sits. |
| Scoring rubric with ordinal anchors (S1) | Reproducible by independent raters; tracks Cohen's κ. |

### What Nitrogen has and the ABM lacks

| Nitrogen element | Why it matters |
|---|---|
| `text_role_assessment` | Forces every case to code text as driver / legitimizer / coordinator / decoration / authorizing / legal_basis. The ABM has no slot for this and §9 cannot resolve "is text causal?" without it. |
| `non_textual_forces` (empire, land, slavery, class_control, patriarchy, trade, resource_capture, ethnic_conflict, …) | Tracks confounders explicitly. The ABM §7 acknowledges exogenous shocks exist but does not model them. |
| `argument_template` (T1–T8) | Abstracts canonical text content into eight functional types: exclusive_salvation, final_sorting, expansion_mandate, purification, sacred_enforcement, softened_modern_interpretation, counter_reading, asymmetric_modern_rights_borrowing. Reusable as a code-content classifier. |
| MCI (missionary control integration) as a specific exit-cost mechanism | The ABM's exit cost is a single scalar. MCI specifies the *mechanism* by which exit cost is raised when the cadre controls childhood, education, language, kinship — not by legal apostasy penalty alone. |
| Counter-reading R as a rival regime within the same tradition | The ABM models one regime per simulation. Restraint counterreadings (abolitionism, Quaker practice, liberation theology, modern softening) operate as competing regimes drawing on the same canon — a phenomenon the ABM cannot currently represent. |
| Evidence hierarchy (Levels 1–5) and locked rule chain | Methodological discipline absent from the ABM, which currently lets §9 wave at "directional consistency" with thin observational data. |
| Documented historical cases with source trails | The ABM has an illustrative 10-row table. Nitrogen has 16 cases with attached evidence (48 source rows, 2 documented at deep-dive level). |

### What both have but in incompatible form

| Concept | ABM form | Nitrogen form | Reconciliation |
|---|---|---|---|
| Code structural strength | σ (legibility-substitutability, continuous 0–1) | T (textual affordance, ordinal 0–3) | T scores the *content type's* affordance for σ, π, exit cost. T should map onto multiple ABM parameters, not just σ. |
| Enforcement viability | π (continuous reward) + delegation | I (incentive amplification, 0–3) + L (lived uptake, 0–3) | I ≈ π level. L ≈ binary "did σ × π cross activation threshold for this regime?" |
| Institutional thickness | enforcement affordance + centralization + capital compounding | C (control-axis integration, 0–3) | C is a composite over three ABM dimensions. Decompose. |
| Restraint | absent | R (counter-reading strength, 0–3) | ABM extension required: rival-regime modeling. |

## 4. Synthesis architecture

The synthesis is a **two-layer model** with explicit interfaces between them.

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER A — Code-content classifier (Nitrogen-derived)       │
│                                                             │
│  Inputs:  canonical texts + commentary tradition            │
│  Outputs: argument_template_distribution (T1–T8 weights)    │
│           text_role_assessment                              │
│           counter_reading_strength (R)                      │
│                                                             │
│  This layer tells you *what kind of code* is being run.     │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER B — Regime dynamics (ABM)                            │
│                                                             │
│  Inputs:  σ, π, q, A, base_opp, δ, η, exit_threshold,       │
│           AND outputs from Layer A                          │
│                                                             │
│  Outputs: regime classification (quiet/mixed/collapse/      │
│           capture), enforcement concentration metrics,      │
│           exit trajectory, δ trajectory                     │
│                                                             │
│  Plus: non_textual_forces as exogenous parameter            │
│        perturbations (Tilly-style state pressure, etc.)     │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER C — Empirical case bank (16 Christian regimes)       │
│                                                             │
│  For each regime: scored on ABM parameters AND coded        │
│  on Layer A outputs. Source trail per claim.                │
│                                                             │
│  This is the validation/test set, not a separate framework. │
└─────────────────────────────────────────────────────────────┘
```

The key change: Layer A becomes an **input** to Layer B, not a parallel framework. The argument templates (T1–T8) are abstractions over code content that determine *which σ and π regions are even reachable* by a given tradition, before institutional dynamics are run.

This solves the original mismatch: the ABM said "code content doesn't matter, only geometry does" — a strong claim that was always vulnerable. The synthesis says: code content shapes which geometries are *available* to a regime; once a geometry is selected (by institutional choice + non-textual forces), the ABM dynamics determine the equilibrium. Code content is therefore upstream of geometry, not parallel to it.

## 5. Required ABM extensions (Boron work)

These are model changes, not parameter sweeps. Each requires new code in `src/`, new tests, and re-running the relevant sweeps.

### Extension 1 — Argument-template input vector

**Status quo:** `σ` and `π` are set directly by the modeler.

**Extension:** Accept an `argument_template_distribution` over T1–T8. Each template has a calibrated mapping to (σ_max, π_max, base_opp_floor, exit_cost_baseline) describing the *envelope* of geometries that template makes structurally available. The modeler then sets concrete values within that envelope to represent a specific historical regime.

Example: T1 (exclusive_salvation) makes high-σ, high-π reachable; T7 (counter_reading) caps π low and raises P_pluralistic_restraint. T6 (softened_modern_interpretation) caps σ low even in a tradition whose canon contains T1 material.

This is the cleanest answer to question 3 (whether `text_role_assessment` should be first-class). The argument template is first-class; `text_role_assessment` becomes a diagnostic *output* after a run, telling us which of {driver, legitimizer, coordinator, decoration} the text actually was, given the dynamics that ensued.

**Cost:** ~200 lines of code, calibration table, two new sweeps.

### Extension 2 — Rival-regime competition (counter-reading R)

**Status quo:** One regime per simulation.

**Extension:** Two coupled regimes drawing on overlapping canon. Agents can be members of regime A or regime B; defection between them is a third option besides exit-to-secular. The R variable in Nitrogen becomes the σ_B × π_B viability of the counter-regime. Empirical case: abolitionism vs. pro-slavery Christianity using overlapping canon.

This is non-trivial. It is the single largest extension in the synthesis. It may merit its own paper.

**Cost:** ~600 lines, new sweep architecture, possibly v3.0 of the ABM.
**Decision required:** Whether to include in revised Paper 2 or defer to a separate paper. My recommendation: defer. Note the limitation in revised Paper 2 §7 and add Extension 2 as future work.

### Extension 3 — Non-textual force decomposition

**Status quo:** ABM treats σ, π as the regime's full structural specification.

**Extension:** Add explicit exogenous force vector: `(empire_pressure, resource_capture_pressure, class_control_pressure, ethnic_conflict_pressure)` that perturbs π and exit_cost over time. This makes the ABM able to represent the *coupling* of code to power that the Nitrogen lived-religion variables track.

Concretely: a Christian missionary regime in colonial Canada is not a free-standing code-geometry instance. It is `(Christian missionary code) × (settler colonial state apparatus) × (residential school custody mechanism)`. The ABM should model these as three separable inputs whose interaction determines the regime's trajectory.

**Cost:** ~150 lines, one new sweep dimension.

### Extension 4 — MCI as exit-cost mechanism specification

**Status quo:** Exit cost is a scalar.

**Extension:** Decompose exit cost into mechanisms: (legal apostasy penalty, kinship endogamy, economic dependence, language non-portability, child custody, geographic isolation). MCI = 3 corresponds to high values on the last three mechanisms specifically. This decomposition matters because Paper 3 (caste) needs to distinguish between exit costs operating through caste endogamy versus exit costs operating through colonial mission custody — these are different mechanisms even if the scalar exit cost is identical.

**Cost:** ~100 lines, optional sweep over decomposition.

### Extension 5 — Target-population modeling (NEW, surfaced by Phase S1)

**Status quo:** The ABM models a single voluntary-membership population subject to internal enforcement. Exit_cost is the only mechanism preventing departure under enforcement pressure; all agents are members; sanction targets the deviant member.

**Extension:** Add a target population that the regime acts on but whose members are not regime members. The regime's σ × π applies to the target via classification-and-sanction, but the target's exit options, exit costs, and counterfactual life-paths differ structurally from members'. Concretely: target_member agents have no membership benefits, no internal belief-update toward the regime's y0, and their "exit cost" is the cost of escaping enforcement custody rather than the cost of leaving voluntary membership. The regime's enforcement capital still accumulates from punishing them, but the agents themselves are not selecting compliance to gain in-group benefit.

**Why it is required.** Phase S1 found three of fifteen scored Christian cases (LR005 Doctrine of Discovery, LR015 Canadian residential schools, LR016 U.S. boarding schools) score `match_type=formal_only_mechanism_mismatch`. The formal σ × π × exit_cost profile predicts CAPTURE, but the case's actual mechanism is enforcement projected onto a non-member or captive population, not voluntary-membership-with-blocked-exit. The current ABM cannot represent the distinction. Paper 3 (caste — colonial-Brahminical regime projecting onto lower jātis) is structurally an Extension 5 problem and cannot proceed without it.

**Cost:** ~400 lines, new agent class, new sweep dimension. Likely v3.1 or v4.0 of the ABM.

**Decision required:** Whether to include in revised Paper 2 or defer to Paper 3 as its native extension. My recommendation: defer. Note in revised Paper 2 §7 that captive-population regimes are outside Layer B's scope and require Extension 5; the four CAPTURE cases in Phase S1 reduce to two substantive matches (LR003, LR004) under the current ABM, which is the honest framing.

### Extensions to defer

- **Endogenous code drift** (the canon's interpretation shifts in response to enforcement intensity). This is a real phenomenon (Slave Bible, Vatican II) but is beyond Paper 2's scope.
- **Multi-tradition comparison.** The Nitrogen team's locked discipline says "Christianity first." The ABM should follow.

## 6. Required Nitrogen rescoring (Christian baseline rewrite)

For each of the 16 cases, produce a unified record with the following fields. Fields with `[ABM]` come from Paper 2's rubric. Fields with `[NIT]` come from Nitrogen. Fields marked `[NEW]` are introduced by the synthesis.

```yaml
case_id: LR015
case_name: Canadian Indian Residential Schools
period: 19th-20th centuries
region: Canada

# ABM scoring (replaces Nitrogen's T+L+I+C+MCI−R composite)
sigma: 4                    # [ABM] legibility 0-4
substitutability: 4         # [ABM] external compliance accepted as sufficient
enforcement_affordance: 4   # [ABM] sanctioning is profitable and routinized
centralization: 4           # [ABM] joint church-state authority
exit_cost: 4                # [ABM] children removed; language suppressed; kinship severed
predicted_regime: capture   # [ABM] from sigma × pi × exit_cost geometry
observed_regime: capture    # [NEW] from historical record

# Code-content layer (Nitrogen-derived)
argument_templates: [T3_expansion_mandate, T5_sacred_enforcement]   # [NIT]
text_role_assessment: authorizing                                     # [NIT]
counter_reading_present: false                                        # [NIT]

# Mechanism layer
exit_cost_mechanisms:                                                 # [NEW]
  - child_custody: 4
  - language_suppression: 4
  - kinship_severance: 3
  - legal_compulsion: 4
  - geographic_isolation: 2

# Non-textual forces
non_textual_forces:                                                   # [NIT]
  - state_power: 4
  - land: 3
  - class_control: 3
  - political_legitimacy: 3
  - empire: 3

# Evidence trail
verification_status: documented   # [NIT]
evidence_level: 4                 # [NIT] from 5-level hierarchy
source_ids: [SRC_LR015_NCTR_HISTORY, SRC_LR015_TRC_SUMMARY, ...]      # [NIT]

# Diagnostic
text_was_causal: yes_authorizing_and_motivating                       # [NEW]
non_textual_was_causal: yes_state_apparatus                           # [NEW]
joint_attribution: text_via_state                                     # [NEW]
```

Each case rewritten this way provides:
- An ABM regime classification (testable against the observed historical regime),
- A code-content profile (testable against canonical textual analysis),
- Explicit confounders (forcing causal honesty),
- Evidence trail (forcing claim discipline).

The 16 rewrites become Paper 2's revised §9 *and* Paper 3's foundation.

## 7. Sweep restructuring (ABM)

Current sweeps total 3,246 runs across 5 sweep types. After extensions 1, 3, 4, the necessary new sweeps are:

| Sweep | Purpose | Approximate run count |
|---|---|---|
| Argument-template envelope sweep | Confirm T1–T8 mapping to (σ_max, π_max, exit_cost_baseline) | 8 templates × 5 grid points × 30 seeds = 1,200 |
| Non-textual force interaction sweep | Verify that exogenous force perturbation moves regime as predicted | 4 forces × 4 levels × 10 seeds = 160 baseline + 480 confirmatory |
| Exit-cost mechanism decomposition sweep | Show that scalar exit cost decomposes correctly | 6 mechanisms × 4 levels × 30 seeds = 720 |
| Christian regime replication sweep | For each of 16 cases, run ABM at scored parameters and verify regime classification matches observed | 16 cases × 30 seeds = 480 |

Total new runs: ~3,000. At 4–6 hours per 360 runs on a 64-core machine (per Boron README), this is ~50–80 hours of wall-clock time, easily parallelizable. Not a blocker.

## 8. Paper 2 restructuring

Current Paper 2 structure (per the .tex file):

```
1. Introduction
2. Literature positioning
3. Theoretical framework
4. Parameter-observable mapping
5. Scoring rubric
6. Agent-based model
7. Scope and limitations
8. Results
9. Discussion (incl. weak observational §9.4)
10. Conclusion
```

Proposed restructure:

```
1. Introduction (revised: state synthesis claim)
2. Literature positioning (light revision)
3. Theoretical framework
   3.1 Code geometry (existing)
   3.2 Code content as upstream constraint (NEW — argument templates)
   3.3 Non-textual forces as exogenous perturbations (NEW)
4. Parameter-observable mapping
5. Scoring rubric (extended with text_role_assessment, non_textual_forces)
6. Agent-based model
   6.1-6.10 (existing)
   6.11 Argument-template envelope (NEW)
   6.12 Exit-cost mechanism decomposition (NEW)
7. Scope and limitations
8. Results
   8.1-8.10 (existing baseline)
   8.11 Argument-template sweep (NEW)
   8.12 Non-textual force sweep (NEW)
   8.13 Exit-cost mechanism sweep (NEW)
9. Empirical application: 16 Christian regimes (REPLACES current §9.4)
   9.1 Methodology
   9.2 Documented cases (LR015, LR006)
   9.3 Plausible cases (14 others)
   9.4 Pattern across cases
   9.5 Cross-tradition deferred
10. Discussion (revised)
11. Conclusion
```

Section 9 becomes the empirical spine instead of an underpowered observational appendix. The 16 cases deliver what Paper 2's current §9 admits it does not: a structured comparison with attached evidence at the level required by the rubric.

## 9. What this means for Paper 3 (caste)

Paper 3 was originally going to apply Paper 2 to the colonial-caste nexus. With the synthesis, Paper 3 becomes:

- **Method:** Same ABM rubric, applied to two regimes whose collision is the case.
  - Regime A: pre-colonial varṇa-jāti dharmaśāstra system (low σ in most regions, ritual-locality-dependent enforcement, low centralization, high exit cost via kinship endogamy).
  - Regime B: colonial Christian missionary apparatus + British classificatory state (high σ via census/legal categories, π via state alliance, exit cost via legal reclassification + missionary education).
  - Regime C: post-collision hybrid where census-rigidified caste replaces ritually-flexible varṇa.

- **Mechanism:** Show that Regime B raised σ across the substrate by *making the substrate legible to itself in colonial categories* — Scott's legibility extended through missionary ethnography, colonial census, and Risley's anthropometry. The substrate's exit-cost mechanisms (kinship endogamy) were not invented by colonialism but were *ossified* by colonial classification because once jāti became a legible legal category, it became enforceable.

- **Text role:** This is where `text_role_assessment` matters most. In pre-colonial dharmaśāstra, text was largely **legitimating** of an already-operating ritual mechanism. In colonial-Christian missionary regime, text was **driver and authorizing** of conversion mandates and civilizational hierarchies. The collision produced the modern caste system as a **co-legitimating** structure where Brahminical text and colonial classification reinforced each other. This is a Paper 3 thesis claim, testable against the 16-case Christian baseline + a parallel pre-colonial Indic baseline (deferred to Paper 4 or the comparative phase).

- **Missionary case:** LR015 (residential schools) and LR016 (Carlisle) are the structural analogs to colonial mission education in India (Doveton, Bishop Cotton, La Martiniere). The mechanism transfers. The *failure* of full Christianization in India relative to Canada is itself diagnostic — the substrate's pre-existing high exit cost via caste endogamy made the missionary regime's marginal contribution to exit cost negligible, so Regime B did not capture the population the way it captured Indigenous Canadians whose substrate had different exit-cost mechanisms. This is testable in the synthesized ABM.

## 10. Sequencing and decision points

Recommended order:

**Phase S1 — Translation. COMPLETE 2026-04-27.**
Output: `synthesis/unified_christian_baseline_v1/` with 16 cases scored (15 substantive, 1 declined per Q1). Substantive match rate 9/12 = 75% under the Q5 schema (boring_null and formal_only_mechanism_mismatch decomposed honestly). Surfaced Extension 5 as a new fifth extension (this revision adds it to §5). Surfaced the COLLAPSE-narrow-definition issue and the regime-vs-event-axis issue as Phase S5 manuscript-revision items (logged in §15 below). Confirmed the active-rate gotcha quantitatively: 18 of 72 v2.5 cells flip QUIET → MIXED under corrected classification.

**Phase S2 — ABM Extension 1 (argument-template input vector). 2–4 weeks. NEXT.**
Per Q1 resolution (theoretical derivation, see §12), envelope mapping derives from the eight templates' structural variables in `argument_templates.json`, not from empirical calibration on the 16-case corpus. Saves 1–2 weeks relative to the empirical-calibration path. New work goes in `src/religion_fundamentalism_abm_v3_0.py` per the append-only versioning rule. Sweep specification: 8 templates × 5 grid points along a low-π → high-π diagonal within each envelope × 30 seeds = 1,200 runs. Active-rate-at-sweep-time required (no post-hoc reclassification). Detailed task spec in `INSTRUCTION_BORON_S2.md` (forthcoming).

**Phase S3 — ABM Extensions 3 and 4 (non-textual forces; exit-cost decomposition). 2 weeks.**
Mechanically simpler. Can run in parallel with S2.

**Phase S4 — Christian regime replication sweep. 1 week.**
Validates the synthesis. For each of 16 cases, score parameters from Phase S1, run ABM, compare predicted regime to observed regime. Failures are findings.

**Phase S5 — Paper 2 restructuring and submission. 2–4 weeks.**
After S1–S4, write revised paper.

**Decision points for Kiran:**

1. After Phase S1: Are the 16 cases cleanly rescorable, or does the rescoring reveal a deeper structural problem? If clean, proceed. If not, the synthesis architecture in §4 needs revision.
2. After Phase S2: Did argument templates as input to the ABM produce coherent envelope predictions? If yes, this is the strongest result of the revision and goes in §3.2 of revised Paper 2. If no, fall back to coding text content as a diagnostic output only (current Nitrogen approach).
3. After Phase S4: Did the ABM correctly predict regime classification for the 16 cases? Whatever happens, this is the empirical spine of revised Paper 2.

**Extension 2 (rival-regime competition for counter-readings):** explicitly deferred. Note in Paper 2 §7. Possible standalone paper.

## 11. What dies in this synthesis

For honesty, list what gets discarded:

- **Nitrogen's verse-level scoring (C/A/M/E/U/O/R/P) on 31,102 KJV passages.** Three phases of work. No downstream use even within Nitrogen. The synthesis does not need it. Argument templates (T1–T8) replace it at the case level. The corpus and commentary linkage tooling can be archived but is unlikely to be reused.

- **Nitrogen's composite `control_axis_activation_score = T+L+I+C+MCI−R`.** Replaced by ABM regime classification. The component variables are kept where they map onto ABM parameters; the composite itself is dropped.

- **Nitrogen's 500-passage validation infrastructure.** Already abandoned (zero passages annotated). Confirmed unrecoverable.

- **The original ABM's claim that code content is orthogonal to code geometry.** Specifically: §7's "Two systems with identical code geometry scores but radically different theological commitments are predicted to exhibit similar enforcement dynamics" needs revision. The synthesis says: code content determines which geometries are *reachable*, after which geometry determines dynamics. This is a meaningful retreat from the original strong claim, but the empirical evidence will likely support the weaker claim better than the stronger one.

## 12. Open questions

These are unresolved and the synthesis cannot proceed past Phase S2 without answers:

**Q1.** Does the argument-template envelope mapping (Extension 1) require empirical calibration from the 16 cases, or can it be derived theoretically from the templates' structural variables (already specified in `argument_template_seed.csv`)? If the former, Phase S1 must produce calibration data. If the latter, S2 is independent of S1.

**Q2.** Is `text_role_assessment` an output (diagnostic of what the text did during a run) or an input (a claim about how the text functions in this tradition)? The synthesis assumes output. The decision affects whether Layer A produces this field or Layer B does.

**Q3.** How does the synthesis handle the **transpersonal authority** discussion (Paper 2 §9.5)? That section already starts moving in the synthesis direction (apaurusheya → low σ → no enforcement niche). It is currently the weakest section of Paper 2 because it asserts a relationship without modeling it. The synthesis offers a way to formalize it — apaurusheya is a code-content feature that constrains σ_max — but doing so requires Extension 1 to be calibrated for non-Christian templates, which violates the Christianity-first scope. Alternatives: (a) cut §9.5 from revised Paper 2; (b) keep it but explicitly mark as conjecture pending comparative phase; (c) derive a single Indic argument template (apaurusheya + ahimsa cluster) and test only its envelope mapping, not full historical instances.

**Q4.** Counter-reading regime (Extension 2): the four restraint cases in Nitrogen (LR011–LR014) are scored as low control-axis but high R. Without Extension 2, the synthesis cannot represent them — the ABM has no rival-regime mechanism. Are they:
- (a) excluded from the 16-case validation set in revised Paper 2, with a note that restraint regimes require Extension 2;
- (b) included as "regimes with low σ × π that did not produce enforcement equilibria," using only ABM Layer B without rival-regime mechanism;
- (c) included with an explicit caveat that the model captures only their failure-to-capture-the-population aspect, not their rival mobilization aspect.

I lean (b) for revised Paper 2 and (c) once Extension 2 is built.

### Resolutions from Phase S1 (2026-04-27)

**Q1 RESOLVED — theoretical derivation.** Template usage in the 16-case corpus is too skewed for empirical envelope calibration: T2 has 0 cases, T1/T6/T8 each have ≤1. Theoretical derivation from the structural variables (C, A, M, E, O, U, R, P) specified in `argument_templates.json` is the path. Empirical match within the corpus serves as consistency check, not primary calibration. Detailed derivation rationale appears in `INSTRUCTION_BORON_S2.md` §3.

**Q2 RESOLVED — `text_role_assessment` stays as a Layer C coding annotation.** Phase S1 found the field correlates meaningfully with regime classification (`coordinating` perfectly correlates with QUIET; `authorizing`/`legal_basis` cluster around MIXED→CAPTURE; `legitimating` flags cases where non-textual forces dominate) but is not derivable from ABM dynamics alone. Keep it traveling alongside case data; do not promote to first-class ABM input or output.

**Q3 DEFERRED to Phase S5.** The transpersonal authority (apaurusheya) discussion stays where it is in the current manuscript with a `speculative` flag, pending the comparative phase.

**Q4 RESOLVED — option (b) for revised Paper 2; transition to (c) once Extension 2 is built.** Restraint cases (LR011–LR014) included as low-σ × low-π regimes that did not produce enforcement equilibria. Their `match_type=boring_null` for three of four (the framework correctly predicts QUIET for low-everything but this is a sanity check, not validation) is reported separately from substantive matches.

**Q5 (added in S1) RESOLVED — match-type schema preserved.** Four-valued `match_type` field (`substantive`, `boring_null`, `formal_only_mechanism_mismatch`, `null`) is the honest reporting unit. The raw match rate (15/15 = 100% if reported alone) overstates framework performance; the substantive rate (9/12 = 75%) is the framework-validation number.

## 13. What to do next

If you accept this synthesis architecture: instruct Codex on Boron to begin Phase S1 — produce `unified_christian_baseline_v1.csv` rescoring all 16 cases in the unified vocabulary, with per-case markdown notes citing existing Nitrogen evidence trails. This requires no new ABM code, no new sweeps. It is a translation exercise, but a concrete one that exposes whether the synthesis architecture survives contact with the cases.

If Phase S1 succeeds, the larger ABM extensions (Phases S2–S4) follow.

If Phase S1 reveals that the 16 cases resist rescoring — for instance, if multiple cases require sub-regime decomposition that the ABM cannot represent — that is a finding that constrains the synthesis and may force narrower scope.

The Nitrogen rescoring should happen on Boron, not Nitrogen, because the ABM lives there and the rescoring's purpose is to feed into ABM extensions. Nitrogen becomes the source of evidence and the source-of-truth for documentation; Boron becomes the home of the unified scored cases. This avoids duplicating evidence trails.

## 14. Issues surfaced by the Boron CLAUDE.md authoring session (2026-04-27)

After this synthesis doc was drafted, a separate Claude Code session authored `CLAUDE.md` at the Boron repo root and surfaced two operational findings worth folding into the plan:

### 14.1 Active-rate gotcha in regime classification

`metrics.csv` stores `punish_rate = punished / N_total`, but exited agents always have `punished = 0`. With observed exit rates of 60–70%, raw rates dilute punishment intensity by the same fraction. `scripts/reclassify_regimes.py` produces `reclassified_seed_results.csv` and `reclassified_summary.csv` with corrected `active_punish_rate = punish_rate / (1 − exit_rate)`.

**18 of 72 v2.5 confirmatory cells flip from QUIET to MIXED under the corrected classification** (verified by counting `cell_reclassified_hier=True` rows in `reclassified_summary.csv`). The corrected counts are roughly 1 capture, 8 quiet, 54 mixed, 9 collapse — versus the manuscript's reported 1 capture, 26 quiet, 36 mixed, 9 collapse from uncorrected data.

This affects three things:

- **Phase S1**: when comparing the ABM's predicted regimes for the 16 Christian cases against the manuscript's reported empirical regime distribution, use the *corrected* distribution as the truth. Documented in `INSTRUCTION_BORON_S1.md`.
- **Phase S2**: the new argument-template envelope sweep must compute `active_punish_rate` from the start, not rely on downstream reclassification. Documented in `INSTRUCTION_BORON_S2.md`.
- **Phase S5 (manuscript revision)**: §8.1, Table 5, Figure 1, and per-regime concentration metrics must be regenerated from `reclassified_seed_results.csv`. New figure outputs go in a new whitelisted result directory; original results stay frozen as reproducibility artifacts.

### 14.2 Append-only model versioning

Old model files (`v2_5.py`, `v2_4.py`, etc.) are reproducibility artifacts tied to committed CSVs, not deprecated code. Editing them silently invalidates manuscript figures. New work goes in new files. Phase S2's v3.0 naming is consistent with this.

This rule has been added explicitly to both Boron instruction files. It also implies that the synthesis cannot "fix" perceived issues in v2.5 in place; if Phase S1 or S2 reveals that v2.5 has a real bug (not just the active-rate issue, which is downstream), that bug is fixed in v3.0 and v2.5 stays unchanged.

### 14.3 Style mismatch (minor)

The user's global `~/.claude/CLAUDE.md` specifies seaborn/plotly + camelCase. The existing publication code is matplotlib + snake_case. Per the Boron `CLAUDE.md`, existing publication figures stay as matplotlib (frozen artifacts); new analysis figures should use seaborn for static publication and plotly for interactive notebooks. Affects Phase S2 onward.

---

## 15. Phase S1 findings beyond the original instruction

Three findings surfaced in Phase S1 that are not absorbed into §5–§12 above and are tracked here for Phase S5 manuscript revision:

### 15.1 COLLAPSE-narrow-definition

The ABM's COLLAPSE label requires `exit_rate ≥ 0.90` (enforcement-induced depopulation). This excludes a real and empirically common regime type: slow attrition under loose enforcement (mainline Protestant decline, late-modern Catholicism, the "nones" demographic transition). LR014 forced this finding. Phase S5 manuscript-revision item: clarify in §6.10 that COLLAPSE in the ABM denotes specifically enforcement-induced depopulation, and that slow attrition under loose enforcement is observationally distinct but currently flattened to MIXED or QUIET. The framework's substantive claim — that code geometry produces the four labeled regime *types* — is preserved; the manuscript clarification is about what the labels denote, not what the ABM produces.

### 15.2 Regime-vs-event-axis

Two cases (LR001 First Crusade 1095–1099, LR002 Albigensian Crusade 1209–1229) are mobilization episodes shorter than the ABM's 500-step steady-state assumption suggests. They were scored by treating the regime unit as the underlying papal authorization apparatus during the crusade window. Phase S5 manuscript-revision item: add a brief note in §5 (Scoring Rubric) clarifying that the regime unit must be long enough for steady-state enforcement to be a defined notion. Episodes shorter than ~50 simulation timesteps' equivalent should either be reframed to the underlying enduring apparatus or scored with explicit confidence flags.

### 15.3 Active-rate gotcha — manuscript figure rebuild

Quantitatively confirmed in Phase S1: 18 of 72 v2.5 confirmatory cells flip QUIET → MIXED under corrected classification (8 quiet / 54 mixed / 9 collapse / 1 capture, vs. manuscript-reported 26 / 36 / 9 / 1). Phase S5 must regenerate §8.1, Table 5, Figure 1, Figure 2, and per-regime concentration metrics from `reclassified_seed_results.csv` and place them in a new whitelisted result directory (suggested: `results/v2.5_corrected_three_regime_confirm_active_rate/`). The original `results/v2.5_corrected_three_regime_confirm/` directory must not be overwritten — per CLAUDE.md it is a frozen reproducibility artifact.

---

*End of synthesis working document. Last update: 2026-04-27, post-Phase-S1.*
