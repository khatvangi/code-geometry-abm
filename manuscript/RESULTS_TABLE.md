# RESULTS_TABLE.md — canonical numbers, one source of truth

Every number the manuscript cites is drawn from here, and every row names the
committed CSV it came from. Assembled 2026-07-19. No number in this file is
hand-entered from memory; each was computed from the named file in this session.

**Classifier (finalized):** `CAPTURE = retained (final_exit_rate ≤ 0.20) AND active
(max_punish ≥ 0.10)`. Four operational outcome classes as the cells of a 2×2 over
two structural outcomes (activation × retention), plus COLLAPSE (exit ≥ 0.90) as a
boundary case:

| | not retained | retained |
|---|---|---|
| **not active** | (leaking, dead) → QUIET* | QUIET |
| **active** | MIXED | CAPTURE |

*exit ≥ 0.90 → COLLAPSE. Source of definition: `src/regime_classifier.py`
(self-check passes). `enforcer_share` removed from the gate — see the vacuity
audit below.

Provenance key: **[C]** = committed run (path under repo). **[S]** = generated
this session from the *uncommitted* v3.3 model edits (marked explicitly; needs a
committed rerun before it is a published number).

---

## Classifier-finalization audits (this session)

**Vacuity of the old concentration criterion [C].** Reclassifying all committed
runs with vs without the `enforcer_share ≥ 0.70` gate changed **0 of 9,570**
classifications (factorial_shock_off 4050, exogenous_delta_fixed 1620,
boundary_sealed 1890, boundary_open 1890, ablation ceiling 120). `enforcer_share`
has **no mass near 0** (frac ≤0.05 = 0.000 in every dataset) and median 0.97–0.98;
it saturates high wherever punishment occurs, so it is redundant with activation,
not a graded concentration measure. Sources: the five committed CSVs listed above.

**Activation-threshold sensitivity [C]** (`recon/exogenous_delta_fixed`,
`recon/boundary_sealed`). Capture rate vs `PUNISH_ACTIVE_MIN`:

| threshold | exogenous capture | boundary_sealed capture | δ dose-response | σ=0.25/π=0.05 dead cell |
|---|---|---|---|---|
| 0.05  | 0.253 | 0.816 | monotone | **BREAKS** (90/180 capture) |
| 0.075 | 0.198 | 0.694 | monotone | holds (0/180) |
| **0.10 (canonical)** | **0.198** | **0.661** | **monotone** | **holds (0/180)** |
| 0.15  | 0.186 | 0.473 | monotone | holds (0/180) |
| 0.20  | 0.006 | 0.070 | **degenerates** (~0 everywhere) | holds (0/180) |

Robust band for *both* the dose-response and the necessity result is ≈ **[0.075,
0.15]**; the canonical 0.10 sits in its interior. The loose end (0.05) revives the
dead cell; the strict end (0.20) kills the dose-response. Methods should state this
band explicitly.

**Threshold-dependence of each result.** Results that rest on the 0.10/0.20 cutoffs
are marked **[T]** below; results that are threshold-free (continuous statistics,
role-independent metrics, or machine-precision quantities) are marked **[∞]**. The
threshold-free surfaces underlying the [T] results — mean exit and mean max_punish
over σ×π and over δ — are in **`manuscript/RESULTS_CONTINUOUS.md`**, and the primary
Results should lead with those. In particular the necessity claim has a
threshold-free form: at σ=0.25/π=0.05, mean max_punish = 0.051 at both δ=0.0 and
δ=0.95 (Δ=0.000) — enforcement intensity is flat regardless of exit closure.

**COLLAPSE without enforcement [C].** Across all committed sweeps, every COLLAPSE
run has sub-threshold enforcement:

| dataset | COLLAPSE runs | of which max_punish < 0.10 | max_punish (min/med/max) |
|---|---|---|---|
| `results/v2.5_methodology_paper_canonical` | 45 | **45 (100%)** | 0.037 / 0.063 / 0.094 |
| `results/v2.5_corrected_three_regime_confirm` | 45 | 45 (100%) | 0.037 / 0.063 / 0.094 |
| `results/v2.5_corrected_sweep_regime_search_fast` | 18 | 18 (100%) | 0.037 / 0.059 / 0.094 |
| all `recon/*` sweeps | 0 | — | — |

**Consequence:** COLLAPSE occurs *without activation* — 100% of collapse runs
never crossed the enforcement threshold (max_punish ≤ 0.094). Depopulation here is
driven by open exit, not by enforcement. Describe it as depopulation without
activation; do not attribute it to enforcement.

**Clean 2×2 (drop the separate 0.90 rule) [C].** Reclassifying all committed data
as activation × retention with no COLLAPSE rule changes **108 / 28,581 runs
(0.38%)** — every change is COLLAPSE→QUIET (18 + 45 + 45 inactive runs), since all
collapse runs are inactive. The "gap" cell (inactive, 0.20 < exit < 0.90) is **560
runs (1.96%)**, all already labeled QUIET. **Recommendation: adopt the clean 2×2**
(activation × retention) as the analytical classifier; retain COLLAPSE only as a
descriptive flag for the exit ≥ 0.90 tail within the inactive region, not a
separate dynamical regime.

**Stale-`regime`-column audit [C].** Every block was checked for whether it read a
committed `regime` column (which for the recon sweeps was written with the
**legacy prevalence-gated** schema) instead of recomputing with the canonical
hierarchical `regime_classifier`:

| block | how regimes were derived | defect? |
|---|---|---|
| (a) activation frontier | recomputed from exit + max_punish | clean |
| (b) dose-response | recomputed from exit + max_punish | clean |
| **(c) shock factorial** | **had read stale legacy `regime` column** | **FIXED — 71% wrong (0→2880 CAPTURE)** |
| (d) ablation | role-independent metrics, no regime | clean |
| (e) decoupled-δ | had read stale column; recompute agrees (0%) | recomputed on principle |
| (f) v3.3 | direct from run outputs | clean |
| vacuity / sensitivity / collapse / 2×2 audits | all recomputed via `classify` | clean |

Only (c) was materially wrong: the legacy column's ≥0.90 prevalence gate demoted
2880 genuine (retained ∧ active) CAPTURE runs to MIXED. All regime-bearing blocks
are now recomputed; provenance is stated per block below.

---

## (a) Activation frontier — `recon/boundary_open` & `recon/boundary_sealed` [C] [T]
**Provenance: RECOMPUTED** — P(active)/P(capture) computed directly from `final_exit_rate` + `max_punish` per run, not the `regime` column.
_Threshold-dependent classification; threshold-free surfaces (mean exit, mean max_punish over σ×π) in RESULTS_CONTINUOUS.md._

Both δ-extremes, 9 σ × 7 π × 30 seeds = 1890 runs each.

**Activation (exit OPEN, δ₀=0): P(active) per cell — pure code-geometry frontier.**
Overall active rate 0.598; **capture 0/1890** (nothing retained when exit is open).

```
pi      0.01 0.03 0.05 0.10 0.15 0.25 0.50
sig0.05  0.0 0.00 0.00 0.00 0.00 0.17 0.90
sig0.15  0.0 0.00 0.00 0.00 0.40 0.90 1.00
sig0.25  0.0 0.00 0.00 0.63 0.90 1.00 1.00
sig0.35  0.0 0.00 0.00 0.93 1.00 1.00 1.00
sig0.45  0.0 0.00 0.60 1.00 1.00 1.00 1.00
sig0.55  0.0 0.00 1.00 1.00 1.00 1.00 1.00
sig0.65  0.0 0.27 1.00 1.00 1.00 1.00 1.00
sig0.75  0.0 1.00 1.00 1.00 1.00 1.00 1.00
sig0.95  0.0 1.00 1.00 1.00 1.00 1.00 1.00
```

**Capture (exit SEALED, δ₀=0.95): P(capture) per cell — same frontier, now retained.**
Overall capture rate 0.661 (1249/1890).

```
pi      0.01 0.03 0.05 0.10 0.15 0.25 0.50
sig0.05  0.0 0.00 0.00 0.00 0.00 0.87 1.00
sig0.15  0.0 0.00 0.00 0.13 1.00 1.00 1.00
sig0.25  0.0 0.00 0.00 1.00 1.00 1.00 1.00
sig0.35  0.0 0.00 0.47 1.00 1.00 1.00 1.00
sig0.45  0.0 0.00 1.00 1.00 1.00 1.00 1.00
sig0.55  0.0 0.17 1.00 1.00 1.00 1.00 1.00
sig0.65  0.0 1.00 1.00 1.00 1.00 1.00 1.00
sig0.75  0.0 1.00 1.00 1.00 1.00 1.00 1.00
sig0.95  0.0 1.00 1.00 1.00 1.00 1.00 1.00
```

Reading: the σ×π frontier governs **activation**; sealing exit converts the active
region to **capture** (π=0.01 stays dead; low-σ/low-π stays inactive). This is the
two-axis thesis in one overlay. Source columns: `sigma, pi_reward, final_exit_rate,
max_punish` in each `sweep_seed_results.csv`.

## (b) Exit-capacity dose-response — `recon/exogenous_delta_fixed` [C] [T]
**Provenance: RECOMPUTED** — capture rate computed from `final_exit_rate` + `max_punish` per run, not the `regime` column.
_Capture rates are threshold-dependent; continuous dose surface (mean max_punish, mean exit by δ) and the threshold-free necessity form are in RESULTS_CONTINUOUS.md._

σ∈{0.25,0.75,0.95} × π∈{0.05,0.25,0.50} × δ₀∈{0,0.2,0.4,0.6,0.8,0.95} × 30 seeds.
Capture rate by imposed exit-closure δ₀ (classifier: retained ∧ active):

| δ₀ | 0.0 | 0.2 | 0.4 | 0.6 | 0.8 | 0.95 |
|---|---|---|---|---|---|---|
| capture | 0.000 | 0.000 | 0.000 | 0.011 | 0.285 | 0.889 |

**Necessity cell:** σ=0.25, π=0.05 stays **0 capture at every δ₀ including 0.95**
(0/30 at δ=0.95; 0/180 across the column). Closing the exit cannot manufacture
capture where the code geometry does not activate. Source columns: `delta0, sigma,
pi_reward, final_exit_rate, max_punish`.

## (c) Shock factorial — perfect null — `recon/factorial_shock_off` & `_on` [C] [T]
**Provenance: RECOMPUTED** via `regime_classifier.classify_dataframe`
(`exit_col=final_exit_rate, punish_col=max_punish`, hierarchical). _The committed
`regime` column was **legacy-schema** (prevalence ≥0.90 gate) and disagreed with the
canonical hierarchical classifier on **71% of runs** — see the correction below._

4050 runs each. Recomputed hierarchical regime distribution is **identical** shocks
off vs on (the null holds), but the dataset is **capture-heavy**, not the "no
capture" the stale column implied:

| | QUIET | MIXED | CAPTURE |
|---|---|---|---|
| shock off (recomputed) | 450 | 720 | **2880** |
| shock on (recomputed) | 450 | 720 | **2880** |
| _stale legacy column (both)_ | _450_ | _3600_ | _0_ |

Split by endogenous δ-drift: **drift off (η=0, 810 runs)** → 720 MIXED / 90 QUIET /
0 CAPTURE; **drift on (η>0, 3240 runs)** → 2880 CAPTURE / 360 QUIET / 0 MIXED. So the
endogenous-δ feedback (η>0) closes the exit and converts active systems to CAPTURE,
and **exogenous threat shocks change nothing** (off≡on exactly). The capture runs
have prevalence 0.077–0.140 (why the legacy gate hid them), exit ~0.006, max_punish
~0.17. Source columns: `final_exit_rate, max_punish, eta_delta_drift`.

**Non-orthogonality of the two axes [C, RECOMPUTED].** Sealing the exit
(boundary_open→sealed) raises P(active) in **12 of 63 σ×π cells (never lowers it)**,
all on the frontier margin; overall P(active) 0.598→0.661 (mean cell shift +0.062,
+0.328 among the 12 affected). Retention and activation are separable across most of
the grid (51/63 cells unchanged) but **coupled at the boundary**: closing the exit
retains members *and* nudges marginal cells into activation. Source:
`recon/boundary_open` & `boundary_sealed`, `max_punish` per cell.

## (d) Privilege ablation — role-independent — `recon/privilege_ablation/ablation_seed_results.csv` [C] [∞]
**Provenance: NO REGIME** — role-independent metrics (top5/Gini over active agents) read from the ablation CSV; no regime classification involved.
_Threshold-free: top5/Gini over active agents vs a random null._

Floor (no privilege) vs ceiling (full privilege bundle), 120 runs each, active-only
metrics with a random-allocation null:

| arm | top5_active | gini_active | gini_null (random) | exit_rate |
|---|---|---|---|---|
| floor | 0.091 | 0.240 | 0.028 | 0.585 |
| ceiling | 0.580 | 0.901 | 0.062 | 0.331 |

Privilege-manufactured share of top-5% concentration: (0.580 − 0.091)/0.580 =
**0.843 (84%)**. Concentration is a product of the privilege architecture, not an
emergent property of the floor model (floor Gini 0.240 barely above the 0.028
random null). Source columns: `arm, top5_active, gini_active, gini_null, exit_rate`.

**Single-privilege add-back [C] [∞]** — same CSV, 120 seeds per arm. Recovery is
expressed as a fraction of the floor→ceiling top-5% span (0.0907 → 0.5799):

| arm | top5_active | gini_active | recovers |
|---|---|---|---|
| floor | 0.0907 | 0.2402 | — |
| add_quota | 0.0907 | 0.2402 | 0.0% |
| add_monopoly | 0.0907 | 0.2402 | 0.0% |
| **add_punish_mult** | **0.2505** | **0.6317** | **32.7%** |
| add_backlash_protect | 0.0907 | 0.2402 | 0.0% |
| add_cap_gain | 0.0907 | 0.2402 | 0.0% |
| add_budget_patronage | 0.0907 | 0.2402 | 0.0% |
| add_cost_discount | 0.0907 | 0.2402 | 0.0% |
| ceiling | 0.5799 | 0.9007 | 100% |

**Seven of the eight single privileges are exactly inert** — byte-identical to the
floor to 4 dp. The exception is the **punishment multiplier**, which alone recovers
about a third of the span. The correct statement is therefore *not* "no single
privilege recovers concentration": one does, and the remaining seven are inert
because they act only on a cadre that the quota-less floor never forms. Concentration
is conjunctive **except** for the coercive-power multiplier, which is the single
load-bearing privilege.

**Concentration does not discriminate capture [C] [∞]** —
`recon/exogenous_delta_fixed`, regimes recomputed (hierarchical), active-agent
metrics recomputed from each run's `agent_summary.csv`:

| regime | n | top5_active | gini_active | final_exit_rate |
|---|---|---|---|---|
| CAPTURE | 320 | 0.678 | 0.918 | **0.105** |
| MIXED | 1120 | 0.625 | 0.903 | **0.339** |
| QUIET | 180 | 0.425 | 0.713 | 0.021 |

Among **active** systems (CAPTURE vs MIXED) concentration is near-identical
(top5 0.678 vs 0.625; Gini 0.918 vs 0.903) while exit differs threefold (0.105 vs
0.339). **Retention, not concentration, separates the regimes.** QUIET sits lower on
both concentration measures only because it is barely active — an activation effect,
not a retention one, which is why non-CAPTURE must not be pooled.

## (e) Decoupled-δ — zero capture — `recon/decoupled_k1.5|k3.0|k6.0` [C] [T]
**Provenance: RECOMPUTED** via `regime_classifier.classify_dataframe` (hierarchical).
_Here the committed `regime` column happened to match the recompute exactly (0%
disagreement) — because decoupled δ never closes the exit, so no run reaches CAPTURE
under any schema — but it is now recomputed on principle, not trusted._

4050 runs each. When δ is decoupled from enforcer share, capture never occurs at any
coupling strength, **even with δ-drift on** (contrast with (c), where coupled drift
produces capture):

| coupling | QUIET | MIXED | CAPTURE | drift-on (η>0) |
|---|---|---|---|---|
| k=1.5 | 450 | 3600 | 0 | 360 QUIET / 2880 MIXED / 0 CAPTURE |
| k=3.0 | 450 | 3600 | 0 | 360 QUIET / 2880 MIXED / 0 CAPTURE |
| k=6.0 | 450 | 3600 | 0 | 360 QUIET / 2880 MIXED / 0 CAPTURE |

This is the key contrast to (c): **coupled** endogenous δ (factorial) closes the exit
and yields capture; **decoupled** δ does not, at any k. Source columns:
`final_exit_rate, max_punish, eta_delta_drift`.

## (f) v3.3 endogenous exit capacity [S] [∞]
**Provenance: DIRECT** — computed from this session's run_summary/metrics/agent_final + panel; no regime column involved.
_Threshold-free: closure threshold, machine-precision anti-circularity, and capacity/exit are continuous quantities._

Model: `src/religion_fundamentalism_abm_v3_3.py` (edited this session). Aggregated
CSVs materialized under `results/v3_3_endogenous_capacity/`. **[S]** = these become
**[C]** once the item-3 commit lands; raw per-run dirs are not committed.

**Closure threshold — `results/v3_3_endogenous_capacity/closure_sweep.csv`.** Tie
channel fixed point o* = (renewal_base − crowdout)/(decay − renewal); the tie
channel closes (o*≤0) iff crowd-out > base renewal = 0.006. Sweep (μ=0.3, σ=0.95,
π=0.25, 5 seeds):

| ec_tenure_crowdout | o* pred | tie closes | mean exit_capacity final | exit_last100 |
|---|---|---|---|---|
| 0.0005 | +0.917 | no | 0.910 | 0.023 |
| 0.002 | +0.667 | no | 0.817 | 0.040 |
| 0.008 | −0.333 | yes | 0.490 | 0.055 |

Threshold, not ratchet. Note: at μ=0.3 the econ channel stays high (~0.96), so total
capacity floors at ~0.49 when the tie channel closes rather than reaching 0; the
capacity→0 closure requires closing the econ channel too (μ above its own threshold).

**Anti-circularity — `results/v3_3_endogenous_capacity/anticircularity_panel.csv`**
(directional, erosion arm, n=462,702 agent-steps, 1500 clusters). The capacity
update reconstructs from its declared inputs (ties, econ, tenure, hetero) to **max
residual 3.33e-16** (machine zero). Regressing that structural residual on lagged
enforcement gives coefficients ≤ **6.2e-19** (all p>0.05). The naive
`Δcap ~ cap_{t-1} + enforcement` spec shows a spurious `delivered` term (9.6e-5,
p=3.7e-5) — omitted-variable bias from the capacity *sum* proxying a nonlinear
update, not a leak; the structural residual is the correct test. Enforcement has
provably zero effect on capacity.

**Generational arms — `results/v3_3_endogenous_capacity/generational_arms.csv`**
(final code, μ=0.3, σ=0.95, π=0.25, 5 seeds):

| arm | ec@449 | cum exit | exit_last100 | frac born-inside |
|---|---|---|---|---|
| erosion (turnover off) | 0.817 | 0.448 | 0.040 | 0.000 |
| born_inside 0.8 | 0.738 | 0.477 | 0.090 | 0.469 |
| born_inside 0.0 (control) | 0.872 | 0.496 | 0.100 | 0.000 |

The born-inside cohort lowers aggregate exit capacity vs the outside-joiner control
(0.738 vs 0.872) — the predicted direction; the effect on realized exit is modest at
μ=0.3 because the econ channel is near-saturated there. Erosion per-seed detail:
`results/v3_3_endogenous_capacity/erosion_arm_summary.csv`.

**Generational arms with the econ channel LIVE — `generational_arms_live_econ.csv`**
(μ∈{0.6,0.8}, both crowd-out levels, born∈{0.8,0.0}, 10 seeds). ei* =
0.004/(0.01·μ) = 0.667 (μ=0.6) / 0.500 (μ=0.8), both < 1; mean econ_independence
0.52–0.74 confirms the channel is genuinely **interior**, not clipped at 1.

| μ | crowd | born | ec@449 | cum exit | last100 | fracBorn | mean econ |
|---|---|---|---|---|---|---|---|
| 0.6 | 0.002 | 0.8 | 0.604 | 0.426 | 0.075 | 0.494 | 0.645 |
| 0.6 | 0.002 | 0.0 | 0.750 | 0.449 | 0.055 | 0.000 | 0.743 |
| 0.6 | 0.008 | 0.8 | 0.363 | 0.211 | 0.030 | 0.480 | 0.641 |
| 0.6 | 0.008 | 0.0 | 0.488 | 0.304 | 0.060 | 0.000 | 0.736 |
| 0.8 | 0.002 | 0.8 | 0.538 | 0.405 | 0.083 | 0.505 | 0.519 |
| 0.8 | 0.002 | 0.0 | 0.672 | 0.436 | 0.077 | 0.000 | 0.595 |
| 0.8 | 0.008 | 0.8 | 0.303 | 0.138 | 0.017 | 0.472 | 0.520 |
| 0.8 | 0.008 | 0.0 | 0.416 | 0.248 | 0.044 | 0.000 | 0.593 |

With the econ channel live, the born-inside effect is **consistent and larger**: in
every (μ, crowd) pair born_inside=0.8 has lower ec@449 than the born_inside=0.0
control (Δ ≈ −0.11 to −0.15) and lower cumulative exit — a congregation that
reproduces internally erodes aggregate exit capacity and retains more members, with
no enforcement involved. Both structural knobs act monotonically: higher μ (econ
dependence) and higher crowd-out each lower capacity.

---

## What the table establishes (thesis, one line each)

1. **Activation axis** — code geometry (σ×π) sets whether the apparatus activates
   [(a) open map]; exogenous threat shocks do not change it [(c) off≡on null].
2. **Retention axis** — exit capacity sets whether it holds anyone [(a) sealed vs
   open, (b) dose-response]. Capture requires the exit to close: **coupled**
   endogenous δ closes it and yields capture [(c) factorial, drift-on → 2880
   CAPTURE], **decoupled** δ does not at any strength [(e) → 0 CAPTURE].
3. **The two axes are largely separable but coupled at the margin** — sealing the
   exit raises activation in 12/63 frontier cells (mean +0.062, never falls); state
   as a non-orthogonality caveat, not independent axes.
4. **Concentration is downstream, not an axis** — high wherever active (~60% top-5%,
   Gini ~0.9), 84% privilege-manufactured [(d)], and it never once discriminated
   capture across 9,570 runs [vacuity audit].
5. **Capture = retained ∧ active** (clean 2×2, 0.38% reclassification); COLLAPSE is
   depopulation *without activation*, a descriptive tail of the inactive region.
6. **v3.3** contributes the endogenous exit-capacity mechanism with a
   machine-precision anti-circularity proof [(f)]; with the econ channel live
   (μ≥0.6) the born-inside cohort erodes capacity monotonically — pending a
   committed rerun.

Threshold-free primary surfaces: `manuscript/RESULTS_CONTINUOUS.md`.
