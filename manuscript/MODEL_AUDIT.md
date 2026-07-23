# Executable-model audit

Scope: the requested v2.7 model and sweep/figure scripts. This is a code audit, not an interpretation of intended behavior. Line numbers refer to the repository files as audited.

## 1. NETWORK — **MISMATCH**

The manuscript claim (static Watts–Strogatz, `k=18`, `p=0.10`, unchanged after exit) does not describe the audited runs. Although a small-world branch exists, the parameter default is scale-free (`graph: str = "scale_free"`) at `src/religion_fundamentalism_abm_v2_7.py:32`, and both audited sweeps explicitly pass `"--graph", "scale_free"` (`scripts/run_v2_7_endogenous_delta_sweep.py:84-85`; `scripts/run_dose_response.py:65`). The operative scale-free constructor is `return nx.barabasi_albert_graph(p.n, m, seed=int(p.seed))` (`src/religion_fundamentalism_abm_v2_7.py:438-440`), with `m = max(2, int(round(math.log(p.n + 1))))`; for N=350, `m=6`, not WS `k=18`.

The unused small-world option dynamically chooses approximately sqrt(N), not a fixed 18: `k = max(4, int(round(math.sqrt(p.n))))`, makes it even, then calls `nx.watts_strogatz_graph(p.n, k, 0.10, ...)` (`src/religion_fundamentalism_abm_v2_7.py:441-445`). At N=350 this happens to yield 19 rounded then incremented to 20, not 18.

Edges are removed after a successful exit: `n_drop = int(round(p.exit_rewire_fraction * len(neigh_ids)))` and `self.model.G.remove_edge(self.node_id, int(j))` (`src/religion_fundamentalism_abm_v2_7.py:389-398`). The default fraction is 0.90 (`:77`). Thus the graph is not static and positions/adjacencies are not unchanged after exit.

## 2. ENFORCER QUOTA — **MISMATCH**

The actual default is 8%, not 12%: `enforcer_quota_frac: float = 0.08` (`src/religion_fundamentalism_abm_v2_7.py:111`), and both audited sweeps explicitly pass 0.08 (`scripts/run_v2_7_endogenous_delta_sweep.py:122-123`; `scripts/run_dose_response.py:79`). Quota size uses rounding, not floor: `quota = int(round(p.enforcer_quota_frac * len(active)))`, followed by a minimum of one when the fraction is positive (`src/religion_fundamentalism_abm_v2_7.py:495-498`). Python's `round` uses ties-to-even.

## 3. LITERALISM DISTRIBUTION — **MISMATCH**

Literalism is beta-distributed, not uniform: `L_alpha: float = 1.5`, `L_beta: float = 4.5` (`src/religion_fundamentalism_abm_v2_7.py:101-102`) and `self.L = ... rng.beta(self.model.params.L_alpha, self.model.params.L_beta)` (`:145`). Rigidity is separately `Beta(2,4)`: `self.b = ... rng.beta(2.0, 4.0)` (`:147`).

## 4. CAPITAL DECAY — **MISMATCH**

Capital decays every agent update at 0.5% per step: `cap_decay: float = 0.005` (`src/religion_fundamentalism_abm_v2_7.py:112`) and `self.cap = ... self.cap * (1.0 - p.cap_decay)` for both exited and active agents (`:204`, `:209`). The audited sweeps also explicitly pass 0.005 (`scripts/run_v2_7_endogenous_delta_sweep.py:132-133`; `scripts/run_dose_response.py:84`).

## 5. INITIAL STATES — **MISMATCH**

The main states are not initialized uniformly on [0,1]:

- cultivation/ITC: `self.x = ... rng.normal(0.35, 0.12)` clipped to [0,1] (`src/religion_fundamentalism_abm_v2_7.py:143`);
- belief: `self.y = ... rng.normal(0.50, 0.12)` clipped (`:144`);
- literalism: `Beta(1.5,4.5)` clipped (`:145`, with parameters at `:101-102`);
- compliance/EPC: `self.s = 0` (`:146`);
- rigidity `b` and enforcement propensity `r`: each clipped `Beta(2,4)` (`:147-148`);
- utility `u`, capital, and service begin at zero (`:149`, `:161-162`); enforcer status begins false (`:163`).

## 6. FAILED OBSERVATION — **MISMATCH**

There are two different failure behaviors. Failed observation of binary compliance is a fixed zero: `s_obs = other.s if sees_s else 0` (`src/religion_fundamentalism_abm_v2_7.py:170-171`). Failed observation of cultivation is a clipped normal substitute, not uniform: `x_obs = float(np.clip(rng.normal(0.35, 0.25), 0.0, 1.0))` (`:173-177`). Failed heresy/belief observation is also a clipped normal centered on current orthodoxy: `y_obs = float(np.clip(rng.normal(self.model.y0, 0.25), 0.0, 1.0))` (`:185-190`).

## 7. SIMULATION LENGTH — **MISMATCH**

Both requested sweeps use 450 steps, not 500. The endogenous-delta sweep CLI default is `ap.add_argument("--steps", type=int, default=450)` (`scripts/run_v2_7_endogenous_delta_sweep.py:403`) and forwards it via `"--steps", str(steps)` (`:80-81`). Dose response sets `N_STEPS = 450` (`scripts/run_dose_response.py:39`) and passes it at `:63`.

## 8. PHASE ORDER — **MISMATCH**

The controller runs **before** agent updates and punishment, not after punishment. `step()` begins `self._update_controller()` (`src/religion_fundamentalism_abm_v2_7.py:451-452`), then runs each agent's `step()` (`:454-457`), updates cadre assignments (`:459-467`), runs `police_phase()` (`:468-469`), distributes patronage and updates delta (`:475-476`), then attempts exit (`:478-482`) and increments time (`:483`). Metrics are not called within `step()`; the outer simulation loop records them after `model.step()`.

## 9. SHOCKS — **MATCH** for the two named sweeps; **MISMATCH** if the manuscript implies every reported run is shocked

Both named sweeps explicitly pass `--shock_schedule 100,220,320` and a nonzero best-fit strength (`scripts/run_v2_7_endogenous_delta_sweep.py:106-109`; `scripts/run_dose_response.py:20,71-72`, where strength is 0.25).

At a scheduled time, `self.threat += p.shock_strength`; otherwise threat decays by `1-relax_rate` (`src/religion_fundamentalism_abm_v2_7.py:535-540`). Threat then modifies every one of these quantities:

- authority/monopoly driver: `self.A = ... 1.0 - math.exp(-p.A_gain_threat * self.threat)` (`:541`), with monopoly later set by `self.A >= ...` (`:467`);
- patronage budget: `p.budget_base + p.budget_threat_gain * self.threat` (`:542`);
- punishment reward: `p.pi_reward = self.baseline_pi + p.tighten_gain_pi * self.threat` (`:544`);
- punishment severity: `p.lam_punish = self.baseline_lam + p.tighten_gain_lam * self.threat` (`:545`);
- heresy-distance threshold: `p.d0 = ... self.baseline_d0 - p.tighten_gain_d0 * self.threat` (`:546`);
- membership benefit directly through `membership_benefit_threat * self.model.threat` (`:212-215`);
- outside opportunity is reduced through `- p.exit_opportunity_threat_coeff * self.model.threat` (`:337-341`).

Yes, a reported repository sweep includes a shock-free condition: `S0_no_controller_no_exit` has an empty `shock_schedule` and strength 0 in `scripts/run_v2_scenarios.sh:24-30`, and is invoked with `"" 0.00` at `:96`; the script forwards that empty schedule at `:82-83`. The other scenarios use steps 100,220,320 (`:97-100`).

## 10. DELTA DRIFT — **MATCH** to the expected code formula; **MISMATCH** to any claim that delta is exogenous

Drift only runs when eta is positive and punishment intensity meets `punish_floor` (`src/religion_fundamentalism_abm_v2_7.py:554-559`). The operative lines are `enforcer_share = ... enforcer_punish_events_step / ... punish_events_step` (`:560-562`), `delta_target = float(min(1.0, self.delta_baseline + enforcer_share))` (`:563`), and `self.current_delta = ... self.current_delta + eta * (delta_target - self.current_delta)` (`:564`).

The quota sensitivity gives a representative enforcer punishment share around 0.53–0.55: medians range 0.5278–0.5473 across quotas (`manuscript/s1_text.tex:220-227`; generating data `results/ablation_quota/summary_by_quota.csv:2-7`). Hence, for example, baseline delta 0.10 implies a target around 0.63–0.65. If cadre share approaches 1, `min(1, delta0 + share)` mechanically targets 1 (for any nonnegative baseline); repeated gated updates push current delta toward 1, though convergence is gradual at rate eta and stops when the punishment-intensity gate is not met.

## 11. EXIT RULE — **MATCH** to the review allegation; **MISMATCH** to a single-factor account

The outside-opportunity path is:

1. degree is current graph degree (`deg = int(self.model.G.degree(self.node_id))`, `src/religion_fundamentalism_abm_v2_7.py:331`);
2. for delta > 0, the base is first multiplied by `(1-delta)`: `opp_base_eff = p.exit_opportunity_base * (1.0 - delta)` (`:332-336`);
3. raw opportunity is `sigmoid(opp_base_eff - degree_coeff*deg - threat_coeff*threat)` (`:337-341`);
4. it is floor/power transformed: `p_opp = p.exit_block_floor + ... (p_opp_raw ** p.exit_block_exponent)` (`:342`);
5. for delta > 0 it is multiplied by `(1-delta)` a second time: `p_opp *= (1.0 - delta)` (`:343-344`) and clipped (`:345`).

Thus `(1-delta)` appears **twice** in the opportunity computation (once inside the sigmoid through its input and once as an outer multiplier). At delta=1 the outer multiplier makes `p_opp` exactly zero despite `exit_block_floor=0.02` (`:85`). Separately, desire is based on punishment, utility, degree, and membership reward: `exit_drive = (p.exit_threshold - self.u) + punish_exit_term - punish_retention_term - 0.02 * deg - mu`, followed by a sigmoid and accumulation of `exit_intent` (`:352-370`). After the commit threshold, effective exit cost is `exit_cost*(1+degree_coeff*deg)+exit_epc_lockin_coeff*s` (`:373-375`); actual exit requires a fresh draw below `last_p_opp` (`:377-380`).

## 12. ENFORCER PRIVILEGE BUNDLE — **MISMATCH** to any manuscript description that omits a bundled structural advantage

Every code-level advantage found is:

- **exclusive punishment under monopoly:** when monopoly is on, non-enforcers return without policing (`src/religion_fundamentalism_abm_v2_7.py:256-258`);
- **punishment probability multiplier:** monopoly policing uses 1.5; off-monopoly enforcers use 1.5 and non-enforcers use `non_enforcer_punish_eps=0.02` (`:282-286`; defaults `:118-119`). A separate default `non_enforcer_punish_mult=0.25` exists (`:117`) but is not used in this operative branch; the audited sweeps pass both 0.25 and 0.02 (`scripts/run_v2_7_endogenous_delta_sweep.py:142-147`);
- **capital-linked enforcement-cost discount:** `kappa_eff = kappa_cost * (1 - 0.20*cap)` (`src/religion_fundamentalism_abm_v2_7.py:299-300`, parameter `:120`), then enforcers multiply that remaining cost by 0.30 (`:301-302`, parameter `:122`), i.e. a 70% role discount in addition to the capital discount;
- **backlash protection:** enforcer backlash probability is multiplied by 0.25 (`:306-310`, parameter `:121`), a 75% reduction in probability; backlash cost itself remains 0.30 (`:51`, applied `:311-314`);
- **patronage:** the positive institutional budget is distributed only to active enforcers, equally when service is zero or proportional to accumulated service otherwise (`:520-533`); baseline budget is 0.15 plus `0.60*threat` (`:108-110`, `:542`);
- **capital/service feedback:** every punishment adds 0.15 capital and 1 service (`:295-297`; default gain `:113`), which improves future cost and selection rank;
- **selection favors accumulated capital and literalism:** suitability is exactly `0.6 * agent.cap + 0.3 * agent.L + 0.1 * (agent.r * agent.b)` (`:502-503`). Agents with capital at least 0.25 are eligible first (`:505-516`, threshold `:114`), then high-suitability fallbacks fill the rounded quota.

## 13. CONCENTRATION STATISTIC — **MISMATCH**

It is top 5 **percent**, not top 5 agents. `topShare` sets `k = max(1, int(np.ceil(frac * x.size)))` and sums the k largest values (`scripts/build_methodology_paper_canonical.py:77-83`); callers pass 0.05 and 0.10 (`:133-134`). For N=350, top 5% means `ceil(17.5)=18` agents; top 10% means 35. Therefore the manuscript phrase “top 5 agents issue ~85%” is mislabeled relative to the implemented top-5% statistic.

## 14. COLLAPSE CLASSIFIER — **MATCH**

`COLLAPSE` is assigned solely on `exit_rate >= 0.90`, before any punishment test, in both classifiers: `if exit_rate >= 0.90: return "COLLAPSE"` (`scripts/reclassify_regimes.py:32-34` and `:43-49`). There is no punishment requirement for collapse.

## 15. INVARIANCE VS QUOTA — **MISMATCH**

The literal claim that punishment concentration is invariant across all parameters is contradicted by the repository's quota sensitivity. Top-5% share falls materially from 0.868 at quota 0.04 to 0.448 at quota 0.25, while median enforcer share stays near 0.53 (0.538 to 0.528): `manuscript/s1_text.tex:220-227`. The source data give the unrounded values in `results/ablation_quota/summary_by_quota.csv:2-7`. The manuscript itself acknowledges the decline as mechanical at `manuscript/s1_text.tex:232`; that qualification is incompatible with unqualified invariance.

## 16. FIGURE PROVENANCE — **MISMATCH**

Figure 1's generator explicitly filters dose-response data to drift-on only: `df = df[df["drift_condition"] == "drift_on"].copy()` (`scripts/generate_submission_figures.py:82-86`). Therefore this generator cannot produce a drift-off dashed curve from the dose-response dataset; its plot loop varies only `pi_reward` (`:105,129-137`).

Figure 5 is not literalism enrichment. It is a retention-mechanism figure: panel A aggregates monopoly ON/OFF medians for top-5 share, enforcer share, and exit rate (`scripts/generate_submission_figures.py:340-378`); panel B reads quota sensitivity and plots top-5 share, enforcer share, and exit rate against quota (`:395-420`).

`reproduce.sh` invokes only `build_methodology_paper_canonical.py` and `build_methodology_paper_figures.py` (`reproduce.sh:49-52`). The latter's own provenance header says it regenerates manuscript Figures 2, 3, and 6 (plus Table 6 and an unreferenced trajectory artifact), while Figures 1, 4, and 5 come from other pipelines (`scripts/build_methodology_paper_figures.py:4-14`). Its output calls corroborate Figure 2 (`:141`), Figure 3 (`:209`), and Figure 6 (`:176`). Thus `reproduce.sh` does **not** actually regenerate all manuscript figures despite its broad comments at `reproduce.sh:2-9,58-61`.

## MISMATCH SUMMARY

Mismatches are present in items **1, 2, 3, 4, 5, 6, 7, 8, 9 (only the universal-shock implication), 10 (if delta is described as exogenous), 11 (if described as a single delta factor), 12 (if the privilege bundle is omitted), 13, 15, and 16**. Item 14 matches. Item 9 matches for the two named v2.7 sweeps, item 10 matches the expected drift formula, and item 11 confirms the review's double-factor allegation.

AUDIT DONE
