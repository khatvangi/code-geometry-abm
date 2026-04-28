# Phase S1 Dry-Run Report

**Purpose:** Pre-scoring inventory. Catches scope problems, regime-unit ambiguities, and decline-to-score cases *before* I commit numerical scores to `unified_cases.jsonl`.

**Status of inputs (verified):**
- PLOS submission `manuscript_PLOSONE.tex` §3–§5 read; rubric anchors from `S1_Text.pdf` Tables 1–5 captured.
- All 16 case records read from `case_export.jsonl`; methodology, EXPORT_NOTES, argument templates read.
- Rubric: 5 ordinal dimensions L, S, A, C, E ∈ {0,1,2,3,4}. Predicted regime ∈ {quiet, mixed, collapse, capture}.
- Active-rate gotcha noted: when comparing to manuscript empirical distribution, use *reclassified* counts, not raw.

---

## 1 — Headline taxonomy of the 16 cases

| Type | Cases | Count | Phase S1 stance |
|---|---|---|---|
| Enforcement-dominant, well-evidenced | LR001, LR003, LR004, LR005, LR015 | 5 | Score normally; expect MIXED/CAPTURE predictions. |
| Enforcement-dominant, plausible only | LR002, LR008, LR009, LR010, LR016 | 5 | Score normally with `medium` confidence on weaker dimensions. |
| Text-as-legitimator (text not driving) | LR006 | 1 | Score normally; flag that Nitrogen `text_role_assessment = legitimating` predicts the regime gets enforcement *power* from non-textual forces. |
| Restraint / counter-reading regimes | LR011, LR012, LR013, LR014 | 4 | **Cannot be evaluated as positive enforcement cases by current ABM rubric.** Per synthesis Q4: score *as if observed regime is QUIET*, predict QUIET, flag explicitly that the case's substantive content (rival mobilization on shared canon) is outside the model. |
| Scope problem: too broad to score as one regime | LR007 | 1 | **Decline to score as a single regime.** Justification below; either narrow to a defensible sub-instance or surface as a finding. |

Total: 5 + 5 + 1 + 4 + 1 = 16 ✓.

---

## 2 — Per-case proposals

For each case I list: regime_unit (the historically bounded scope I propose to score), expected confidence per dimension, predicted regime (rough sketch — to be confirmed during scoring), and any open issues.

Anchor calibration from S1 Text Table 5 (used to discipline my numbers):
- Counter-Reformation Roman Inquisition 1542–1700: L=3, S=3, A=4, C=4, E=3 → Capture
- Iranian morality police post-1979: L=4, S=3, A=4, C=4, E=3 → Capture
- Saudi CPVPV 1979–2016: L=4, S=3, A=4, C=3, E=3 → Capture
- Theravāda forest tradition: L=1, S=0, A=1, C=0, E=1 → Quiet
- Quaker meeting US: L=1, S=0, A=0, C=0, E=0 → Quiet

### LR001 — First Crusade

- **Regime_unit:** "First Crusade mobilization apparatus, 1095–1099, Latin Christendom under Urban II's papal authorization."
- **Note:** This is a *mobilization episode*, not a steady-state regime. The ABM models long-run dynamics over ~500 simulation steps. A 4-year crusade with rapid call-and-disband is an awkward fit. The question is whether to score the *underlying papal-clerical authorization apparatus* (which persists across centuries and is steady-state) or the *crusade as an event*.
- **Proposed**: score the underlying papal authorization regime *during the crusade window*. L=3 (papal indulgence rhetoric is observable; sermon attendance and crusader vow public). S=3. A=3 (excommunication for vow-breaking; oath enforcement). C=3 (papacy commands but with feudal dispersion). E=2 (medium — vow obligation is real but exit means going home, not legal apostasy). Predicted: MIXED.
- **Confidence:** medium across the board. The First Crusade isn't a long-run enforcement regime in the ABM's sense.
- **Open question:** Is "crusading mobilization" the right unit for the rubric, or should I reframe to "papal authorization apparatus, 1095–1291 (long-12th-13th c. crusading era)"? The latter fits ABM better but the Nitrogen evidence is keyed to 1095–1099. **Flag for review.**

### LR002 — Albigensian Crusade

- **Regime_unit:** "Albigensian crusade and Cathar suppression, 1209–1229, Languedoc, Innocent III through Louis IX."
- Similar scope question to LR001 (event vs. ongoing apparatus) but the suppression *did* settle into long-run anti-heresy administration (which becomes LR009-style).
- **Proposed:** L=3, S=3, A=3, C=3, E=3. Predicted: MIXED→CAPTURE boundary.
- **Confidence:** medium.

### LR003 — Spanish Inquisition

- **Regime_unit:** "Spanish Inquisition tribunal system, 1478–1834, crown-papal joint enforcement against conversos and heresy."
- This is the canonical inquisition case and maps cleanly to the S1 Text Counter-Reformation Inquisition row.
- **Proposed:** L=3, S=3, A=4, C=4, E=3. Predicted: CAPTURE.
- **Confidence:** high on A, C; medium on L, S, E (no documented testimony on actual exit cost beyond the converso category).
- Note: Nitrogen scores `text_role_assessment = legal_basis`, not `authorizing`. The text was a legal premise cited in tribunal procedure — not the originating motivator. Doesn't change ABM scoring (text role is orthogonal to σ), but worth flagging.

### LR004 — Portuguese Inquisition

- **Regime_unit:** "Portuguese Inquisition tribunal system, 1536–1821, metropolitan + Goa colonial branch."
- Two sub-regimes (metropolitan + Goa) with possibly different geometry. EXPORT_NOTES explicitly flags this: "tribunal-by-tribunal variation still needs narrower archival work."
- **Proposed:** Score as one regime with L=3, S=3, A=4, C=4, E=3 (mirror to LR003) but flag in `open_questions` that Goa may be a distinct sub-regime with different exit cost (forced conversion of Hindu/Muslim populations + colonial extraction = very different mechanism from Iberian conversos).
- **Confidence:** medium on the unified scoring; high if narrowed to metropolitan only.

### LR005 — Doctrine of Discovery / colonial conquest

- **Regime_unit:** "Doctrine-of-Discovery legal-doctrinal regime: papal bulls (1452 *Dum Diversas* through 1493 *Inter Caetera*) + their colonial-state implementation 15th–17th centuries."
- This case is *legal-doctrinal infrastructure*, not a single tribunal. Tricky for ABM — what's the population? Indigenous peoples being dispossessed are not "members of the regime" in the ABM sense. The actors are crowns + papacy + colonizers, with Indigenous peoples as targets, not members.
- **Open issue:** the ABM scores enforcement *within* a community. LR005 is enforcement *outward*, against conquered populations. The dimensions I'm scoring on are: how does the *Christian colonial regime* maintain orthodoxy among *colonizers and clergy*? That's coherent but it's not what Nitrogen is scoring.
- **Proposed:** Score the orthodoxy-among-clergy-and-colonizers axis. L=3, S=3, A=3, C=4 (papal-crown monopoly), E=2 (clergy can leave the order, but cost is high). Predicted: MIXED.
- **Confidence:** low. **The case requires a synthesis-level decision: is "the conquering Christian regime" the unit, or is it a multi-population coupled system that the ABM cannot represent?** Flag prominently.

### LR006 — Atlantic slavery pro-slavery biblical argument

- **Regime_unit:** "U.S. antebellum pro-slavery clerical-print regime, ~1820–1865, Protestant + Catholic clergy in slaveholding states."
- Narrowed from Nitrogen's 16–19c Atlantic scope because the documented evidence is overwhelmingly U.S. antebellum (Stringfellow, Fuller, Priest, Hopkins, Lord, Bacon — all U.S. antebellum Library of Congress sources).
- **Crucial:** Nitrogen `text_role_assessment = legitimating`. Per synthesis methodology, this means the text is *not* the driver — slavery is driven by labor/trade/race. The text legitimates an existing extraction system. ABM dimensions still scoreable but the *interpretation* is that scoring the regime as "high σ × π" overstates what the *text* did.
- **Proposed:** L=3, S=3, A=2 (clerical sanction was real but not robustly institutional — denominations split rather than enforcing single orthodoxy), C=2 (no monopoly — Methodists, Baptists, Presbyterians all split), E=2 (slaveholders could leave the church but not the slaveholding economy). Predicted: MIXED.
- **Confidence:** medium-high. Nitrogen has `evidence_quality=4` and 7 deep-dive evidence rows.
- **Note:** scoring_decisions will need to explicitly name the legitimator-vs-driver distinction.

### LR007 — Missionary-colonial conversion regimes

- **Decline to score as a single regime.** Justification:
  - Scope: "16th–20th centuries, Americas Africa Asia". This is **four centuries × three continents × dozens of denominations × hundreds of mission stations**.
  - Specificity: per Nitrogen's own EXPORT_NOTES, "Current source bundle supports civilizational and spiritual replacement pressures *in selected colonial settings* though local variation remains large."
  - Methodology rule: "The scoring unit is the regime, not the tradition." LR007 is closer to a tradition (or a class of regimes) than a regime.
  - Internal heterogeneity: a Jesuit reduction in 17th-c. Paraguay, a Protestant CMS station in 19th-c. India, and a Catholic White Fathers mission in 20th-c. Rwanda are all "missionary-colonial conversion regimes" but they have radically different code geometries (different exit cost mechanisms, different enforcement affordance).
- **Proposed disposition:**
  1. Note in `unified_cases.jsonl` with `predicted_regime = null`, `observed_regime = null`, `regime_match = null`, with a long entry in `scoring_decisions` and `open_questions` explaining why it's not scoreable.
  2. Surface as a finding in `synthesis_findings.md §1` (coverage): one of 16 cases is structurally too broad for the ABM rubric without scope narrowing, which is itself a Phase S2 input (Extension 4 exit-cost decomposition is exactly the kind of mechanism that would let LR007's heterogeneous instances be distinguished).
- **Alternative:** the user can, if they wish, instruct me to pick the narrowest defensible sub-instance — but that adds a Christian case to the corpus that Nitrogen did not score, which is methodologically dubious. **Default disposition is decline.**

### LR008 — Witch trials

- **Regime_unit:** "Early-modern European witch trial complex, ~1480–1750, post-*Malleus Maleficarum* judicial-demonological regime."
- This *is* a coherent regime — same demonological frame, similar legal procedures, recurrent across multiple European jurisdictions.
- **Proposed:** L=3 (demonological signs were "legible" — confessions, alleged marks), S=3, A=3 (procedures were established), C=2 (decentralized — local courts, not papal monopoly), E=3 (accusation often unappealable and lethal). Predicted: MIXED, with possible CAPTURE in the panic peaks.
- **Confidence:** medium. The case has substantial regional and temporal variation that scoring as one regime flattens.
- **Note:** Nitrogen flags "regional judicial variation remains significant" — same scope concern as LR007 but to a lesser degree. I will score it as a single regime with a confidence flag, not decline.

### LR009 — Heresy suppression

- **Regime_unit:** "Medieval-to-early-modern Christian heresy adjudication apparatus, 12th–17th c., conciliar + tribunal Western Christendom."
- **Overlap problem:** LR009 substantially overlaps with LR002 (Albigensian, an instance), LR003 (Spanish Inquisition, an instance), LR004 (Portuguese Inquisition, an instance), and LR008 (witch trials, sometimes adjudicated under heresy). Nitrogen seems to have included LR009 as a *generalized* version of LR002–LR004 + the Roman Inquisition.
- **Proposed:** Score as the medieval Roman Inquisition specifically (1231–1542, pre-Spanish-Inquisition), to avoid double-counting. L=3, S=3, A=3, C=3, E=3. Predicted: MIXED→CAPTURE.
- **Open issue:** Should I score it at all if it overlaps so heavily with LR002, LR003, LR004? **Flag for review.** My current view: yes, score it as the medieval Roman Inquisition specifically, because that period is not otherwise covered.
- **Confidence:** medium.

### LR010 — Anti-Jewish expulsion / persecution arguments

- **Regime_unit:** "Latin Christian anti-Jewish expulsion-and-persecution complex, ~1215 (Lateran IV) – 1492 (Spain expulsion), Western Europe."
- Nitrogen scores this *lower* on control axis: T=3, L=2, I=2, C=2 (composite 9 vs. typical 12). `text_role_assessment = identity_boundary_marker`, not authorizing — text marks the inside/outside line but doesn't authorize specific enforcement actions.
- **Proposed:** L=2 (badge requirements are observable but episodic, not continuous), S=2, A=2 (sanctions exist but are not part of routine institutional infrastructure for most periods), C=2, E=3 (apostasy from Judaism into Christianity available but reverse not — and forced conversion + expulsion mean exit is *imposed*, not chosen). Predicted: MIXED with occasional collapse-events (1290 England, 1492 Spain expulsions are local collapse from the Jewish-community side; the Christian regime persists).
- **Confidence:** medium-low. The dimension that's hardest is: whose perspective is the regime? Nitrogen has Christian regime targeting Jews; is the regime "Latin Christianity's boundary-marking apparatus" or "the Jewish community under Christian pressure"? I propose the former — score the Christian regime's boundary apparatus.

### LR011 — Abolitionist biblical counterreading (RESTRAINT)

- **Regime_unit:** "Atlantic Christian abolitionist scriptural-counterreading network, 1780s–1865, primarily U.S. and British Protestant reform."
- Nitrogen restraint score R=3, control axis composite 5 (low). `text_role_assessment = coordinating` — text aligns dispersed reformers, doesn't authorize coercion.
- **Synthesis Q4:** the four restraint cases (LR011–LR014) are rival regimes operating on overlapping canon with the pro-coercion regimes (LR006 in particular). The current ABM cannot model rival-regime competition (deferred to Extension 2).
- **Proposed:** Score per synthesis Q4 option (b): include as "regimes with low σ × π that did not produce enforcement equilibria." L=1, S=0, A=1 (peer accountability in Quaker meetings is real but not punitive), C=1 (decentralized reform networks), E=0 (free entry/exit). Predicted: QUIET. Observed: also QUIET (in the ABM's enforcement-output sense — abolitionism mobilized, but it didn't *enforce orthodoxy on members through punishment*).
- **Critical:** the score `predicted = QUIET, observed = QUIET, regime_match = true` is a **type-of-match that doesn't actually validate the framework** — it's the boring null. The interesting question (does the ABM correctly identify restraint regimes as low-σ × low-π) is answered yes, but the case's rival-mobilization aspect is invisible to the ABM.
- **Confidence:** high on the prediction; the open question is whether including this case is methodologically honest given the ABM's limitations.

### LR012 — Quaker anti-slavery practice (RESTRAINT)

- **Regime_unit:** "Quaker (Religious Society of Friends) abolitionist organizing tradition, 1758–1865, Atlantic world."
- Same disposition as LR011. Maps almost exactly to S1 Text Table 5 "Quaker meeting, contemporary US" row (1, 0, 0, 0, 0 → Quiet).
- **Proposed:** L=1, S=0, A=0, C=0, E=0. Predicted: QUIET.
- **Confidence:** high.

### LR013 — Liberation theology (RESTRAINT)

- **Regime_unit:** "Latin American Catholic + Protestant liberation-theology movement, ~1968 (Medellín CELAM) – ~1990, base communities and theological networks."
- Restraint case, same disposition.
- **Proposed:** L=1, S=1, A=1 (some peer discipline within base communities), C=1, E=1. Predicted: QUIET.
- **Confidence:** medium. Liberation theology is more institutionally embedded than Quaker meetings, so dimensions might be slightly higher.
- **Note:** R is 2 in Nitrogen, not 3 — the restraint is less full-throated than Quaker. Doesn't change ABM scoring much.

### LR014 — Modern universalist / softening interpretations (RESTRAINT)

- **Regime_unit:** "Late-20th-century mainstream Christian softening (post-Vatican II Catholic + liberal Protestant), ~1965–present, global North."
- Restraint case. `text_role_assessment = legitimating` — note that *softened* readings are legitimating non-coercive practice.
- **Proposed:** L=1, S=1, A=0, C=1, E=0. Predicted: QUIET (with slow attrition — closer to S1 Text "Mainline Protestantism" row 2,2,1,1,0 → Collapse, but the Nitrogen evidence is positioning this as restraint, not collapse).
- **Confidence:** medium. **Open question:** is "modern universalist Christianity" experiencing collapse (population departing because the system is too lax to retain) or quiet (low enforcement = no incentive to leave)? Nitrogen frames as restraint (intentional softening); empirically, mainline Protestant decline looks like collapse. **The two framings predict different ABM regimes.** Flag.

### LR015 — Canadian Indian Residential Schools

- **Regime_unit:** "Canadian Indian Residential School system, 1880s–1996, federal government + Catholic + Anglican + United + Presbyterian church partnership."
- **Flagship case.** `evidence_quality = 5`, 9 deep-dive evidence rows, full TRC documentation, Vatican + Anglican apologies attached.
- **Proposed:** L=4, S=4, A=4 (compulsory attendance from 1920; corporal punishment routinized; language suppression enforced), C=4 (federal Indian Affairs administrative apparatus unified the system across denominations), E=4 (children physically removed; legal compulsion; geographic isolation).
- Predicted: CAPTURE. Score profile maps exactly to CCP / Stalinist / Iranian morality police rows in S1 Text Table 5 (4,4,4,4,4 / 4,4,4,4,4 / 4,3,4,4,3).
- **Confidence:** high across all dimensions.
- **Important methodological note:** the residential school *system itself* was a regime that captured Indigenous *children* — a non-consenting population that did not "join" by choice. The ABM models voluntary-membership communities (with exit). This is a structural mismatch — the system was *imposed* on a target population, not chosen. The "exit cost" is meaningful in a different way (children physically prevented from going home), and the regime didn't need to manage internal dissent because residents had no rights. **This will be a paragraph in `mismatches_report.md` even if the prediction matches the observation.**

### LR016 — U.S. Native American boarding schools / Carlisle model

- **Regime_unit:** "U.S. federal Indian boarding school system, 1879 (Carlisle founding) – ~1934 (Indian Reorganization Act), Christian (Protestant + Catholic) mission partnership with federal Bureau of Indian Affairs."
- Mirrors LR015 closely. Same 4,4,4,4,4 profile.
- **Proposed:** L=4, S=4, A=4, C=3 (BIA was less monolithic than Indian Affairs Canada — also some boarding schools were federal-only without church partnership), E=4. Predicted: CAPTURE.
- **Confidence:** high. evidence_quality=4, plausible (not yet `documented` like LR015).
- **Methodology terminology note from `methodology_locked.md`:** The Pratt phrase "Kill the Indian in him, and save the man" is U.S. Carlisle, not Canadian residential schools. The assimilationist *logic* is shared, the *phrase* is not. I'll respect that in scoring rationales.

---

## 3 — Open questions I want resolved before final scoring

These are decisions that change the structure of the deliverables, not just per-case numbers. Phase S1 should not silently absorb them.

**Q1.** **LR007 disposition.** Decline as un-scoreable (my recommendation), or pick a narrowest-defensible sub-regime? If the latter, which? Most defensible sub-instances:
- "Jesuit reductions in Spanish Paraguay, 1609–1767" (well-documented, single denomination, single colonial state, defined institutional form)
- "Protestant Church Mission Society stations in colonial India, ~1813–1947" (also well-documented, single-denominational, defined)
- Either would add a case Nitrogen did not specifically score. Decline is methodologically safer.

**Q2.** **LR009 vs. LR002/LR003/LR004 overlap.** Score LR009 as the medieval Roman Inquisition (1231–1542) only, to avoid double-counting? Or score LR009 as a higher-level abstract pattern at the cost of conceptual incoherence?

**Q3.** **LR005 (Doctrine of Discovery) — what's the regime?** The Christian-colonial regime *as it operated on its own clergy/colonizers* (scoreable on ABM dimensions but loses the case's actual content), or the regime *as it operated on Indigenous targets* (the substantively important question, but the targets aren't members of the regime in the ABM sense)? My proposal scores the former and flags the latter.

**Q4.** **LR014 (modern softening) — quiet or collapse?** Nitrogen frames as restraint (R=3, intentional softening). Empirically, mainline Protestant retention is poor — closer to "collapse (slow attrition)" in S1 Text Table 5. Predicting QUIET says low enforcement = no exit pressure = stable. Predicting COLLAPSE says low retention = population draining. The case gets a different `regime_match` flag depending. Which framing?

**Q5.** **Restraint cases (LR011–LR014) — what does it mean for `regime_match` to be `true`?** All four will likely score as predicted=QUIET, observed=QUIET. That's a true match in the formal sense, but the ABM is matching a *boring null*: it correctly identifies low-σ × low-π regimes as quiet. The case's substantive content (rival mobilization on shared canon) is invisible. Per synthesis Q4 option (b), include them anyway. Confirm?

**Q6.** **LR015/LR016 (residential / boarding schools) — captive populations.** The ABM models voluntary-membership systems with exit. Residential schools imposed membership on minors who could not exit. Score the system's regime geometry on the standard rubric (which is what Nitrogen evidence supports), but flag this in `mismatches_report.md` as a **structural mismatch between the case and the model** even though `regime_match = true` numerically. Confirm this is the right disposition?

**Q7.** **Manuscript revision divergence (V3 paste vs. PLOS submission).** I'm scoring against the PLOS submission (canonical). The V3 paste's §3.3 explicitly enumerates four regimes including QUIET (the PLOS submission lists only three in §3.3 prose, though §6.10 classification has all four). For predicted-regime labels I'll use the four-regime ABM classification scheme from §6.10/§8 (which is universal across versions). Should be a non-issue. Confirm?

---

## 4 — Estimated coverage after dispositions

If I proceed as proposed:
- **Scored normally:** 15 of 16 cases (LR001–LR006, LR008–LR016).
- **Declined:** 1 case (LR007).
- **Restraint cases scored but flagged:** 4 (LR011–LR014).
- **Captive-population cases flagged in mismatches report:** 2 (LR015, LR016).

Predicted regime distribution from proposed scores (rough):
- Quiet: 4 (LR011, LR012, LR013, LR014)
- Mixed: 6 (LR001, LR002, LR006, LR008, LR009, LR010) — possibly more
- Collapse: 0–1 (LR014 if reframed)
- Capture: 4 (LR003, LR004, LR015, LR016) — possibly LR005, LR009 if scored higher
- Declined: 1 (LR007)

If observed regimes track predicted, regime_match rate ≈ 13–15 / 15 scored cases. **A high match rate at this stage would be suspicious** — the ABM should not be able to predict 15/15 from a 5-parameter rubric without confirmation bias. I will double-check my scoring before declaring matches, especially for LR011–LR014 (where the match is the boring null) and LR015–LR016 (where the match conceals a structural mismatch).

---

## 5 — What happens after this dry-run is approved

1. I produce `unified_cases.jsonl` (16 lines, JSON-per-case) per the schema in `INSTRUCTION_BORON_S1.md` §"unified_cases.jsonl".
2. I produce `regime_predictions_summary.csv` (flat tabular).
3. I produce `mismatches_report.md` (per-case diagnoses for any `regime_match=false`).
4. I produce `synthesis_findings.md` (~5–10 pages addressing seven questions including the active-rate discrepancy).
5. I produce `unified_christian_baseline_v1.csv` (CSV serialization of the JSONL).
6. I produce `MANIFEST.md`.
7. I append a Q&A entry to repo-root `HISTORY.md` per CLAUDE.md convention.
8. I update `.gitignore` with `!synthesis/**` if you want this committed (TBD per Hard Rule 3).

Estimate: 4–6 hours of focused scoring + writing once Q1–Q7 above are answered.

---

*End of dry-run. Awaiting decisions on Q1–Q7 before producing final deliverables.*
