# CMOT Q-Items Verification Report

## Q-CMOT-1

Path used: `results/v2.7b_endogenous_delta_sweep_gated/reclassified_seed_results.csv`

The direct target path exists, so no fallback path was needed.

Total row count: 1350

Full column list:

```text
['eta_delta_drift', 'delta0', 'sigma', 'pi_reward', 'seed', 'max_punish_intensity_step', 'run_dir', 'final_fund_prevalence', 'final_exit_rate', 'old_max_punish', 'new_max_punish', 'enforcer_punish_share', 'top5_punishment_share', 'top10_punishment_share', 'old_regime_legacy', 'new_regime_legacy', 'old_regime_hier', 'new_regime_hier', 'reclassified_legacy', 'reclassified_hier', 'reclassified']
```

Regime columns found as close equivalents:

```text
old_regime_legacy:
MIXED    1200
QUIET     150

new_regime_legacy:
MIXED    1200
QUIET     150

old_regime_hier:
CAPTURE_HIERARCHICAL    960
MIXED                   240
QUIET                   150

new_regime_hier:
CAPTURE_HIERARCHICAL    960
MIXED                   240
QUIET                   150
```

Comparison to manuscript claim `120 quiet, 494 mixed, 466 capture` (total 1080):

- Full-file total does not match 1080. The loaded file has 1350 rows.
- Neither corrected schema column reproduces `120/494/466`.
- Corrected legacy vector, full file: QUIET 150, MIXED 1200, CAPTURE 0, COLLAPSE 0.
- Corrected hierarchical vector, full file: QUIET 150, MIXED 240, CAPTURE_HIERARCHICAL 960, COLLAPSE 0.
- Full-file discrepancy vs claim:
  - Legacy: QUIET +30, MIXED +706, CAPTURE -466, total +270.
  - Hierarchical: QUIET +30, MIXED -254, CAPTURE +494, total +270.
- Capture count under corrected legacy schema: 0.
- Capture count under corrected hierarchical schema: 960 (`CAPTURE_HIERARCHICAL`).

Denominator check: the natural drift-on subset `eta_delta_drift > 0` has 1080 rows, which matches the manuscript total. Even on that subset, neither schema reproduces `120/494/466`:

```text
eta_delta_drift > 0, corrected legacy:
MIXED    960
QUIET    120

eta_delta_drift > 0, corrected hierarchical:
CAPTURE_HIERARCHICAL    960
QUIET                   120
```

Thus the `466 capture` count is not reproduced by the corrected reclassification columns. Under corrected legacy it is 0; under corrected hierarchical it is 960 for the drift-on 1080-row subset and 960 for the full file.

## Q-CMOT-2

Dose-response search result: no `reclassified_seed_results.csv` or `sweep_seed_results.csv` was found inside `results/dose_response` quickly. The available per-run dose-response aggregate loaded was:

`results/dose_response/all_runs.csv`

Related cell summary file present:

`results/dose_response/summary.csv`

`all_runs.csv` columns include `regime_hier` but do not include `regime_legacy`.

All drift-on runs (`drift_condition == "drift_on"`):

```text
n = 600

regime_legacy:
not present

regime_hier:
MIXED       515
QUIET        79
COLLAPSE      6

median final_fund_prevalence = 0.10625
```

Exact manuscript-sentence subset (`drift_condition == "drift_on"` and `sigma >= 0.4`):

```text
n = 420

regime_legacy:
not present

regime_hier:
MIXED    420

median final_fund_prevalence = 0.1070336391437308
median final_exit_rate = 0.08
median max_punish = 0.19575089348218555
median enforcer_punish_share = 0.9847404632123202
```

Schema finding:

- The stored column is named `regime_hier`, but `scripts/run_dose_response.py` classifies CAPTURE using `prev >= 0.90 and exit_rate <= 0.20`, then assigns MIXED when `max_punish >= 0.10`.
- That is the prevalence-gated legacy-style CAPTURE rule, not the canonical hierarchical rule described in the manuscript as having no prevalence criterion.
- Therefore the manuscript sentence is wrong to attribute the MIXED classification to the hierarchical regime scheme using a 0.90 prevalence threshold.
- The MIXED classification there comes from the legacy-style schema, despite the column name `regime_hier`.
- One-word correction needed: `legacy`.

QITEMS DONE

## Q-CMOT-1 follow-up: reclassified columns

Loaded `results/v2.7b_endogenous_delta_sweep_gated/reclassified_seed_results.csv`.
Full rows: 1350
Drift-on rows (eta_delta_drift > 0): 1080

### FULL

`reclassified_legacy` value_counts():
```
reclassified_legacy
False    1350
```
Equals {QUIET:120, MIXED:494, CAPTURE:466} after treating CAPTURE_HIERARCHICAL as CAPTURE: False

`reclassified_hier` value_counts():
```
reclassified_hier
False    1350
```
Equals {QUIET:120, MIXED:494, CAPTURE:466} after treating CAPTURE_HIERARCHICAL as CAPTURE: False

`reclassified` value_counts():
```
reclassified
False    1350
```
Equals {QUIET:120, MIXED:494, CAPTURE:466} after treating CAPTURE_HIERARCHICAL as CAPTURE: False

`new_regime_legacy` value_counts():
```
new_regime_legacy
MIXED    1200
QUIET     150
```
Equals {QUIET:120, MIXED:494, CAPTURE:466} after treating CAPTURE_HIERARCHICAL as CAPTURE: False

`new_regime_hier` value_counts():
```
new_regime_hier
CAPTURE_HIERARCHICAL    960
MIXED                   240
QUIET                   150
```
Equals {QUIET:120, MIXED:494, CAPTURE:466} after treating CAPTURE_HIERARCHICAL as CAPTURE: False

### DRIFT_ON

`reclassified_legacy` value_counts():
```
reclassified_legacy
False    1080
```
Equals {QUIET:120, MIXED:494, CAPTURE:466} after treating CAPTURE_HIERARCHICAL as CAPTURE: False

`reclassified_hier` value_counts():
```
reclassified_hier
False    1080
```
Equals {QUIET:120, MIXED:494, CAPTURE:466} after treating CAPTURE_HIERARCHICAL as CAPTURE: False

`reclassified` value_counts():
```
reclassified
False    1080
```
Equals {QUIET:120, MIXED:494, CAPTURE:466} after treating CAPTURE_HIERARCHICAL as CAPTURE: False

`new_regime_legacy` value_counts():
```
new_regime_legacy
MIXED    960
QUIET    120
```
Equals {QUIET:120, MIXED:494, CAPTURE:466} after treating CAPTURE_HIERARCHICAL as CAPTURE: False

`new_regime_hier` value_counts():
```
new_regime_hier
CAPTURE_HIERARCHICAL    960
QUIET                   120
```
Equals {QUIET:120, MIXED:494, CAPTURE:466} after treating CAPTURE_HIERARCHICAL as CAPTURE: False

Explicit answer:
No. No column on either the full file or the drift-on subset reproduces 120 quiet / 494 mixed / 466 capture. For the drift-on subset, reclassified_hier has CAPTURE count 0 after treating CAPTURE_HIERARCHICAL as CAPTURE.

## Q-CMOT-1 resolution: prevalence-gate scheme

Verification target:

`results/v2.7b_endogenous_delta_sweep_gated/reclassified_seed_results.csv`

### Part A: classifier source and thresholds

The relevant Python classifiers found for the gated endogenous-delta sweep are:

1. `scripts/run_v2_7_endogenous_delta_sweep.py`, original sweep classifier:

```text
16 def classify_regime(exit_rate: float, prevalence: float, max_punish: float, capture_exit_cap: float) -> str:
17     if exit_rate >= 0.90:
18         return "COLLAPSE"
19     if prevalence >= 0.90 and exit_rate <= capture_exit_cap:
20         return "CAPTURE"
21     if max_punish >= 0.10:
22         return "MIXED"
23     return "QUIET"
```

The default capture exit cap is:

```text
407     ap.add_argument("--capture-exit-cap", type=float, default=0.20)
```

So the original sweep classifier uses fundamentalist prevalence `>= 0.90`, exit `<= 0.20` by default, punishment `>= 0.10` for active/MIXED, and no enforcer-share threshold.

2. `scripts/reclassify_regimes.py`, source of the `reclassified_seed_results.csv` regime columns:

```text
32 def classify_legacy(exit_rate: float, prevalence: float, max_punish: float) -> str:
33     if exit_rate >= 0.90:
34         return "COLLAPSE"
35     if prevalence >= 0.90 and exit_rate <= 0.20:
36         return "CAPTURE"
37     if max_punish >= 0.10:
38         return "MIXED"
39     return "QUIET"
42 def classify_hier(
43     exit_rate: float,
44     max_punish: float,
45     enforcer_punish_share: float,
46     capture_exit_cap: float = 0.20,
47 ) -> str:
48     if exit_rate >= 0.90:
49         return "COLLAPSE"
50     if exit_rate <= capture_exit_cap and max_punish >= 0.10 and enforcer_punish_share >= 0.70:
51         return "CAPTURE_HIERARCHICAL"
52     if max_punish >= 0.10:
53         return "MIXED"
54     return "QUIET"
```

The corrected hierarchical column uses `new_max_punish`:

```text
207     # old classification (using diluted max_punish)
208     old_legacy = classify_legacy(exit_rate, prevalence, old_max_punish)
209     old_hier = classify_hier(exit_rate, old_max_punish, enforcer_share, capture_exit_cap)
211     # new classification (using active-only max_punish)
212     new_legacy = classify_legacy(exit_rate, prevalence, new_max_punish)
213     new_hier = classify_hier(exit_rate, new_max_punish, enforcer_share, capture_exit_cap)
```

The reclassification script default is:

```text
398     ap.add_argument("--capture-exit-cap", type=float, default=0.20,
399                     help="exit rate cap for CAPTURE classification (default: 0.20)")
```

Conclusion for Part A: I did not find a Python classifier in `scripts/` or `src/` that encodes capture as hierarchical dynamics plus `final_fund_prevalence >= 0.10`. The implemented code uses either a legacy prevalence threshold of `0.90` or a hierarchical rule with no prevalence gate. The manuscript text at `manuscript/manuscript.tex:629` describes a `0.10` composition threshold; applying that threshold post hoc to the hierarchical-dynamics rows is the third scheme tested below.

### Part B: drift-on counts from `reclassified_seed_results.csv`

Drift-on subset: `eta_delta_drift > 0`, `n = 1080`.

Operative max-punish column for the corrected hierarchical classifier is `new_max_punish`. `old_max_punish` gives the same counts in this subset.

Using:

`capture_dynamics = final_exit_rate <= 0.20 AND enforcer_punish_share >= 0.70 AND new_max_punish >= 0.10`

Counts:

```text
capture_dynamics = 960
capture_dynamics AND final_fund_prevalence >= 0.10 = 466
capture_dynamics AND final_fund_prevalence < 0.10 = 494
quiet by classifier active threshold (new_max_punish < 0.10) = 120
```

The vector `{quiet, capture_dynamics AND prev >= 0.10, remainder}` is:

```text
{120, 466, 494}; sum = 1080
```

Yes, this exactly equals `{120, 466, 494}` in the manuscript order quiet / capture-gated / remainder, with the remainder corresponding to the active capture-dynamics rows whose prevalence stays below `0.10`.

### Part C: prevalence-gate sensitivity on capture-dynamics runs

Within the drift-on subset:

```text
capture gate none = 960
capture gate final_fund_prevalence >= 0.10 = 466
capture gate final_fund_prevalence >= 0.90 = 0
median final_fund_prevalence among capture_dynamics = 0.09867655992363095
```

For the `prev >= 0.10` capture-gated rows, the median final exit rate is `0.0057142857142857` and median enforcer punishment share is `0.9813700595034871`, matching the manuscript's reported medians to rounding.

### Part D: dose-response cross-check

`scripts/run_dose_response.py` classifies capture with a `0.90` prevalence threshold:

```text
141         # regime classification
142         if exit_rate >= 0.90:
143             regime = "COLLAPSE"
144         elif prev >= 0.90 and exit_rate <= 0.20:
145             regime = "CAPTURE"
146         elif max_punish >= 0.10:
147             regime = "MIXED"
148         else:
149             regime = "QUIET"
```

For `results/dose_response/all_runs.csv`, subset `drift_condition == "drift_on"` and `sigma >= 0.4`:

```text
n = 420
stored regime_hier counts = {'MIXED': 420}
dynamics only (final_exit_rate <= 0.20 AND max_punish >= 0.10) = 420
capture with prevalence >= 0.90 = 0
capture with prevalence >= 0.10 = 319
capture with no prevalence gate = 420
```

Adding `enforcer_punish_share >= 0.70` does not change these dose-response dynamics counts in this subset: all 420 dynamics rows also meet the enforcer-share threshold.

### Resolution

(a) The manuscript's `466` capture count is reproducible under a `0.10` prevalence-gated capture rule applied to hierarchical capture dynamics: yes.

(b) The reconstructed emergence-sweep scheme and the dose-response script do not use the same prevalence threshold. The emergence manuscript count is reproduced by `0.10`; `scripts/run_dose_response.py` uses `0.90`.

RESOLUTION DONE

## Hierarchical recompute for prevalence-free rewrite

Source: `results/v2.7b_endogenous_delta_sweep_gated/reclassified_seed_results.csv`

Canonical regime column: `new_regime_hier`; `CAPTURE_HIERARCHICAL` is treated as CAPTURE.

### PART 1 - counts

#### 1a. drift-on (`eta_delta_drift > 0`)

`n = 1080`

```text
new_regime_hier
CAPTURE_HIERARCHICAL    960
QUIET                   120
```

Among `CAPTURE_HIERARCHICAL` rows:

```text
n = 960
median final_exit_rate = 0.0057142857142857
median enforcer_punish_share = 0.9817584814978613
final-delta column = no final-delta column exists
```

#### 1b. drift-off (`eta_delta_drift == 0`)

`n = 270`

```text
new_regime_hier
MIXED    240
QUIET     30
```

#### 1c. subset `sigma == 0.25 & pi_reward == 0.05` (all eta)

```text
QUIET count = 150
total n = 150
```

#### 1d. subset `sigma == 0.25 & pi_reward == 0.50 & eta_delta_drift > 0`

```text
CAPTURE_HIERARCHICAL count = 120
total n = 120
```

#### 1e. subset `sigma == 0.25 & pi_reward == 0.25 & eta_delta_drift > 0`

```text
CAPTURE_HIERARCHICAL count = 120
total n = 120
```

#### 1f. strict low-delta0 capture cells

Cells are unique `(sigma, pi_reward, eta_delta_drift, delta0)`, restricted to `delta0 in {0.1, 0.2}`, `sigma >= 0.75`, and `eta_delta_drift > 0`; each cell has 10 seeds.

```text
cells with CAPTURE_HIERARCHICAL fraction >= 0.70 = 48
total qualifying cells considered = 48
```

#### 1g. subset `sigma == 0.95 & pi_reward == 0.25 & eta_delta_drift == 0.30`

```text
CAPTURE_HIERARCHICAL count = 30
total n = 30
median final_exit_rate = 0.0028571428571428
```

#### 1h. full file

`n = 1350`

```text
new_regime_hier
CAPTURE_HIERARCHICAL    960
MIXED                   240
QUIET                   150
```

### PART 2 - context dump

#### 2a. `grep -n "466\|494\|0\.90\|0\.10" manuscript/manuscript.tex`

```text
230:External observability & $v_{\text{obs}}$ & 0.90 & Probability of observing external compliance \\
267:Base opportunity & 0.30 & 0.30--0.90 & Baseline outside-option quality \\
352:The model initializes $N = 350$ agents on a Watts-Strogatz small-world network \cite{watts1998}. The neighbor count $k$ is set to $\max(4, \text{round}(\sqrt{N}))$, yielding $k = 18$ for $N = 350$. The rewiring probability is $p = 0.10$, producing a network with high clustering and short average path length, consistent with the social structure of bounded religious communities in which most interactions are local but occasional long-range ties exist. The network is static; agents do not form or sever ties during the simulation. This is a simplification addressed in \S7.
389:where $\sigma$ is the substitution weight (the paper's key code-geometry parameter), $x_{\text{obs}}$ is the observer's estimate of $j$'s internal cultivation, and $s_{\text{obs}}$ is the observer's estimate of $j$'s external compliance. The observation process introduces noise: external compliance $s_j$ is observed with probability $v_{\text{obs}}$ (default 0.90; external markers are visible), while internal cultivation $x_j$ is observed with probability $a_{\text{obs}}$ (default 0.05; internal states are opaque). When observation fails, the observer substitutes a random draw from a uniform distribution.
464:We classify each run under two complementary schemas. The legacy four-regime schema requires fundamentalist prevalence at least 0.90 jointly with exit rate at most 0.20 for the CAPTURE label, with COLLAPSE assigned at exit rate at least 0.90, MIXED whenever active punishment is at least 0.10 without collapse or capture, and QUIET as the residual. The hierarchical schema, used for the phase analysis below, drops the prevalence requirement and instead conditions CAPTURE on three concentration criteria: exit rate at most 0.20 (matching the legacy gate), maximum active punishment rate at least 0.10, and enforcer share of punishments at least 0.70. The hierarchical schema isolates the structural-concentration signature without requiring near-uniform population fundamentalism. Both schemas use \emph{active} punishment rate, defined as punishments divided by the surviving (non-exited) population at each timestep, rather than the raw rate which dilutes by exit fraction.
514:Quiet cells are characterized by sub-threshold active punishment. Median maximum active punishment rate is 0.071 (range 0.040 to 0.100), with median exit rate 0.503. The 8 canonical QUIET cells split into two clusters with distinct phenomenology. Five cells occupy the low-legibility low-enforcement-reward region ($\sigma = 0.25$, $\pi = 0.05$) where enforcement never activates because no agent has reason to specialize in it. Three cells, in contrast, sit at $\sigma = 0.95$ with high base opportunity and easy exit (exit threshold 1.5): legibility is high, but the combination of weak enforcement reward and easy exit drains the population faster than the enforcement cadre can stabilize. Both clusters fail to cross the active-enforcement threshold, but for structurally distinct reasons. The first reflects an inactive enforcement niche; the second reflects an active but non-retentive one whose niche collapses before consolidation. Under conditions of low $\pi$, visible compliance can be auditable without sanctioning stabilizing as a social role: monitoring without reward, or monitoring with reward that is outpaced by exit, both leave the system quiet.
617:The gated endogenous drift sweep (135 cells: $\sigma \in \{0.25, 0.75, 0.95\} \times \pi \in \{0.05, 0.25, 0.50\} \times \eta \in \{0.0, 0.05, 0.10, 0.20, 0.30\} \times \delta_0 \in \{0.1, 0.2, 0.3\}$; 10 seeds per cell; 1,350 total runs) produces the full regime structure.
621:At $\eta > 0$ (drift enabled, 1080 runs): 120 quiet, 494 mixed, 466 capture. Capture emerges broadly. In all 466 capture runs, final $\delta = 1.0$ (the maximum), median exit rate $= 0.006$, and median enforcer punishment share $= 0.981$. The enforcement apparatus drove $\delta$ from initial values of 0.1 to 0.3 all the way to 1.0 endogenously.
629:At $\sigma = 0.25$, $\pi = 0.25$, all 120 runs with $\eta > 0$ remain mixed despite $\delta$ drifting to 1.0. Enforcement is active (max\_punish $= 0.166$) and $\delta$ saturates, but fundamentalist prevalence stays below the capture classification threshold. The dynamics are capture-like (near-zero exit, concentrated enforcement, maximum $\delta$) but the community composition metric does not cross 0.10. This is a classification-boundary effect rather than a substantive regime difference.
660:To test whether the relationship between code legibility and enforcement dynamics is monotonic, we conducted a fine-grained dose-response sweep across ten $\sigma$ values (0.10 to 0.95) at two enforcement reward levels ($\pi = 0.25$ and $\pi = 0.50$), with and without endogenous narrative drift ($\eta = 0.10$ versus $\eta = 0$), 30 seeds per combination (1,200 runs total).
664:Below $\sigma = 0.2$, enforcement does not activate. At $\sigma = 0.10$, $\pi = 0.25$, only 3.3\% of runs classify as active. Enforcer share is 0.15. Narrative drift does not engage: final $\delta$ remains at 0.19. The code is too opaque for monitoring to succeed.
672:All drift-on runs at $\sigma \geq 0.4$ exhibit capture-like dynamics (near-zero exit, maximum $\delta$, enforcer share 0.98) but classify as MIXED under the hierarchical regime scheme because fundamentalist prevalence (median 0.10) does not cross the capture threshold (0.90). This reflects a measurement limitation of the prevalence metric. By every behavioral metric except the prevalence count, these systems are in capture.
678:\caption{Dose-response: code legibility ($\sigma$) and enforcement reward ($\pi$) jointly govern enforcement regime. 1,200 ABM runs (10 $\sigma$ values $\times$ 2 $\pi$ levels $\times$ 2 drift conditions $\times$ 30 seeds). Panel~A: enforcement activation. Panel~B: enforcement concentration (enforcer punishment share). Panel~C: population retention (exit rate). Panel~D: narrative drift (final $\delta$). Solid lines: drift enabled ($\eta = 0.10$). Dashed lines: drift disabled ($\eta = 0$). Sand/sienna: $\pi = 0.25$. Wine/charcoal: $\pi = 0.50$.}
1070:\textit{Nature}. 2010;466(7308):861--863.
```

#### 2b. manuscript regime-classification subsection context

```text
440:\]
441:where $y_{\text{target}}$ is the mean belief position of agents whose fundamentalism index $F_i = r_i \times b_i$ exceeds a threshold $F^*$. This creates a feedback loop: enforcers who successfully accumulate high $r$ and $b$ values shift the orthodoxy target toward their own positions, which in turn shifts the population's belief distribution (through the individual drift rule in \S6.3). The $\bar{y}$ ablation (\S8.3) demonstrates that this feedback is not the mechanism driving enforcement concentration; concentration arises from delegation and capital compounding, not from belief convergence.
442:
443:\subsection{Endogenous alternative degradation}
444:
445:The alternative degradation parameter $\delta$, which was held exogenous in the baseline and retention sweeps, becomes endogenous in the gated drift specification through a drift mechanism that links enforcement concentration to narrative degradation of the outside world:
446:\[
447:\delta(t+1) = \delta(t) + \eta \times (\delta_{\text{target}} - \delta(t))
448:\]
449:\[
450:\delta_{\text{target}} = \min(1.0,\; \delta_0 + \text{enforcer\_share})
451:\]
452:\[
453:\text{enforcer\_share} = \frac{\text{total punishment by enforcers}}{\text{total punishment}}
454:\]
455:
456:The parameter $\eta$ controls drift speed. When $\eta = 0$, $\delta$ is fixed at its initial value (recovering baseline behavior). When $\eta > 0$ and the enforcement cadre dominates punishment ($\text{enforcer\_share} > 0.97$, the typical value in active cells), $\delta_{\text{target}}$ approaches $\delta_0 + 1.0$, pushing $\delta$ toward saturation.
457:
458:An intensity gate prevents spurious drift in quiet cells. The drift equation fires only when the maximum per-capita punishment in the population exceeds a floor of 0.08. This floor was calibrated to the quiet-to-active boundary observed in the baseline sweep (quiet cells: median max\_punish = 0.051; active cells: max\_punish $\geq$ 0.091). The gate implements a theoretical constraint: narrative drift requires an enforcement apparatus with institutional salience. A single functionary issuing occasional sanctions does not reshape community cosmology; a vigorous enforcement apparatus that visibly punishes deviants and controls institutional discourse does.
459:
460:\subsection{Regime classification}
461:
462:To summarize system-level outcomes, each simulation run is assigned an operational regime label derived from terminal-state metrics computed over active agents. These labels are intended as compact descriptors of recurrent dynamical patterns, not as claims that the underlying state space is intrinsically discrete. The primary evidentiary objects remain the continuous outcome variables themselves: exit rate, punishment intensity, enforcement concentration, and fundamentalist prevalence. Regime labels are used to compress these variables for visualization and comparison across large parameter sweeps.
463:
464:We classify each run under two complementary schemas. The legacy four-regime schema requires fundamentalist prevalence at least 0.90 jointly with exit rate at most 0.20 for the CAPTURE label, with COLLAPSE assigned at exit rate at least 0.90, MIXED whenever active punishment is at least 0.10 without collapse or capture, and QUIET as the residual. The hierarchical schema, used for the phase analysis below, drops the prevalence requirement and instead conditions CAPTURE on three concentration criteria: exit rate at most 0.20 (matching the legacy gate), maximum active punishment rate at least 0.10, and enforcer share of punishments at least 0.70. The hierarchical schema isolates the structural-concentration signature without requiring near-uniform population fundamentalism. Both schemas use \emph{active} punishment rate, defined as punishments divided by the surviving (non-exited) population at each timestep, rather than the raw rate which dilutes by exit fraction.
465:
466:These thresholds are researcher-specified summary rules rather than estimated natural boundaries. For that reason, all regime maps reported below should be read together with the underlying continuous metrics. Sensitivity checks show that the broad four-region structure is preserved under threshold perturbations of plus or minus five percentage points. At the same time, the thresholds are not treated as sacrosanct. In particular, some runs exhibit capture-like behavior on continuous indicators such as near-zero exit, highly concentrated punishment, and maximal alternative degradation while remaining below the strict prevalence cutoff. Such cases are analytically important because they show that the regime structure is real even when a categorical boundary is conservative. We therefore use the discrete labels for summary presentation, while retaining the continuous metrics as the substantive basis of interpretation.
467:
468:The COLLAPSE label, as defined here, denotes specifically enforcement-induced depopulation. Slow attrition under loose enforcement, exemplified by mainline Protestant decline, late-modern Catholicism, and the demographic transition to religious non-affiliation, is observationally distinct from this mechanism and is currently flattened to MIXED or QUIET within our scheme.
469:
470:Classification is applied at the level of individual seed runs. Parameter-cell classification is then assigned by majority vote across seeds. This two-level procedure avoids treating single stochastic realizations as definitive while preserving within-cell heterogeneity. Where seed disagreement is substantial, that disagreement is itself informative and is reported as boundary instability rather than suppressed by averaging alone.
471:
472:\subsection{Simulation protocol}
473:
474:Each simulation is run for 500 time steps. This horizon is sufficient for the system to approach steady behavior under all tested specifications: punishment concentration, exit rate, and enforcement-share trajectories stabilize by approximately step 200 in the tested configurations, with the remaining horizon serving as a buffer against premature classification. At each step, the model proceeds in five phases. First, agents update internal cultivation and external compliance. Second, agents evaluate neighbors and execute punishment. Third, the institutional controller updates the enforcement cadre, orthodoxy target, and patronage budget. Fourth, agents evaluate exit. Fifth, system metrics are recorded. Agent ordering is randomized within each phase at every step to eliminate order-dependent artifacts.
475:
476:The baseline parameter sweep covers 108 cells spanning the joint space of legibility, enforcement reward, outside-option quality, and exit threshold. To separate exploration from confirmation, this sweep is conducted in two stages: an exploratory pass over the full grid with two seeds per cell, followed by a confirmatory pass on the retained cells with five seeds per cell. All headline regime maps and regime counts in the Results section are taken from the confirmatory stage; exploratory runs are used only to identify candidate boundary structure. The endogenous-drift sweep covers 135 cells spanning legibility, enforcement reward, drift speed, and initial outside-world degradation, with ten seeds per cell. Targeted retention sweeps for sanctified suffering and membership reward add a further 1,320 runs. Across all five sweeps, the total simulation count is 3,246 runs. The model is implemented in Python using Mesa for scheduling, a custom execution loop for enforcement and exit phases, and NetworkX for network generation; all stochastic processes use NumPy's PCG64 generator under fixed seeds for reproducibility.
477:
478:\subsection{Model variants}
479:
480:We analyze a nested sequence of model specifications that progressively add institutional mechanisms while preserving the same agent-based core. The purpose of this sequence is not version proliferation for its own sake, but causal isolation: each extension adds one theoretically motivated mechanism whose incremental contribution can be evaluated against the shared baseline.
```

RECOMPUTE DONE
