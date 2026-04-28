# Mismatches Report — Phase S1

**Phase:** Synthesis Phase S1 — Christian baseline rescoring
**Source data:** `unified_cases.jsonl` (16 cases)
**Date:** 2026-04-27

---

## Headline finding

**Zero formal mismatches** (`regime_match=False`) across the 15 scored cases. **One declined case** (LR007). **Six matches that warrant separate explanation** despite being formally `regime_match=True`:

- 3 *boring-null* matches (LR011, LR012, LR013): the framework correctly identifies low-σ × low-π regimes as QUIET — a sanity check, not a framework validation.
- 3 *formal-only-mechanism-mismatch* matches (LR005, LR015, LR016): the predicted regime matches the observed regime by formal score, but the *mechanism* the rubric describes does not apply to the case.

This means the substantive match rate — the rate at which the framework's claim is genuinely tested and confirmed — is **9 of 12 informative cases** (the 9 substantive matches out of the 12 cases that are not boring nulls and not declined). The remaining 3 informative cases are formal-only-mechanism-mismatches, which are not framework validations but case-level diagnostic findings about the ABM's scope.

The decomposed match rate is therefore more honest than the raw 15/15 number, and the explicit `match_type` field in `unified_cases.jsonl` makes this decomposition queryable rather than buried in prose.

The 15/15 raw rate is suspicious in the abstract, and the dry-run flagged confirmation-bias risk before scoring. The audit (documented in `scoring_decisions` per case) found:

- Five cases were specifically considered for tilting up (LR003 considered between MIXED and CAPTURE; LR009 same; LR002 same), with the score held at the conservative position when the institutional consolidation argument supported it (LR003, LR004) or tilted down when it didn't (LR009).
- One case (LR014) was specifically considered for tilting from QUIET to MIXED per Q4 ruling — that override is documented and surfaced as a finding rather than absorbed.
- Two cases (LR015, LR016) sit at the rubric ceiling (4/4/4/{3-4}/4) and would have produced CAPTURE under any reasonable scoring; the structural-mismatch finding is what those cases produce *despite* the formal match.

The corpus also has a coverage bias that contributes to the high formal match rate: the 16 Christian cases were selected by Nitrogen because they were either well-documented enforcement-dominant regimes or well-documented restraint counter-readings. Genuine moderate-uncertainty cases (e.g., 19th-c. Lutheran state churches in Scandinavia, where σ × π × E sits in the contested middle of the parameter space) were not part of the case bank to begin with. This means the framework was not stress-tested against ambiguity; it was tested against extremes plus their inverses. A future Phase S4 should include moderate cases.

---

## Section 1 — Cases that reveal an ABM scope limitation: enforcement projected onto non-member or captive populations

These three cases (LR005, LR015, LR016) score `regime_match=True` and `match_type=formal_only_mechanism_mismatch` because **the predicted regime matches the observed regime in formal score, but the mechanism the ABM rubric describes — voluntary-membership communities with exit-by-departure — does not apply to the case**.

The ABM models enforcement *within* a community of voluntary members evaluating whether to stay or leave. Each of these three cases involves a regime that operated by *projecting* its enforcement onto a population that did not choose membership and could not exit on the regime's terms. The match is by accident of formal score, not by mechanism.

Per Q3 disposition, this grouping is a recurring scope limitation rather than a per-case quirk. It is also a substantive Phase S2 input (Extension 5 flag — target-population modeling, not yet specified in detail).

### LR005 — Doctrine of Discovery / colonial conquest

**Predicted: MIXED (L=3, S=3, A=3, C=4, E=2). Observed: MIXED. regime_match=True. match_type=formal_only_mechanism_mismatch.**

The rubric scores the orthodoxy-among-clergy-and-colonizers axis (per Q3 disposition). Clergy in colonial settings could leave a religious order, return to Europe, or transfer between orders — moderate exit cost, moderate enforcement, internal heterogeneity (Las Casas as Christian internal critique). MIXED is the formal prediction.

But the case's substantive content is the regime's *external projection* onto Indigenous peoples — papal bulls authorizing crown sovereignty over conquered lands, missionary-colonial conversion enforcement, dispossession through *Inter Caetera* and the legal-afterlife (*Johnson v. M'Intosh*, 1823). The targets are not members of the regime in the ABM's sense; they did not choose to enter and could not negotiate exit on the regime's terms.

The ABM's exit-cost dimension is not measuring what the case is about. The match is a coincidence of formal score, not validation of the framework's mechanism.

This is a Phase S2 Extension 5 input.

### LR015 — Canadian Indian Residential Schools

**Predicted: CAPTURE (L=4, S=4, A=4, C=4, E=4). Observed: CAPTURE. regime_match=True. match_type=formal_only_mechanism_mismatch.**

The rubric scores the system at the maximum on every dimension. The TRC documentation supports each: continuous behavioral surveillance of children (σ=4), external Christian-civilizational compliance treated as conversion regardless of internal disposition (S=4), comprehensive disciplinary infrastructure (A=4), federal Indian Affairs administrative monopoly across four denominations (C=4), and child-custody-with-legal-compulsion exit cost (E=4). The score profile matches CCP party discipline and Stalinist self-criticism (S1 Text Table 5: 4,4,4,4,4 → Capture).

But the *mechanism* the ABM describes is voluntary-departure cost in a community of agents weighing whether to stay or leave. That mechanism is not what was operating at residential schools. The exit cost was *legal compulsion of minors who never chose to enter*, enforced by adults outside the regime (federal Indian agents, RCMP) on a target population (Indigenous children). The system was imposed, not chosen, and "exit" is replaced by "physical custody."

The framework's prediction is correct in form. The mechanism is qualitatively different.

This is the most diagnostically important case in the corpus. It is the canonical Phase S2 Extension 5 case and a substantive Phase S5 manuscript-revision item. The current ABM cannot represent what made the residential school regime function: not high voluntary-departure cost but the legal removal of children's capacity to be members-with-exit at all. Paper 3 (caste) faces the same structural issue (colonial-Brahminical regime projecting on lower jātis, who were not members of the orthodox Brahminical regime in the ABM's sense).

### LR016 — U.S. Native American boarding schools / Carlisle model

**Predicted: CAPTURE (L=4, S=4, A=4, C=3, E=4). Observed: CAPTURE. regime_match=True. match_type=formal_only_mechanism_mismatch.**

Mirrors LR015 with C=3 (less unified federal-religious apparatus than Canada — substantial denominational variation and federal-only schools without church partnership). DOI 2022 documentation, NPS Carlisle records, and the Pratt assimilationist program ("Kill the Indian, save the man" — preserved here as U.S. Carlisle attribution per `methodology_locked.md`) support the maximum-on-everything-except-C scoring.

Same structural mismatch as LR015: children-as-targets, not members-with-exit.

### What these three cases collectively tell Phase S2

The ABM as currently specified cannot represent regimes whose primary enforcement modality is projection onto a non-member population. The phenomenon is real and historically central — colonialism, residential schools, caste rigidification under colonial classification — but the ABM's voluntary-membership framing assumes its primary enforcement target is the regime's own members.

**Phase S2 Extension 5 (target-population modeling)** is the unspecified-but-needed extension this finding flags. The synthesis architecture in `SYNTHESIS_WORKING_DOC.md §5` named four extensions; this is a fifth. Per Q3 disposition: do not design Extension 5 in detail, just flag the need. Synthesis Q3 framing: "the ABM handles enforcement within a voluntary-membership community; it does not handle enforcement projected outward onto a target population that is not a member of the regime in the ABM's sense."

This is also Paper 3's central methodological problem.

---

## Section 2 — Cases scored as matches but representing a "boring null" rather than framework validation

These three cases (LR011, LR012, LR013) score `regime_match=True` and `match_type=boring_null`. The prediction matches the observation because **the rubric correctly identifies low-σ × low-π regimes as QUIET — a sanity check, not a framework validation**.

The framework's interesting empirical claim is about CAPTURE emergence under high-σ × high-π × high-exit-cost. None of these three cases tests that claim. They test only the framework's complement: that low-σ × low-π × low-exit-cost does *not* produce capture, which any sensible rubric would predict.

Per synthesis Q4 option (b): include these cases anyway, with `match_type=boring_null` so the inflation of the raw match rate is queryable rather than buried.

### LR011 — Abolitionist biblical counterreading

L=1, S=0, A=1, C=1, E=0 → predicted QUIET. Abolitionism mobilized politically but did not enforce orthodoxy on its own members through punishment. The case's substantive content — *rival mobilization on the same canon as the pro-slavery clerical regime LR006* — is invisible to the ABM. Phase S2 Extension 2 (rival-regime competition) is what this case demands; the boring-null match is the best the current ABM can do.

### LR012 — Quaker anti-slavery practice

L=1, S=0, A=0, C=0, E=0 → predicted QUIET. Exact match to S1 Text Quaker-meeting anchor (1,0,0,0,0 → Quiet). Inner-light epistemology resists external-compliance proxy; disownment from meeting is loss of fellowship without coercive sanction. Same as LR011 — the rival-regime aspect is invisible.

### LR013 — Liberation theology

L=1, S=1, A=1, C=1, E=1 → predicted QUIET. Slightly elevated relative to Quaker because base communities are more institutionally structured, but still well below activation. The movement was politically vigorous but internally non-enforcing.

### What these three cases collectively tell Phase S2

**Phase S2 Extension 2 (rival-regime competition)** is required to evaluate restraint cases substantively. Until then, the boring-null match is the best the ABM can do, and the boring-null match rate (3 of 15 = 20%) should be reported separately from the substantive match rate.

---

## Section 3 — A case where rubric and observation diverge but were called a match per Q4 disposition

### LR014 — Modern universalist / softening interpretations

**Predicted: MIXED (per Q4 override). Observed: MIXED-with-high-attrition. regime_match=True. match_type=substantive (with caveat).**

This case warrants explicit treatment because the rubric strictly applied would have produced a different prediction.

**The strict rubric reading:** L=1, S=1, A=1, C=1, E=0–1. Per the manuscript's dose-response §8.12 (S1 Text Table 5 anchors plus the published curve), σ ≈ 0.20–0.25 at low π should produce sub-activation: enforcement does not engage. The strict ABM prediction is therefore QUIET.

**The observation:** mainline Protestant + post-Vatican II Catholic regimes have low active enforcement *combined with* high attrition — the "nones" demographic transition, Pew retention <50% for some denominations. This is empirically *not* QUIET (QUIET implies stable population at low enforcement) but also not COLLAPSE in the ABM's sense (COLLAPSE in §6.10 requires enforcement-induced depopulation, exit_rate ≥ 0.90).

**Per Q4 disposition:** score predicted=MIXED, observed=MIXED, match=true. The ABM rubric flattens "loose-enforcement-with-attrition" into MIXED because there is no formal regime category for it.

**The finding (Phase S5 manuscript-revision flag):** the ABM's COLLAPSE label is too narrowly defined. It requires enforcement-induced depopulation, which is one specific mechanism of religious decline. Real-world religious decline frequently happens *without* enforcement tightening — attrition under loose enforcement, cultural pluralism eroding inherited affiliation, the secular-substitute hypothesis. The current rubric absorbs this into MIXED or QUIET depending on the scorer's choice; neither is faithful to the case.

This is a substantive §9 Discussion item for Paper 2 revision. The COLLAPSE definition in §6.10 should be clarified ("enforcement-induced depopulation") and a parallel category for non-enforcement-induced attrition should be considered, either as a separate regime or as a sub-classification within MIXED/QUIET.

The 15/15 raw match rate is *not* enhanced by LR014 — the match here is a Q4-judgment-call match, not a strict-rubric match. If a future analyst applies the rubric strictly without Q4 override, LR014 would flip to mismatch (predicted QUIET, observed MIXED-with-high-attrition), and the substantive match rate would drop from 9/12 to 8/12. Either reading is defensible. Documented here so the choice is visible.

---

## Section 4 — The declined case

### LR007 — Missionary-colonial conversion regimes (DECLINED)

Per Q1 disposition: `predicted_regime=null`, `observed_regime=null`, `regime_match=null`, `match_type=null`.

The Nitrogen scope ("16th–20th centuries, Americas Africa Asia") is too broad to score as a single regime. Internal heterogeneity is too large: a Jesuit reduction in 17th-c. Paraguay, a Protestant CMS station in 19th-c. India, and a Catholic White Fathers mission in 20th-c. Rwanda are all "missionary-colonial conversion regimes" but have radically different code geometries, especially on exit-cost mechanisms.

Picking a narrowest-defensible sub-instance would add a Christian case to the corpus that Nitrogen did not separately evidence — methodologically dubious. EXPORT_NOTES corroborates the scope problem: "evidence is weighted toward Atlantic and early American examples rather than all missions across Africa and Asia."

**This decline is itself a Phase S2 input.** Extension 4 (exit-cost mechanism decomposition) is exactly the kind of mechanism that would let LR007's heterogeneous instances be distinguished without flattening. The ABM's scalar exit_cost cannot represent the variation; the synthesis Extension 4 specifically can. Different missions had different exit cost mechanisms (Jesuit reductions: geographic isolation + linguistic incorporation; Protestant CMS in India: primarily symbolic conversion with weak exit cost; African mission stations: colonial-state-backed compulsion).

---

## Cross-case diagnoses (taxonomy from instruction)

The instruction's mismatches taxonomy has four causes: (a) scoring error, (b) rubric inadequacy, (c) evidence inadequacy, (d) ambiguity in regime classification thresholds. With zero formal mismatches, the relevant diagnoses apply to the *match-but-not-validating* cases above.

**Cause (a) scoring error:** none identified. The dry-run audit and per-case `scoring_decisions` confirmation-bias notes find that the scoring is internally consistent with the rubric anchors and the evidence trails.

**Cause (b) rubric inadequacy:** LR014 (loose-enforcement-with-attrition not formally distinguished from MIXED) and the LR005/LR015/LR016 group (target-population enforcement not modeled). These are real findings, surfaced for Phase S2 Extension 5 and Phase S5 manuscript revision.

**Cause (c) evidence inadequacy:** LR007 (declined) is the canonical case. EXPORT_NOTES already documents that Nitrogen evidence is weighted to Atlantic / early American examples; the scope (16th–20th c., three continents) outruns the evidence. Nitrogen evidence_quality=3 acknowledges the gap.

**Cause (d) classification-threshold ambiguity:** LR002 (MIXED→CAPTURE boundary), LR009 (same), LR014 (MIXED-vs-QUIET boundary, resolved by Q4 override). These are flagged in `scoring_decisions` per case but do not destabilize the match status under the conservative scoring chosen.

---

## Implications for Phase S2

In order of importance:

1. **Extension 5 (new — target-population modeling)** is needed before Phase S4 can validate LR005, LR015, LR016 substantively. Three of fifteen scored cases (20%) require it.

2. **Extension 2 (rival-regime competition)** is needed to evaluate LR011–LR013 substantively. Three of fifteen scored cases (20%) require it. Synthesis already had this as deferred — Phase S1 confirms it cannot be deferred indefinitely if the restraint cases are to be informative.

3. **Extension 4 (exit-cost mechanism decomposition)** is needed to score LR007 at all (if scored), and to handle the Goa-vs-metropolitan distinction within LR004. Synthesis already had this scoped.

4. The COLLAPSE-narrow-definition finding (Q4) is a Phase S5 manuscript-revision item, not a code extension.

5. The active-rate gotcha (manuscript reports 26 quiet / 36 mixed under uncorrected `punish_rate`; reclassified counts are 8 quiet / 54 mixed) is a Phase S5 figure-rebuild item, surfaced separately in `synthesis_findings.md` §8.

---

*End of mismatches report.*
