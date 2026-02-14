# Comprehensive Audit Report: Religion-Code-Geometry ABM

**Date:** 2026-02-13
**Auditor:** Claude Opus 4.6
**Codebase:** `/storage/social-science/religion-code-geometry-abm/`
**Latest version audited:** `src/religion_fundamentalism_abm_v2_5.py` (837 lines)
**Total codebase:** ~9,000 lines (9 simulation versions + 15 analysis scripts)

---

## 1. Project Overview

This is a multi-version agent-based model exploring how religious fundamentalism, institutional enforcement, costly signaling, and apostasy co-evolve in a networked community under external threat.

### Tech Stack

| Component | Version |
|-----------|---------|
| Python | 3.12.4 |
| Mesa | 3.4.2 |
| pandas | 3.0.0 |
| numpy | 2.4.2 |
| networkx | 3.6.1 |
| matplotlib | 3.10.8 |

### Version History

| File | Lines | Key Addition |
|------|-------|-------------|
| `religion_fundamentalism_abm.py` | 356 | Base model (v0) |
| `religion_fundamentalism_abm_v1_1.py` | 376 | Minor refinements |
| `religion_fundamentalism_abm_v2.py` | 554 | Heresy/apostasy dynamics |
| `religion_fundamentalism_abm_v2_1.py` | 575 | Exit friction parameter |
| `religion_fundamentalism_abm_v2_2.py` | 638 | Regime grid exploration |
| `religion_fundamentalism_abm_v2_3.py` | 667 | Mixed regime search |
| `religion_fundamentalism_abm_v2_3_1.py` | 690 | Boundary refinements |
| `religion_fundamentalism_abm_v2_4.py` | 803 | Internal army / enforcer delegation |
| `religion_fundamentalism_abm_v2_5.py` | 837 | Monopoly on enforcement, literalism trait |

### Simulation Runs Completed

- ~17 batch runs, ~100+ individual simulations
- Each produces: `metrics.csv` (350-450 rows x 32 columns), `agent_summary.csv` (300-350 rows x 17 columns)
- Aggregate outputs: regime maps, Gini analyses, phase diagrams, MP4 network visualizations

---

## 2. Claim Verification: Do Simulations Do What They Claim?

### Claim 1: "Costly signaling substitutes for ideological work"

**VERDICT: CORRECTLY IMPLEMENTED**

The `perceived_moral()` function (`v2_5.py` line 159-172) computes:

```
moral = (1 - sigma) * x_obs + sigma * s_obs
```

With `sigma=0.75`, EPC (visible signal `s`) accounts for 75% of moral perception. ITC (`x`) is only observed 5% of the time (`a_obs=0.05`). So 95% of the time, observers use a random guess for ITC but accurately see EPC 90% of the time. Agents can appear moral by displaying `s=1` without genuine cultivation.

### Claim 2: "Threat increases enforcement and orthodoxy"

**VERDICT: CORRECTLY IMPLEMENTED**

The `_update_controller()` (`v2_5.py` line 488-504) correctly:

- Increases `pi_reward` (enforcement reward) linearly with threat
- Increases `lam_punish` (punishment severity) linearly with threat
- Decreases `d0` (heresy threshold -- narrower tolerance) with threat
- Shifts `y0` (orthodoxy target) toward fundamentalist consensus

### Claim 3: "Exit barriers scale with network embeddedness and threat"

**VERDICT: CORRECTLY IMPLEMENTED**

`maybe_exit()` (`v2_5.py` line 325-330):

```python
p_opp_raw = sigmoid(base - deg_coeff*deg - threat_coeff*threat)
p_opp = floor + (1-floor) * (p_opp_raw ** block_exponent)
```

Both degree and threat suppress exit opportunity nonlinearly (exponent=2.5). Correctly models "can't leave during a crisis" and "social bonds trap you."

### Claim 4: "Institutional monopoly concentrates punishment in a minority"

**VERDICT: CORRECTLY IMPLEMENTED, RESULTS CONFIRM**

V2.5 results (30 seeds, `batch_v2_5_monopoly_20260213_090212`):

| Metric | Median | Threshold | Pass? |
|--------|--------|-----------|-------|
| Top-5 punishment share | 0.803 | >= 0.30 | YES |
| Top-10 punishment share | 0.977 | >= 0.50 | YES |
| Enforcer punishment share | 0.760 | >= 0.70 | YES |
| Cohen's d (L enrichment) | 2.241 | > 0.20 | YES |

The monopoly mechanism (`v2_5.py` line 250-251: non-enforcers blocked when `A >= 0.35`) combined with patronage distribution creates strong concentration.

### Claim 5: "Literalism drives heresy prosecution"

**VERDICT: CORRECTLY IMPLEMENTED**

Via `theta_L_gain` and `d0_L_gain` (`v2_5.py` line 270-271), high-literalism agents have stricter moral thresholds and tighter heresy tolerance. Combined with cadre selection weighting L at 30% (line 466), literalism leads to enforcer selection leads to punishment monopoly. Cohen's d of 2.241 confirms massive L enrichment among enforcers.

### Claim Verification Comparison: V2.4 vs V2.5

| Metric | V2.5 (Monopoly) | V2.4 (Internal Army) |
|--------|-----------------|----------------------|
| Punishment top-5 share | 0.803 | 0.230 |
| Punishment top-10 share | 0.977 | 0.388 |
| Enforcer punishment share | 0.760 | 0.079 |
| Cohen's d (L enrichment) | 2.241 | 1.978 |
| All criteria met | YES | NO |

V2.5's monopoly mechanism is the key differentiator. V2.4 failed to concentrate punishment because non-enforcers could still punish at 25% rate (`non_enforcer_punish_mult`), diluting the institutional monopoly.

---

## 3. Bugs and Logic Issues

### BUG 1 (Severity: Low) -- Dead code in monopoly enforcement

**File:** `v2_5.py` line 276

```python
if monopoly_on:
    pun_mult = p.enforcer_punish_mult if self.is_enforcer else 0.0  # DEAD CODE
```

Non-enforcers already `return` on line 251 when monopoly is on. The `else 0.0` branch is unreachable. Not a functional bug (correct behavior), but indicates copy-paste from a prior version without cleanup.

### BUG 2 (Severity: HIGH) -- Metrics include exited agents in aggregates

**File:** `v2_5.py` line 508-516

```python
xs = np.array([a.x for a in self.people.values()], dtype=float)  # ALL agents
```

`mean_x`, `mean_y`, `mean_epc`, `mean_r`, `mean_b`, and critically `fund_prevalence` are computed over ALL agents including exited ones. Exited agents have `s=0` and frozen `r`, `b` values.

**Impact:**

- `mean_epc` is deflated (exited agents have `s=0`)
- `fund_prevalence` could be inflated (agents who exited with high `r*b` still count)
- As exit rate climbs, these metrics become increasingly contaminated
- Active-only metrics exist for `mean_degree_active`, `p_opp_mean`, and `stay_value` (line 520-526) but NOT for core belief/enforcement metrics

**Why this matters:** The regime classification in analysis scripts (`classify_regime()`) uses `fund_prevalence` and `exit_rate` -- if prevalence is inflated by frozen exited-agent values, regime boundaries could shift. For example, a run might be classified as CAPTURE (prevalence >= 0.90) when active-agent prevalence is actually lower.

### BUG 3 (Severity: Low) -- Duplicate metric column

**File:** `v2_5.py` line 552-553

```python
mean_p_opp=p_opp_mean,
p_opp_mean=p_opp_mean,
```

Same value written under two column names. Harmless but sloppy.

### BUG 4 (Severity: Medium) -- Cadre eligibility bypass

**File:** `v2_5.py` line 468-470

```python
eligible = [a for a in active if a.cap >= cap_to_enforcer]
ranked = sorted(eligible if len(eligible) >= quota else active, key=suitability, reverse=True)
```

When fewer agents have `cap >= 0.25` than the quota requires, the eligibility threshold is completely bypassed and agents with `cap=0` can become enforcers based purely on literalism (L).

**Impact:** Early in the simulation (before anyone has accumulated institutional capital), cadre selection is driven entirely by `0.3*L + 0.1*(r*b)`. This creates an artificial literalism-selection effect at startup. The `cap_to_enforcer` threshold is effectively meaningless for the first ~50-100 timesteps until enough agents have punished enough to accumulate capital.

**Why this matters:** The early-simulation enforcer selection based on L alone could create path-dependent dynamics where high-L agents get an initial enforcement monopoly, accumulate capital, and then maintain their position even after the capital threshold becomes binding. The "institutional capital" story may partly be an artifact of initial-condition sensitivity.

### ISSUE 5 (Severity: Medium) -- Orthodoxy drift positive feedback loop

**File:** `v2_5.py` line 241 and line 501-504

Belief drift toward orthodoxy (line 241):
```python
self.y = clip(self.y + 0.02 * (self.model.y0 - self.y) + noise, 0, 1)
```

Orthodoxy target shifts toward fundamentalist consensus (line 501-504):
```python
y_enforcers = [a.y for a in ... if a.fundamentalism_index() > F_star]
y_target = mean(y_enforcers)
self.y0 = clip(0.95 * y0 + 0.05 * y_target, 0, 1)
```

This creates a positive feedback loop:

1. Fundamentalists define orthodoxy
2. Orthodoxy moves toward their beliefs
3. All agents drift toward that orthodoxy
4. More alignment with fundamentalists
5. Repeat

The damping (0.95/0.05 blend) is mild. Worth testing whether `y0` fixation occurs and whether the model's heresy dynamics are dominated by this self-reinforcing drift rather than the intended enforcement mechanisms.

---

## 4. Theoretical / Methodological Concerns

### 4A. No heterogeneity in membership benefits

All agents receive identical `membership_gain` (`v2_5.py` line 206):

```python
membership_gain = membership_benefit + membership_benefit_sigma * legibility + membership_benefit_threat * threat
```

This does not vary by agent. In reality, membership value varies enormously by economic dependence, family ties, social position, etc. This simplification makes exit decisions driven almost entirely by punishment accumulation rather than differential attachment -- potentially oversimplifying the retention mechanism.

### 4B. Asynchronous updating creates order effects

The model shuffles agent IDs each phase (line 427, 432, 443), meaning earlier-acting agents' changes are visible to later agents within the same timestep. The triple-shuffle (once per phase: step, police, exit) mitigates this but does not eliminate it. Whether results are sensitive to this should be tested with synchronous updating as a robustness check.

### 4C. Regime classification uses arbitrary thresholds

```python
if exit_rate >= 0.90: return 'COLLAPSE'
if prevalence >= 0.90 and exit_rate <= 0.20: return 'CAPTURE'
if max_punish >= 0.10: return 'MIXED'
return 'QUIET'
```

These cutoffs (0.90, 0.20, 0.10) are researcher-defined. The boundary analysis should test sensitivity to these choices, since a 5% shift in thresholds could reclassify many parameter regions.

### 4D. Enforcement profitability drives runaway dynamics

Expected value per punishment act for an enforcer:

| Outcome | Probability | Net Utility |
|---------|-------------|-------------|
| No backlash | 0.86 | +0.13 |
| Backlash | 0.14 | -0.17 |
| **Expected** | | **+0.088** |

Enforcement is reliably profitable on average. This drives the enforcement economy but the profit margin may be too generous -- it might be worth testing whether reducing `pi_reward` or increasing backlash creates more interesting phase transitions rather than near-universal enforcement convergence.

### 4E. SHA256 hash only covers v0

The provenance file (`runs/_meta/abm_sha256.txt`) records:

```
589d65b3...  src/religion_fundamentalism_abm.py
```

This is the base version, NOT v2.5. The v2.5 runs lack source code hashing. This is a reproducibility gap.

### 4F. Network topology sensitivity untested in later versions

The batch runners for v2.3+ use only `scale_free` graphs. The v0 batch runner (`batch_run.sh`) tested `scale_free`, `small_world`, and `erdos_renyi`, but this topology sensitivity analysis was not carried forward. Given that scale-free networks have highly skewed degree distributions (which interact with the exit-degree mechanism), results may differ substantially on other topologies.

---

## 5. Statistical Analysis Audit

### Gini coefficient (`aggregate_v2_5_minority.py` line 13-25)

**VERDICT: CORRECT**

Standard discrete formula. Handles negatives via shift to non-negative (defensible choice). The formula `(2 * sum(idx * x) / (n * s)) - (n+1)/n` is the well-known rank-based Gini estimator.

### Cohen's d (`aggregate_v2_5_minority.py` line 37-50)

**VERDICT: CORRECT**

Standard pooled-variance independent samples Cohen's d:

```
d = (mean_a - mean_b) / pooled_sd
pooled_sd = sqrt(((n_a - 1)*var_a + (n_b - 1)*var_b) / (n_a + n_b - 2))
```

Correctly handles edge cases (empty arrays, zero variance).

### Top-k share (`aggregate_v2_5_minority.py` line 28-34)

**VERDICT: CORRECT**

```python
k = max(1, ceil(frac * n))
return sum(sorted_desc[:k]) / total
```

Standard concentration metric. Ceiling ensures at least 1 agent.

### Spearman correlation

**VERDICT: CORRECT**

Uses `pandas .corr(method='spearman')`. Correctly checks for zero variance (`nunique() > 1`).

### Regime aggregation (`aggregate_v2_5_boundaries.py` line 102-130)

**VERDICT: REASONABLE BUT FRAGILE**

Uses medians across seeds for regime classification. This masks potential bimodality -- the same parameters could produce MIXED in some seeds and CAPTURE in others. The median might classify it as one regime, hiding the stochastic nature of regime transitions. Reporting interquartile ranges or modal regime (with frequency) would be more informative.

---

## 6. Code Quality Assessment

| Dimension | Rating | Notes |
|-----------|--------|-------|
| Readability | Good | Clear variable names, consistent structure |
| Modularity | Adequate | Single file per version; phases separated into methods |
| Versioning | Poor | 9 separate files with massive duplication |
| Reproducibility | Mostly Good | Fixed seeds, provenance, pip freeze -- SHA256 gap |
| Testing | None | Zero test files, no unit tests, no regression tests |
| Documentation | Minimal | In-code comments sparse; no README; docs/ is empty |
| Parameter management | Good | Dataclass + argparse, all 130+ params exposed |
| Error handling | Minimal | No validation of parameter ranges or combinations |
| Numerical stability | Good | Sigmoid function handles overflow (line 21-26) |
| Batch infrastructure | Good | Shell scripts with logging, metadata, conditional re-run |

---

## 7. Recommendations

### Priority 1: Fix Bug 2 (Exited Agent Contamination)

Add active-only variants for core metrics:

```python
active = [a for a in self.people.values() if not a.exited]
# compute mean_x_active, mean_epc_active, fund_prevalence_active, etc.
```

This is the most impactful fix -- it could shift regime classification results.

### Priority 2: Add Regression Tests

At minimum, test that:

- Single-step execution produces deterministic output for a fixed seed
- `perceived_moral()` returns values in `[0, 1]`
- `fundamentalism_index()` returns values in `[0, 1]`
- Exit mechanics: agent with `exit_intent >= commit_steps` and passing opportunity check actually exits
- Cadre assignment respects quota
- Patronage distribution sums to budget

### Priority 3: Consolidate Version Files

Replace 9 files with one parametric model controlled by feature flags:

```python
@dataclass
class Params:
    enable_heresy: bool = False      # v2+
    enable_exit: bool = False        # v2+
    enable_cadre: bool = False       # v2.4+
    enable_monopoly: bool = False    # v2.5+
    enable_literalism: bool = False  # v2.5+
```

### Priority 4: Robustness Checks

- Test regime classification sensitivity to threshold choices (+/- 5%)
- Run v2.5 on `small_world` and `erdos_renyi` topologies
- Test synchronous vs asynchronous updating
- Vary `membership_benefit` across agents (heterogeneous attachment)

### Priority 5: Fix SHA256 Provenance

Hash the actual model version being run, not just the base version:

```bash
sha256sum src/religion_fundamentalism_abm_v2_5.py >> runs/_meta/abm_sha256.txt
```

### Priority 6: Documentation

- Write a README describing the model, parameters, and how to run
- Document regime classification criteria and their justification
- Add inline comments to key mechanisms (perceived_moral, police_phase, maybe_exit)

---

## 8. Enforcement Economics Deep Dive

The punishment economy is the engine of the model. Here is a detailed trace:

### For an Enforcer (under monopoly, v2.5 defaults)

```
legibility = sigma * v_obs + (1 - sigma) * a_obs
           = 0.75 * 0.90 + 0.25 * 0.05
           = 0.6875

kappa_eff  = kappa_cost * (1 - kappa_cap_discount * cap) * enforcer_kappa_mult
           = 0.08 * (1 - 0.20 * cap) * 0.30
           = 0.024 * (1 - 0.20 * cap)
           ~ 0.024 (at cap=0) to 0.014 (at cap=2.0)

delta_u    = pi_reward * legibility - kappa_eff
           = 0.22 * 0.6875 - ~0.02
           = 0.1513 - 0.02
           ~ +0.13 per punishment act

p_backlash = (backlash_base + backlash_sensitivity * (1 - legibility)) * enforcer_backlash_mult
           = (0.25 + 1.0 * 0.3125) * 0.25
           = 0.5625 * 0.25
           = 0.14

backlash_cost = 0.30

expected_net = 0.86 * 0.13 + 0.14 * (0.13 - 0.30)
             = 0.112 - 0.024
             = +0.088 per punishment act
```

### For the Target

```
cost = lam_punish = 0.25 (+ tighten_gain_lam * threat under high threat)
```

### Patronage on top

```
budget = budget_base + budget_threat_gain * threat
       = 0.15 + 0.60 * threat
```

At threat = 0.25 (post-shock), budget = 0.30, distributed among ~8% of 300 agents = 24 enforcers. If evenly split: 0.0125 per enforcer per step. If proportional to service: top enforcers get substantially more.

### Net result

Enforcers accumulate utility from both punishment and patronage. Targets lose utility from punishment. This asymmetry drives the exit dynamics (targets hit exit threshold, enforcers remain comfortable).

---

## 9. Threat Dynamics Trace

With default parameters (`shock_schedule=(100, 220, 320)`, `shock_strength=0.25`, `relax_rate=0.03`):

| Timestep | Event | Threat | Authority (A) | Monopoly? |
|----------|-------|--------|----------------|-----------|
| 0-99 | Calm | ~0.0 | ~0.0 | No |
| 100 | Shock 1 | 0.250 | 0.394 | Yes (A > 0.35) |
| 150 | Decay | 0.055 | 0.104 | No |
| 200 | Decay | 0.012 | 0.024 | No |
| 219 | Pre-shock | 0.007 | 0.014 | No |
| 220 | Shock 2 | 0.257 | 0.402 | Yes |
| 270 | Decay | 0.056 | 0.106 | No |
| 319 | Pre-shock | 0.012 | 0.024 | No |
| 320 | Shock 3 | 0.262 | 0.408 | Yes |
| 350 | End (decay) | 0.098 | 0.178 | No |

Monopoly only activates briefly (~30-40 steps) after each shock. The rest of the time, enforcement is distributed (non-enforcers punish at `non_enforcer_punish_eps = 0.02`). This creates periodic "enforcement spikes" followed by relaxation.

---

## 10. Data Integrity Verification

### Metrics File (`batch_v2_5_monopoly_20260213_090212/bestparams/seed_01/metrics.csv`)

- 451 rows (timesteps 0-450), 32 columns
- All numeric, no missing values in sample
- Values appropriately bounded (proportions in [0,1], network metrics normalized)
- Temporal progression smooth (no discontinuities except at threat shocks)

### Agent Summary (`batch_v2_5_monopoly_20260213_090212/bestparams/seed_01/agent_summary.csv`)

- 351 rows (350 agents + header), 17 columns
- Punishment distribution highly skewed (most agents issue 0, a few issue many)
- Exit patterns consistent: exit_time varies, exited agents have reduced degree
- Enforcer flag consistent with cadre logic

### Provenance

| Item | Status |
|------|--------|
| Timestamp recorded | YES |
| Python version recorded | YES |
| Package versions recorded | YES |
| Source code hash | PARTIAL (v0 only, not v2.5) |
| Git status | N/A (not a git repo) |

---

## 11. Summary Verdict

### What is WORKING WELL

1. **Core mechanisms are correctly implemented** -- costly signaling, enforcement economics, exit barriers, institutional delegation, and literalism coupling all do what they claim
2. **Statistical analysis is mathematically correct** -- Gini, Cohen's d, top-k share, Spearman correlations are standard and properly coded
3. **Parameter sweep infrastructure is solid** -- batch scripts with seed variation, regime classification, metadata tracking
4. **V2.5 results genuinely demonstrate punishment concentration** -- 80.3% top-5 share across 30 seeds is robust and passes all acceptance criteria
5. **The sigmoid utility function is numerically stable** (line 21-26 handles overflow correctly)
6. **Enforcement economics are internally consistent** -- profitable for enforcers, costly for targets, patronage creates positive feedback

### What NEEDS ATTENTION

1. **BUG 2** (metrics on exited agents) is the most serious issue -- `fund_prevalence` and `mean_epc` become unreliable as exit rate grows, could distort regime classification
2. **BUG 4** (cadre eligibility bypass) creates artificial early literalism selection, potentially confounding the "institutional capital" story
3. **No tests whatsoever** -- 9,000-line research codebase with zero test coverage
4. **Version proliferation** -- 9 near-duplicate files invite drift errors and make maintenance fragile
5. **Empty documentation** -- no README, empty docs/, sparse inline comments
6. **SHA256 gap** -- provenance hashing covers v0 only, not the versions actually being run

### What is THEORETICALLY SOUND

- The model captures real social-science phenomena (enforcement concentration, costly signaling, exit barriers under threat)
- Threat response dynamics are calibrated to produce periodic monopoly activation
- The progression from v2.0 through v2.5 shows iterative refinement toward a specific hypothesis
- The acceptance criteria (top-k share, Cohen's d, enforcer share) are appropriate for the claims being tested

---

*End of audit report.*
