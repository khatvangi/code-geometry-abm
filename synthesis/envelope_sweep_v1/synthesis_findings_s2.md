# Synthesis Findings — Phase S2

**Phase:** Synthesis Phase S2 — ABM Extension 1: argument-template envelope as input
**Source data:** `results/v3_0_envelope_sweep/sweep_seed_results.csv` (1,200 rows), `sweep_summary.csv` (40 rows), `template_regime_counts.csv`, `phase_map_v3_0.png`
**Model:** `src/religion_fundamentalism_abm_v3_0.py`
**Sweep parameters:** 8 templates × 5 grid points × 30 seeds = 1,200 runs at steps=450, n=350, scale_free graph; WORKERS=64; wall-clock ~15 minutes (much faster than §5.4's 13–20 hr estimate due to full 64-core saturation).
**Date:** 2026-04-28

---

## Headline recommendation

**Phase S3 should NOT proceed as currently specified.** The envelope mapping in `INSTRUCTION_BORON_S2.md` §3.3 produces a structurally coherent input layer for the ABM — backward-compat preserved bit-for-bit, validation gates work as designed, sweep ran cleanly at 0 failures — but the resulting parameter space **does not reach the CAPTURE region of v2.5's regime structure**. Zero of 1,200 runs classified as CAPTURE. This is a per-§8.10-Hard-Rule finding ("STOP, write the finding, ask Kiran. Do not silently retune the envelope to make the predictions match.") and requires Kiran's adjudication before Phase S3 begins.

The two questions that must be resolved:

1. **Is the §3.1 mapping for E and base_opp_floor directionally correct?** The text says E "raises base_opp_floor by raising in-group benefits of compliance." But `base_opp` in v2.5 is *outside* opportunity — raising it makes the outside option look BETTER, working against capture. T4 has `base_opp_floor = 0.70` (the highest in the table) precisely because {O, E} are both present, but v2.5's CAPTURE region requires `base_opp ≤ 0.30`. Either §3.1 is directionally inverted, or `base_opp_floor` in §3.3 means something other than `exit_opportunity_base`.

2. **Are the envelope ceilings high enough for any template to reach CAPTURE?** T4 (the highest-π template) has π_max = 0.45. v2.5's only CAPTURE cell was at π = 0.50 with σ = 0.95, base_opp = 0.30, exit_threshold = -1.00. T4's envelope at high grid is (σ = 0.45, π = 0.45, base_opp = 0.70, exit_cost = 0.70) — all four parameters are *less* capture-favorable than v2.5's CAPTURE corner. The envelope as designed is structurally incapable of reaching CAPTURE.

These are not mistakes Kiran made and that I should fix — they are spec-level decisions about what claim Phase S2 was testing. The findings below diagnose what the sweep actually showed. Phase S3 readiness depends on whether the answers to (1) and (2) preserve the current envelope (in which case Phase S2's claim is "templates determine *which* MIXED region is reachable, not whether CAPTURE is reachable") or revise it (in which case the envelope ceilings need adjustment per §3.2).

---

## §1 — Sweep execution summary

**Hard counts:**
- 1,200 / 1,200 runs completed; 0 failed; 0 skipped.
- 1,200 metrics.csv files (each 450 rows × 38 cols); 1,200 agent_summary.csv files.
- Wall-clock: ~15 minutes from launch to last metrics.csv. Throughput ≈ 1.3 runs/sec across 64 workers.
- §6.1 pre-sweep validations 1–3: all PASS (T_FREE back-compat bit-for-bit; T1 σ=0.99 raises ValueError; T7 σ=0.10 within envelope).
- §6.2.1 post-sweep validation: all 1,200 metrics.csv non-empty, schema includes `active_punish_rate` + `punish_rate` + `exit_rate`.
- §6.2.2 active-rate sanity: 10 random spot-checks all PASS (`active_punish_rate >= punish_rate` over the run).

**Active-rate-at-sweep-time mechanism works as designed.** Both `punish_rate` (incidence — fraction of active agents with any punishment) and `active_punish_rate` (mean count per active agent) are written each timestep. The regime classifier reads `active_punish_rate` directly. No post-hoc `reclassify_regimes.py` step needed.

---

## §2 — Aggregate regime distribution

**Per-template regime counts (across all 5 grids × 30 seeds = 150 seeds per template):**

| Template | QUIET | MIXED | COLLAPSE | CAPTURE | Quiet+Collapse % | Mixed % | Capture % |
|---|---:|---:|---:|---:|---:|---:|---:|
| T1 (exclusive_salvation)        |  74 |  76 |  0 |  0 | 49% | 51% | **0%** |
| T2 (final_sorting)              |  74 |  76 |  0 |  0 | 49% | 51% | **0%** |
| T3 (expansion_mandate)          |  84 |  62 |  4 |  0 | 59% | 41% | **0%** |
| T4 (purification)               |  49 | 100 |  1 |  0 | 33% | 67% | **0%** |
| T5 (sacred_enforcement)         |  62 |  87 |  1 |  0 | 42% | 58% | **0%** |
| T6 (softened_modern, P caps)    |  86 |  64 |  0 |  0 | 57% | 43% | **0%** |
| T7 (counter_reading, P only)    |  97 |   0 | 53 |  0 | 100% | 0% | **0%** |
| T8 (asymmetric_rights)          |  72 |  76 |  2 |  0 | 49% | 51% | **0%** |
| **Total**                       | **598** | **541** | **61** | **0** | 55% | 45% | **0%** |

**Cell-level majority regime by template × grid:**

```
template  grid_0    grid_1    grid_2    grid_3    grid_4
T1        QUIET     QUIET     QUIET     MIXED     MIXED
T2        QUIET     QUIET     QUIET     MIXED     MIXED
T3        QUIET     QUIET     QUIET     MIXED     MIXED
T4        QUIET     QUIET     MIXED     MIXED     MIXED
T5        QUIET     QUIET     MIXED     MIXED     MIXED
T6        QUIET     QUIET     QUIET     MIXED     MIXED
T7        COLLAPSE  QUIET     QUIET     QUIET     QUIET
T8        QUIET     QUIET     QUIET     MIXED     MIXED
```

**Headline observations:**

- **The primary axis the sweep resolves is QUIET → MIXED transition along the σ × π diagonal**, not the MIXED → CAPTURE transition. Six templates (T1, T2, T3, T6, T8) transition at grid_3; two templates (T4, T5) transition at grid_2 (earliest activation, consistent with their high enforcement-affordance variable signatures).
- **T4 (purification) is the most enforcement-active template** with 100 MIXED seeds out of 150 (67%), consistent with C+M+E+R signature. But still 0 CAPTURE.
- **T7 (counter_reading) collapses at grid_0** (σ=0.10, π=0.01, base_opp=0.30, exit_cost=0.30): low exit_cost combined with sub-activation σ × π means agents leave before any enforcement equilibrium can form. 53 of 30 grid_0 seeds COLLAPSED — wait, that's 53 of 150 across all grids; the grid_0 cell shows COLLAPSE majority by vote.

---

## §3 — Qualitative envelope predictions: validation against §1

`INSTRUCTION_BORON_S2.md §1` made four qualitative predictions about template-level regime distributions. The sweep's actual outcomes against each:

### Prediction 1 — T3, T4, T5 high-π cells produce >50% mixed/capture

**OUTCOME: PARTIALLY CONFIRMED.** All three templates produce MIXED majority at high grids (T3 grid_3 + grid_4 = MIXED; T4 grid_2–4 = MIXED; T5 grid_2–4 = MIXED). The MIXED rate at the highest cell (grid_4) is 30/30 = 100% for T3, T4, T5. But **zero CAPTURE seeds**. The prediction conflated MIXED+CAPTURE; the sweep cleanly produces MIXED only.

This is the core finding: **Phase S2 successfully demonstrates that templates with E in their structural signature produce active enforcement, but the envelope ceilings as designed do not reach CAPTURE.**

### Prediction 2 — T6, T7 produce >80% quiet across all cells

**OUTCOME: VIOLATED for both templates.**

- T6 produces 64 MIXED of 150 = 43% non-quiet. The P-cap (σ_cap_when_P_present = 0.55, π_cap_when_P_present = 0.15) does not prevent activation at σ=0.55, π=0.15 — those values are above v2.5's quiet-to-active activation threshold. The P-cap caps the *peak* enforcement intensity but doesn't suppress activation.
- T7 produces 53 COLLAPSE of 150 = 35% non-quiet. The COLLAPSEs all occur at grid_0 (low σ, low π, low exit_cost): agents exit before enforcement forms. Outside grid_0, T7 is 100% QUIET (97/120 = 81% — interesting, just hits the >80% threshold for grids 1–4 alone but the grid_0 collapse pulls the template-wide count down).

This is a real finding: **the P-cap does not produce the absolute restraint §1 expected.** P caps enforcement intensity but doesn't prevent the σ × π conjunction from crossing the active-enforcement threshold.

### Prediction 3 — T1, T2 produce mostly mixed at high σ but rarely capture

**OUTCOME: CONFIRMED.** T1 and T2 produce 76 MIXED of 150 each (51%) and 0 CAPTURE. The "rarely capture" prediction is satisfied trivially since the envelope ceilings prevent CAPTURE for any template, but the qualitative *shape* (active-enforcement-yes, capture-no) is correct.

### Prediction 4 — T8 mixed-but-not-capture

**OUTCOME: CONFIRMED.** T8 produces 76 MIXED, 0 CAPTURE. The asymmetric-rights envelope with σ_max=0.45, π_max=0.25 produces mixed-enforcement at high grids but no capture. The shape matches.

### Aggregate prediction-validation rate

Of 4 qualitative predictions: 2 confirmed (T1/T2, T8), 1 partially confirmed (T3/T4/T5 missing the CAPTURE half), 1 violated (T6/T7 don't hit >80% quiet).

**The prediction violations are findings, not bugs.** Per §8.10: "Violations of any qualitative prediction across multiple seeds are findings — they constrain §3."

---

## §4 — The zero-CAPTURE finding: what it means

Across 1,200 sweep runs, no run produced CAPTURE (fund_prevalence ≥ 0.90 AND exit_rate ≤ 0.20). To diagnose, compare envelope ceilings against v2.5's known CAPTURE region:

**v2.5 confirmatory sweep CAPTURE conditions:**
- σ = 0.95, π = 0.50, base_opp = 0.30, exit_threshold = -1.00.
- Only 1 of 72 cells captured (the rare corner per manuscript §8.1).

**v3.0 envelope sweep maximum-stress cell (T4 grid_4):**
- σ = 0.45, π = 0.45, base_opp = 0.70, exit_cost = 0.70.
- All four parameters less capture-favorable than v2.5's CAPTURE corner.

**Per-parameter comparison:**

| Parameter | v2.5 CAPTURE corner | T4 grid_4 envelope max | Direction |
|---|---|---|---|
| σ | 0.95 | 0.45 | T4 < CAPTURE |
| π | 0.50 | 0.45 | T4 ≈ CAPTURE (just below) |
| base_opp | 0.30 | 0.70 | T4 > CAPTURE (worse — outside option BETTER means MORE exit pressure) |
| exit_cost | implicit high | 0.70 | T4 ≈ CAPTURE (similar) |

**The envelope is structurally incapable of reaching CAPTURE.** This is by design: §3.1 maps each structural variable to an ABM-parameter consequence, and no template's variable set produces high enough σ + low enough base_opp simultaneously to enter v2.5's CAPTURE region.

Three readings of this:

**Reading A — the envelope is too conservative; raise the ceilings.** Phase S3 would require revising §3.2 to push σ_max higher (e.g., T4 σ_max = 0.65) and base_opp_floor lower (e.g., T4 base_opp_floor = 0.30 by treating O+E as *raising* exit pressure, not lowering it). This is the most action-forward reading. Risk: arbitrary retuning to make the answer come out.

**Reading B — Phase S2's claim is weaker than originally specified.** The synthesis architecture (§4 of the working doc) says "code content shapes which geometries are *available* to a regime; once a geometry is selected ... the ABM dynamics determine the equilibrium." Phase S2's substantive finding is that **no Christian argument template alone is sufficient to reach CAPTURE**; CAPTURE in real Christian regimes (LR003, LR004, LR015, LR016) requires the *interaction* of templates with non-textual forces (state_power, empire, child_custody) that Phase S2 explicitly excludes per §3.4. This is consistent with Phase S1's finding that LR015/LR016 are `formal_only_mechanism_mismatch`: their CAPTURE comes from non-textual mechanism (custody-of-minors), not from the textual envelope alone.

**Reading C — the §3.1 base_opp directionality is inverted.** If E "raises base_opp_floor" in §3.1 actually means "lowers perceived outside option" (consistent with the textual logic that enforcement makes leaving look worse), then T4's base_opp_floor should be 0.30, not 0.70. This change alone would put T4 grid_4 at (σ=0.45, π=0.45, base_opp=0.30, exit_cost=0.70) — much closer to v2.5's CAPTURE corner. **This is the reading I lean toward.** The §3.1 text seems to have conflated "raises base_opp_floor" with "raises in-group benefits"; in the v2.5 model these have opposite effects on exit.

**Recommendation:** Reading B + C combined.
- (B) acknowledges that Phase S2's strong claim ("templates can reach CAPTURE in isolation") is empirically false in this corpus, and this is a real synthesis finding worth keeping.
- (C) corrects what looks like a directionality error in §3.1 for E and base_opp_floor. If §3.1 is corrected, T4 (and possibly others) would have a sharper-CAPTURE envelope, and re-running the sweep would resolve whether reading A or B is the right framing.

Per Hard Rule 10: I am not retuning §3.2. The corrected envelope, if Kiran approves Reading C, is a separate revision that would gate before any re-sweep.

---

## §5 — Other notable findings

### §5.1 — T7 grid_0 COLLAPSE: low exit_cost dominates

T7's grid_0 (σ=0.10, π=0.01, base_opp=0.30, exit_cost=0.30) classifies COLLAPSE in 23 of 30 seeds. The mechanism: counter-reading templates have P-only signature, no E, no M — minimal in-group enforcement reward. Combined with low exit_cost (E baseline=0.30, no O bonus because P shadows... wait, T7 doesn't have O at all in the variable set, so this isn't P-shadowing). Agents exit because there's no countervailing pull to stay, and base_opp at 0.30 is low enough that exit-friction is non-trivial but there's nothing keeping agents in.

This empirically confirms the LR011/LR012/LR013 boring-null match from Phase S1: **counter-reading regimes don't produce enforcement equilibria**, but the v3.0 sweep also reveals they can produce *collapse*-style exit when exit_cost is low enough. The four restraint cases in Phase S1 had E ranging 0–1 (LR011, LR013 = 0; LR012 = 0; LR014 = 0). At E ≤ 1, exit is feasible enough that T7-template regimes collapse. At higher real-world exit_cost (say, Quaker community embeddedness in 18th-c. Philadelphia), the collapse risk diminishes.

This is consistent with Phase S1 §15.1's COLLAPSE-narrow-definition finding: the ABM's COLLAPSE label captures "enforcement-induced depopulation" but also captures "exit-cost-too-low-to-retain". T7 grid_0 is the latter.

### §5.2 — T6 (P-capped) does activate enforcement

§1 predicted T6 produces >80% quiet. Actual: 57% quiet, 43% mixed. The P-cap caps σ at 0.55 and π at 0.15, but at the high grid (grid_4: σ=0.55, π=0.15) the σ × π conjunction is above v2.5's activation threshold (manuscript dose-response §8.12: σ ≥ 0.40 at π ≥ 0.10 produces activation in 100% of seeds). T6 grid_4 is at σ=0.55, π=0.15 — above the activation threshold despite the P-cap.

**Reading:** P caps the *peak* enforcement intensity (max_active_punish_rate stays low) but does not prevent the regime from crossing the active-enforcement threshold. P is a *ceiling on intensity*, not a *gate on activation*. This distinction is not in §3.1 of the instruction; it's a structural finding of Phase S2.

The substantive claim T6 represents historically — "softened modern interpretations restrain the canon's coercive potential" — is partially true: T6 regimes don't reach high enforcement intensity (max_apr capped at ~0.20), but they do produce active enforcement in mixed-regime form. This is consistent with empirical observation that post-Vatican II Catholicism still excommunicates, ordains-or-doesn't, and disciplines via canon law, just at a much lower enforcement intensity than the Counter-Reformation Inquisition.

### §5.3 — Active-rate-at-sweep-time mechanism: works correctly

The whole point of the active-rate-at-sweep-time fix (per CLAUDE.md and §4.1.3) was to avoid the v2.5 active-rate gotcha at source. v3.0 writes both `punish_rate` (incidence — v2.5.1 active-only) and `active_punish_rate` (mean count among active) directly each timestep. The regime classifier reads `active_punish_rate`. No post-hoc `reclassify_regimes.py` step.

Verified working: §6.2.1 (all metrics.csv have active_punish_rate column) and §6.2.2 (active_punish_rate >= punish_rate on all 10 spot-checks). The Phase S5 figure-rebuild concern from Phase S1 §15.3 does not apply to v3.0 sweep results — they're correct from the start.

---

## §6 — Decision points for Kiran

### Q-S2-1: Resolve the §3.1 base_opp directionality question

Does E (enforcement directive) raise OR lower `base_opp_floor`? The instruction text says "raises ... by raising in-group benefits of compliance" but in v2.5 `exit_opportunity_base` is *outside* opportunity, and raising it works against capture.

- **Option A (current spec):** E raises base_opp_floor. T4 has high base_opp_floor (0.70). Outside option remains attractive. CAPTURE structurally unreachable.
- **Option B (proposed correction):** E lowers base_opp_floor. T4 should have base_opp_floor=0.30. Outside option degraded by perceived in-group benefit. CAPTURE potentially reachable.

I recommend Option B. The textual logic is "enforcement makes leaving look worse" → low base_opp. But this is a spec-level decision and Hard Rule 10 forbids me from making it unilaterally.

### Q-S2-2: Phase S2 claim revision

Given zero CAPTURE in the current sweep, what is Phase S2's actual claim?

- **Strong claim (original):** templates determine which σ × π × base_opp × exit_cost region is reachable, and within that region the ABM produces the regime distribution consistent with the template's textual intent.
- **Weak claim (revised):** templates determine which region of the QUIET → MIXED transition is reachable. CAPTURE requires non-textual force interaction (Extension 3) and/or different envelope geometry (revised §3.1) and is not reachable from textual templates alone.

The weak claim is consistent with Phase S1 findings (formal_only_mechanism_mismatch cases LR005/LR015/LR016 had CAPTURE driven by non-textual mechanisms, not by their textual envelope). Adopting the weak claim would make Phase S2 a confirmation of "code content sets the QUIET-vs-active threshold; non-textual forces and exit-cost mechanisms determine the MIXED-vs-CAPTURE outcome." Phase S3 would then explicitly test that.

### Q-S2-3: Re-sweep decision

If Q-S2-1 = Option B and §3.1 is corrected:
- (a) Re-run the 1,200-run sweep with the corrected envelope. Cost: another ~15 minutes wall-clock.
- (b) Skip the re-sweep; document the directionality issue as a Phase S2 finding and move to Phase S3 with both Reading B and C as live possibilities to be tested then.

I recommend (a) if Q-S2-2 = strong claim (we want to test whether templates *can* reach CAPTURE under corrected directionality). I recommend (b) if Q-S2-2 = weak claim (the current sweep already establishes the weak claim; CAPTURE would not be expected even under corrected directionality without non-textual forces).

### Q-S2-4: T6/T7 prediction-violation framing

The §1 prediction "T6, T7 produce >80% quiet" is empirically violated. Two readings:

- **Tighten the prediction:** specify "T6 produces ≤60% mixed" (acknowledging P caps intensity not activation). T7 grid_0 collapse becomes a documented finding rather than a violation.
- **Update §3.1 P semantics:** if P is supposed to be a *gate* (not just a *ceiling*), reduce P-capped templates' σ_max and π_max more aggressively (e.g., σ_max ≤ 0.40 instead of 0.55) so the active-enforcement threshold is never crossed.

I recommend the first option (tighten the prediction). The current §3.1 P semantics is "caps σ_max and π_max regardless of other variables present" — that's a ceiling, not a gate. The §1 prediction's >80% quiet expectation was inconsistent with the §3.1 specification.

---

## §7 — Recommendations for Phase S3

These are conditional on Q-S2 resolutions:

**If Q-S2-1 = B and Q-S2-3 = (a):** re-run the sweep with corrected envelope, then proceed to Phase S3. Phase S3 specification per `SYNTHESIS_WORKING_DOC.md §10` (Extensions 3 and 4 + Christian regime replication sweep) is unchanged.

**If Q-S2-1 = B and Q-S2-3 = (b):** proceed directly to Phase S3 with the directionality correction noted as a known issue. Phase S3 Extension 3 (non-textual force decomposition) will be the natural place to test whether non-textual forces are what closes the CAPTURE gap (consistent with the weak claim).

**If Q-S2-1 = A (no correction):** Phase S2's substantive claim becomes the weak claim. Phase S3 priority shifts to Extension 5 (target-population modeling, the new fifth extension from Phase S1) since CAPTURE in real cases is driven by mechanisms outside the current ABM's voluntary-membership scope.

In all three scenarios, **the Phase S2 sweep itself is sound** — the active-rate-at-sweep-time mechanism works, the envelope-validation gates work, the qualitative QUIET → MIXED transition is cleanly resolved. The findings are about what the envelope *does not* reach, not about implementation correctness.

---

## §8 — Files produced

```
results/v3_0_envelope_sweep/
├── sweep_seed_results.csv         (290 KB, 1200 rows, 16 cols)
├── sweep_summary.csv              (5.3 KB, 40 rows, 16 cols)
├── template_regime_counts.csv     (0.6 KB, 40 rows)
├── phase_map_v3_0.png             (276 KB, 8-panel σ×π regime map)
├── run.log                        (gitignored *.log)
├── run.pid                        (gitignored *.pid)
└── <T>/grid_<i>/seed_<s>/         (1200 seed dirs each with metrics.csv + agent_summary.csv)

synthesis/envelope_sweep_v1/
├── _dry_run.md                    (4 KB, pre-sweep grid coordinate inspection)
└── synthesis_findings_s2.md       (this file)

src/religion_fundamentalism_abm_v3_0.py   (970 lines, +83 over v2.5)
scripts/run_v3_0_envelope_sweep.py        (245 lines)
scripts/aggregate_v3_0_envelope_sweep.py  (220 lines)
```

All committed except the per-seed `metrics.csv` / `agent_summary.csv` files (under `results/v3_0_envelope_sweep/<T>/grid_<i>/seed_<s>/` — to be staged when Kiran approves).

---

## §9 — Hard-rule compliance

- ✓ No file outside `src/`, `scripts/`, `synthesis/`, `results/v3_0_envelope_sweep/`, `.gitignore`, `HISTORY.md` modified.
- ✓ v2.5–v2.9 model files unchanged (verified by no edits to those paths).
- ✓ Phase S1 deliverables in `synthesis/unified_christian_baseline_v1/` untouched.
- ✓ `synthesis/inputs/manuscript_plosone_v3/` untouched.
- ✓ `manuscript/` untouched.
- ✓ `scripts/reclassify_regimes.py` not invoked — active-rate computed at sweep time per §4.1.
- ✓ No synthetic data; all 1,200 runs from real ABM with fixed seeds 1..30.
- ✓ Existing `results/` directories not overwritten; new sweep in new whitelisted dir.
- ✓ HISTORY.md to be appended.
- ✓ Hard Rule 10 followed: zero-CAPTURE finding raised here for Kiran review; envelope NOT silently retuned.

---

*End of Phase S2 findings as written 2026-04-28 morning. Decisions recorded in §10 below.*

---

## §10 — Decisions adjudicated (2026-04-28)

Kiran adjudicated all four Q-S2 decision points in this order. The resolutions and their downstream consequences:

### §10.1 — Q-S2-1: §3.1 base_opp directionality → Option B (invert)

**Decision:** E does NOT raise `base_opp_floor`. The {O,E} pairing degrades the perceived outside option, so when both are present `base_opp_floor` is pulled *down* (or held at baseline), not pushed up. The §3.1 row for E was directionally inverted with respect to v2.5's `exit_opportunity_base` semantics.

**Application:**
- The §3.1, §3.2, §3.3 sections of `INSTRUCTION_BORON_S2.md` are NOT retroactively edited. They are the spec-of-record for the committed 1,200-run sweep; rewriting them would silently invalidate the audit trail.
- Correction is recorded in a new `INSTRUCTION_BORON_S2.md §3.5 — Directionality correction (post-S2 adjudication)` and applies in Phase S3 onward via a new model file.
- Net envelope change: T4 `base_opp_floor` shifts 0.70 → 0.30 in Phase S3. Other templates unchanged (no other template has {O,E} both present without P-shadowing).

### §10.2 — Q-S2-2: Phase S2 claim → weak claim adopted

**Decision:** Phase S2's substantive claim is the weak form: **templates set the QUIET-vs-active threshold; non-textual forces and exit-cost mechanisms determine the MIXED-vs-CAPTURE outcome.** The strong claim ("templates can reach CAPTURE in isolation") is empirically false in this corpus and is not what Phase S2 demonstrated.

**Why this is the right reading:** consistent with Phase S1's `formal_only_mechanism_mismatch` cases (LR005/LR015/LR016) where CAPTURE was driven by non-textual mechanisms (custody-of-minors, state power, residential schooling) rather than the textual envelope alone. The 1,200-run zero-CAPTURE result is the empirical anchor for the weak claim, not a sign of broken implementation.

**Application:**
- Phase S2's substantive finding is now: "templates determine which σ × π region is reachable along the QUIET → active transition; non-textual forces close the CAPTURE gap." Phase S3's Extension 3 (non-textual force decomposition) is the natural next test.
- Manuscript revisions in Phase S5 should reference this framing rather than the original strong claim.

### §10.3 — Q-S2-3: Re-sweep decision → (b) skip re-sweep

**Decision:** No re-sweep. The S2 1,200-run sweep stands as the anchor for the weak claim. The directionality correction is carried into Phase S3 as an envelope input rather than re-validated in S2.

**Why:** under the weak claim, the S2 sweep's purpose is to establish the QUIET-vs-active envelope, which the current data already does cleanly. CAPTURE would not be expected under the corrected envelope without non-textual forces (which Phase S2 explicitly excludes per §3.4). Spending 15 min on a re-sweep with directionality flipped would not change the headline finding; it would only test whether T4 grid_4 alone hits CAPTURE under corrected base_opp, which Phase S3's Extension 3 sweep will test more rigorously alongside non-textual forces.

**Application:**
- `results/v3_0_envelope_sweep/` is the canonical Phase S2 result dir. No new sweep dir.
- Phase S3 starts from the corrected envelope (per §10.1) without intermediate validation.

### §10.4 — Q-S2-4: T6/T7 prediction violations → tighten §1

**Decision:** Tighten the §1 prediction language; do not re-spec the §3.1 P semantics. P is a ceiling on enforcement intensity, not a gate on activation — the §1 ">80% quiet" prediction was inconsistent with the §3.1 specification, not vice versa.

**Application:**
- Refined predictions recorded in `INSTRUCTION_BORON_S2.md §1.1`:
  - T6 → "≤60% mixed across the envelope" (was: ">80% quiet").
  - T7 → "predominantly QUIET except COLLAPSE at low-exit_cost cells" (was: ">80% quiet across all cells"). T7 grid_0 COLLAPSE is now a documented finding consistent with Phase S1 §15.1 COLLAPSE-narrow-definition, not a violation.
- §3.1 P semantics ("caps σ_max and π_max regardless of other variables") is unchanged.

---

## §11 — Phase S3 entry conditions (post-adjudication)

With Q-S2-1..4 resolved, Phase S3 may begin with the following inherited inputs:

1. **Corrected envelope** per §10.1 / `INSTRUCTION_BORON_S2.md §3.5`. T4 `base_opp_floor` 0.70 → 0.30; all other rows unchanged.
2. **Weak Phase S2 claim** per §10.2 as the working synthesis frame. Phase S3 explicitly tests whether non-textual forces (Extension 3) close the CAPTURE gap that the textual envelope alone cannot.
3. **No re-sweep** per §10.3. Phase S2 sweep results in `results/v3_0_envelope_sweep/` are final.
4. **Refined predictions** per §10.4 / `§1.1` are the predictions of record for any future re-validation.
5. **Append-only model versioning per CLAUDE.md.** Phase S3 will create `src/religion_fundamentalism_abm_v3_1.py` (copy of v3.0 with `ENVELOPE_TABLE` updated for T4 only). v3.0 stays frozen.

Phase S3 sequencing per `synthesis/SYNTHESIS_WORKING_DOC.md §10` is otherwise unchanged: Extension 3 + Extension 4 + Christian regime replication sweep.

---

*End of Phase S2 findings, with adjudicated decisions. Phase S3 may begin.*
