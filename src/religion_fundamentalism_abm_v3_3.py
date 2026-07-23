#!/usr/bin/env python3
"""
religion_fundamentalism_abm v3.3

v3.3 = v2.7 + an endogenous, agent-level EXIT CAPACITY subsystem and cohort
turnover. v2.7 remains the frozen reference model; this file is additive and
reduces exactly to v2.7 when exit_capacity_mode="off" and turnover_mode="off"
(the new code paths make no rng draws in that configuration, so the random
stream and therefore every committed number is preserved).

Motivation. In v2.7 the outside option is a single global scalar `delta`, and
under delta_mode="legacy" its target is

    delta_target = min(1, delta_baseline + enforcer_share)

where enforcer_share is the fraction of punishment acts issued by enforcers.
That is the very quantity capture is *defined* by, so exit closure and capture
were the same variable wearing two hats: the mechanism was circular and could
not be used as evidence that closed exit produces capture.

v3.3 replaces the global delta with a per-agent exit capacity e_i built only
from ties and life history:

    e_i = 0.5 * outside_ties + 0.5 * econ_independence

ANTI-CIRCULARITY INVARIANT (load-bearing; do not relax).
e_i and every input to it may depend ONLY on:
    - tenure inside the group
    - birth status (born inside vs joined from outside)
    - outside/inside tie stocks
    - the generic membership benefit paid to ALL members (mu_membership_reward)
e_i must NEVER read: punishment received or delivered, enforcer/cadre status,
enforcer_punish_share, the service-based patronage budget, practice/compliance,
or the exit rate. `_update_exit_capacity` below is the only writer of these
fields and touches none of those quantities. The enforcement subsystem writes
cap / service / is_enforcer / punished / punish_issued and is never read here,
so the dependency graph is acyclic by construction.

The empirical check on that invariant is the correlation of final e_i with
punishment_received, punishment_delivered and is_enforcer, computed from the
new per-run agent_final.csv.
"""
import os, math, argparse
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import networkx as nx

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import imageio.v2 as imageio
import imageio_ffmpeg
from tqdm import tqdm

from mesa import Agent, Model


def sigmoid(z: float) -> float:
    if z >= 0:
        ez = math.exp(-z)
        return 1 / (1 + ez)
    ez = math.exp(z)
    return ez / (1 + ez)


@dataclass
class Params:
    n: int = 300
    graph: str = "scale_free"  # scale_free | small_world | erdos_renyi
    seed: int = 1

    # Code geometry
    sigma: float = 0.75   # substitutability: EPC counts as moral sufficiency
    v_obs: float = 0.90   # EPC observability
    a_obs: float = 0.05   # ITC observability
    h_obs: float = 0.15   # heresy observability

    # Costs/benefits
    c_epc: float = 0.12
    eps_cult: float = 0.06
    eta_cult: float = 0.07

    # Policing economy
    pi_reward: float = 0.22
    kappa_cost: float = 0.08
    lam_punish: float = 0.25
    backlash_base: float = 0.25
    backlash_cost: float = 0.30
    backlash_sensitivity: float = 1.0

    # Learning / adaptation
    beta_epc: float = 5.0
    beta_pun: float = 6.0
    k_h: float = 10.0
    rho_r: float = 0.04
    rho_b: float = 0.03
    w_m: float = 1.0
    w_heresy: float = 0.6
    d0: float = 0.18

    # Social dynamics
    norm_weight: float = 0.55
    shame_weight: float = 0.70
    noise_x: float = 0.02
    cult_step: float = 0.04

    # Fundamentalism measurement threshold
    F_star: float = 0.45

    # Apostasy / exit dynamics
    exit_cost: float = 0.40
    exit_threshold: float = -1.0
    exit_prob_slope: float = 3.0
    exit_rewire_fraction: float = 0.90
    exit_degree_coeff: float = 0.03
    exit_epc_lockin_coeff: float = 0.25
    exit_min_cost: float = 0.0
    exit_opportunity_base: float = 0.6
    exit_opportunity_deg_coeff: float = 0.03
    exit_opportunity_threat_coeff: float = 1.5
    exit_block_exponent: float = 2.5
    exit_block_floor: float = 0.02
    exit_commit_steps: int = 8
    exit_cooldown: int = 0
    enable_exit: bool = True
    alpha_punish_revalue: float = 0.0
    delta_outside_degrade: float = 0.0
    mu_membership_reward: float = 0.0
    eta_delta_drift: float = 0.0
    punish_floor: float = 0.08
    delta_mode: str = "legacy"
    delta_cap: float = 0.85
    delta_kappa: float = 3.0

    # --- v3.3: endogenous exit capacity ------------------------------------
    # "off" reproduces v2.7 exactly (global delta path, no rng draws added).
    # "endogenous" replaces the global delta with per-agent capacity e_i.
    exit_capacity_mode: str = "off"        # off | endogenous
    ec_outside_ties_init: float = 1.0      # initial outside-tie stock for founders/joiners
    ec_init_random: bool = True            # draw per-agent outside_ties, econ_independence ~ Beta(2,2) at init
    ec_tie_decay: float = 0.01             # per-step decay of outside ties (scaled by current ties)
    ec_tie_renewal_base: float = 0.006     # constant renewal term -> interior fixed point instead of absorbing 0
    ec_tie_renewal: float = 0.004          # tie-proportional renewal rate; MUST be < ec_tie_decay for a stable o*
    ec_tenure_crowdout: float = 0.002      # per-step crowd-out of outside ties by tenure inside
    ec_dependence_rate: float = 0.01       # per-step shift of livelihood onto generic membership benefit
    ec_econ_recovery_base: float = 0.004   # constant recovery floor for economic independence
    ec_econ_recovery: float = 0.002        # econ-proportional recovery rate (see fixed-point note; repelling)
    ec_hetero_sd: float = 0.25             # sd of per-agent LogNormal(0,sd) factor on the two recovery bases
    emit_panel: bool = False               # emit per-step per-agent panel.csv (directional anti-circularity test)
    lambda_exit_opportunity: float = 1.0   # coefficient: exit capacity -> exit OPPORTUNITY channel
    lambda_exit_willingness: float = 1.0   # coefficient: exit capacity -> exit WILLINGNESS channel

    # --- v3.3: cohort turnover ---------------------------------------------
    turnover_mode: str = "off"             # off | on
    death_hazard: float = 0.002            # per-step death probability
    born_inside_frac: float = 0.8          # replacements born inside (o=0) vs joiners from outside

    # Membership value of staying inside the group.
    membership_benefit: float = 0.03
    membership_benefit_sigma: float = 0.08
    membership_benefit_threat: float = 0.10

    # Literalism trait distribution and strictness coupling.
    L_alpha: float = 1.5
    L_beta: float = 4.5
    theta_L_gain: float = 0.12
    d0_L_gain: float = 0.08

    # Institutional delegation / internal army dynamics.
    A_gain_threat: float = 2.0
    A_enforcer_monopoly: float = 0.35
    budget_base: float = 0.15
    budget_threat_gain: float = 0.60
    enforcer_quota_frac: float = 0.08
    cap_decay: float = 0.005
    cap_gain_per_punish: float = 0.15
    cap_to_enforcer: float = 0.25
    cap_max: float = 2.0
    service_decay: float = 0.02
    non_enforcer_punish_mult: float = 0.25
    non_enforcer_punish_eps: float = 0.02
    enforcer_punish_mult: float = 1.5
    kappa_cap_discount: float = 0.20
    enforcer_backlash_mult: float = 0.25
    enforcer_kappa_mult: float = 0.30

    # Institutional controller
    shock_schedule: Tuple[int, ...] = (100, 220, 320)
    shock_strength: float = 0.25
    tighten_gain_pi: float = 0.20
    tighten_gain_lam: float = 0.20
    tighten_gain_d0: float = 0.08
    relax_rate: float = 0.03
    baseline_pi: float = -1.0
    baseline_lam: float = -1.0
    baseline_d0: float = -1.0
    fixed_y0: bool = False


class Person(Agent):
    def __init__(self, unique_id: int, model: "ReligionABM"):
        super().__init__(model)
        self.node_id = unique_id
        rng = self.model.rng

        self.x = float(np.clip(rng.normal(0.35, 0.12), 0.0, 1.0))  # ITC
        self.y = float(np.clip(rng.normal(0.50, 0.12), 0.0, 1.0))  # belief coordinate
        self.L = float(np.clip(rng.beta(self.model.params.L_alpha, self.model.params.L_beta), 0.0, 1.0))
        self.s = 0  # EPC marker
        self.b = float(np.clip(rng.beta(2.0, 4.0), 0.0, 1.0))  # rigidity
        self.r = float(np.clip(rng.beta(2.0, 4.0), 0.0, 1.0))  # enforcement propensity
        self.u = 0.0
        self.punished = 0
        self.punish_issued = 0
        self.punished_total = 0
        self.exited = False
        self.exit_time = -1
        self.exit_cost_eff_last = 0.0
        self.exit_intent = 0
        self.disengaged = False
        self.exit_cooldown_left = 0
        self.last_p_opp = 0.5
        self.last_membership_gain = 0.0
        self.cap = 0.0
        self.service = 0.0
        self.is_enforcer = False
        self.cadre_fallback = False

        # v3.3 exit-capacity state. these four fields are written ONLY by
        # ReligionABM._update_exit_capacity and ReligionABM._turnover, and are
        # never touched by step()/police_phase(), which is what keeps e_i
        # independent of enforcement (see module docstring).
        # the initial population is heterogeneous when ec_init_random is set:
        # per-agent outside_ties and econ_independence are drawn ~ Beta(2,2)
        # (mean 0.5, spread across the unit interval) so the capacity channel
        # has cross-agent variance to test WITHOUT relying on turnover. with the
        # flag off, founders fall back to the homogeneous ec_outside_ties_init /
        # 1.0 defaults (all outside-connected, zero tenure, not born inside).
        if self.model.params.ec_init_random:
            self.outside_ties = float(np.clip(rng.beta(2.0, 2.0), 0.0, 1.0))
            self.econ_independence = float(np.clip(rng.beta(2.0, 2.0), 0.0, 1.0))
        else:
            self.outside_ties = float(np.clip(self.model.params.ec_outside_ties_init, 0.0, 1.0))
            self.econ_independence = 1.0
        # per-agent multiplicative heterogeneity on the two recovery floors: agents
        # differ in available outside contact and independent livelihood, so their
        # equilibria o* and ei* differ and capacity variance persists across the run.
        # LogNormal(0, sd) -> median 1.0, strictly positive. drawn once at init.
        self.ec_hetero = float(np.exp(rng.normal(0.0, self.model.params.ec_hetero_sd)))
        self.tenure = 0
        self.born_inside = False
        self.exit_capacity = 0.5 * self.outside_ties + 0.5 * self.econ_independence

    def perceived_moral(self, other: "Person") -> float:
        p = self.model.params
        rng = self.model.rng

        sees_s = rng.random() < p.v_obs
        s_obs = other.s if sees_s else 0

        sees_x = rng.random() < p.a_obs
        if sees_x:
            x_obs = float(np.clip(other.x + rng.normal(0.0, 0.08), 0.0, 1.0))
        else:
            x_obs = float(np.clip(rng.normal(0.35, 0.25), 0.0, 1.0))

        return (1.0 - p.sigma) * x_obs + p.sigma * s_obs

    def perceived_heresy_distance(self, other: "Person") -> float:
        p = self.model.params
        rng = self.model.rng

        sees_y = rng.random() < p.h_obs
        if sees_y:
            y_obs = float(np.clip(other.y + rng.normal(0.0, 0.08), 0.0, 1.0))
        else:
            y_obs = float(np.clip(rng.normal(self.model.y0, 0.25), 0.0, 1.0))
        return abs(y_obs - self.model.y0)

    def fundamentalism_index(self) -> float:
        return self.r * self.b

    def step(self):
        p = self.model.params
        rng = self.model.rng

        if self.exited:
            self.is_enforcer = False
            self.s = 0
            self.punished = 0
            self.last_membership_gain = 0.0
            self.cap = float(np.clip(self.cap * (1.0 - p.cap_decay), 0.0, p.cap_max))
            self.service = float(max(0.0, self.service * (1.0 - p.service_decay)))
            self.y = float(np.clip(self.y + rng.normal(0.0, 0.01), 0.0, 1.0))
            return

        self.cap = float(np.clip(self.cap * (1.0 - p.cap_decay), 0.0, p.cap_max))
        self.service = float(max(0.0, self.service * (1.0 - p.service_decay)))

        legibility = p.sigma * p.v_obs + (1.0 - p.sigma) * p.a_obs
        membership_gain = p.membership_benefit + p.membership_benefit_sigma * legibility + p.membership_benefit_threat * self.model.threat
        self.last_membership_gain = float(membership_gain)
        self.u += self.last_membership_gain

        if self.disengaged:
            # While disengaging, agents reduce visible participation and stop costly signaling.
            self.s = 0
            self.x = float(np.clip(self.x + rng.normal(0.0, p.noise_x), 0.0, 1.0))
            self.y = float(np.clip(self.y + 0.01 * (self.model.y0 - self.y) + rng.normal(0.0, 0.01), 0.0, 1.0))
            self.punished = 0
            return

        neigh_ids = list(self.model.G.neighbors(self.node_id))
        neigh: List[Person] = [self.model.people[j] for j in neigh_ids if not self.model.people[j].exited] if neigh_ids else []

        local_norm = float(np.mean([n.s for n in neigh])) if neigh else 0.0
        local_enforce = float(np.mean([n.r * n.b for n in neigh])) if neigh else 0.0

        status_gain = p.norm_weight * local_norm + p.shame_weight * local_enforce
        prob_epc = sigmoid(p.beta_epc * (status_gain - p.c_epc))
        self.s = 1 if rng.random() < prob_epc else 0
        if self.s == 1:
            self.u -= p.c_epc

        drive = (p.eta_cult - p.eps_cult) - 0.06 * self.b
        invest = rng.random() < sigmoid(8.0 * drive)
        if invest:
            dx = p.cult_step * sigmoid(6.0 * drive)
            self.x = float(np.clip(self.x + dx + rng.normal(0.0, p.noise_x), 0.0, 1.0))
            self.u += p.eta_cult
            self.u -= p.eps_cult
        else:
            self.x = float(np.clip(self.x + rng.normal(0.0, p.noise_x), 0.0, 1.0))

        # Belief remains plastic and drifts with weak pull toward orthodoxy.
        self.y = float(np.clip(self.y + 0.02 * (self.model.y0 - self.y) + rng.normal(0.0, 0.01), 0.0, 1.0))
        self.punished = 0

    def police_phase(self):
        p = self.model.params
        rng = self.model.rng
        if self.exited or self.disengaged:
            return
        monopoly_on = self.model.monopoly_on
        if monopoly_on and (not self.is_enforcer):
            return

        neigh_ids = [j for j in self.model.G.neighbors(self.node_id) if not self.model.people[j].exited]
        if not neigh_ids:
            return

        scan_prob = 0.15 + 0.70 * (self.r * self.b)
        if rng.random() > scan_prob:
            return

        k = min(len(neigh_ids), 3)
        targets = rng.choice(neigh_ids, size=k, replace=False)

        for tid in targets:
            target: Person = self.model.people[int(tid)]
            m_hat = self.perceived_moral(target)
            d = self.perceived_heresy_distance(target)
            mean_L = self.model.mean_L
            theta_base = 0.55 - 0.20 * self.b
            theta_eff = theta_base + p.theta_L_gain * (self.L - mean_L)
            d0_eff = float(np.clip(p.d0 - p.d0_L_gain * (self.L - mean_L), 0.0, 1.0))
            h_def = sigmoid(p.k_h * (d - d0_eff))
            deficit = p.w_m * (theta_eff - m_hat) + p.w_heresy * h_def
            p_pun_base = self.r * sigmoid(p.beta_pun * deficit)
            if monopoly_on:
                pun_mult = p.enforcer_punish_mult
            else:
                pun_mult = p.enforcer_punish_mult if self.is_enforcer else p.non_enforcer_punish_eps
            p_pun = float(np.clip(p_pun_base * pun_mult, 0.0, 1.0))

            if rng.random() < p_pun:
                self.model.punish_events_step += 1
                if self.is_enforcer:
                    self.model.enforcer_punish_events_step += 1
                target.u -= p.lam_punish
                target.punished += 1
                target.punished_total += 1
                self.punish_issued += 1
                self.cap = float(np.clip(self.cap + p.cap_gain_per_punish, 0.0, p.cap_max))
                self.service = float(self.service + 1.0)

                legibility = p.sigma * p.v_obs + (1.0 - p.sigma) * p.a_obs
                kappa_eff = max(0.0, p.kappa_cost * (1.0 - p.kappa_cap_discount * self.cap))
                if self.is_enforcer:
                    kappa_eff = max(0.0, kappa_eff * p.enforcer_kappa_mult)
                delta_u = (p.pi_reward * legibility) - kappa_eff
                self.u += delta_u

                p_backlash = float(
                    np.clip(p.backlash_base + p.backlash_sensitivity * (1.0 - legibility), 0.0, 1.0)
                )
                if self.is_enforcer:
                    p_backlash = float(np.clip(p_backlash * p.enforcer_backlash_mult, 0.0, 1.0))
                if rng.random() < p_backlash:
                    self.u -= p.backlash_cost
                    self.r = float(np.clip(self.r - 0.5 * p.rho_r, 0.0, 1.0))
                    self.b = float(np.clip(self.b - 0.5 * p.rho_b, 0.0, 1.0))

                if delta_u > 0:
                    self.r = float(np.clip(self.r + p.rho_r, 0.0, 1.0))
                    self.b = float(np.clip(self.b + p.rho_b, 0.0, 1.0))
                else:
                    self.r = float(np.clip(self.r - 0.5 * p.rho_r, 0.0, 1.0))
                    self.b = float(np.clip(self.b - 0.5 * p.rho_b, 0.0, 1.0))

    def maybe_exit(self):
        if not self.model.params.enable_exit:
            return
        if self.exited:
            return

        p = self.model.params
        rng = self.model.rng
        deg = int(self.model.G.degree(self.node_id))
        delta = float(np.clip(self.model.current_delta, 0.0, 1.0))
        endogenous_ec = (p.exit_capacity_mode == "endogenous")
        # hoisted so both channels below read the same value in the same step
        e_i = float(np.clip(self.exit_capacity, 0.0, 1.0))

        if endogenous_ec:
            # v3.3 OPPORTUNITY CHANNEL. the agent's own capacity replaces the
            # global (1 - delta) as the multiplier on the outside-opportunity
            # base. applied exactly once: the legacy second (1 - delta) factor
            # below is skipped entirely in this mode so no factor is doubled.
            opp_base_eff = p.exit_opportunity_base * (e_i ** p.lambda_exit_opportunity)
        elif delta <= 0.0:
            opp_base_eff = p.exit_opportunity_base
        else:
            opp_base_eff = p.exit_opportunity_base * (1.0 - delta)
        p_opp_raw = sigmoid(
            opp_base_eff
            - p.exit_opportunity_deg_coeff * deg
            - p.exit_opportunity_threat_coeff * self.model.threat
        )
        p_opp = p.exit_block_floor + (1.0 - p.exit_block_floor) * (p_opp_raw ** p.exit_block_exponent)
        # exogenous mode imposes delta as a closed exit, so it must apply the same
        # strong exit-closure as legacy (was legacy-only -> imposed delta never closed
        # the exit and the closed-exit->capture test was untestable). decoupled keeps
        # its own delta dynamics and is intentionally excluded here.
        if (not endogenous_ec) and delta > 0.0 and getattr(self.model.params, "delta_mode", "legacy") in ("legacy", "exogenous"):
            p_opp *= (1.0 - delta)
        self.last_p_opp = float(np.clip(p_opp, 0.0, 1.0))

        if self.exit_cooldown_left > 0:
            self.exit_cooldown_left -= 1
            self.disengaged = self.exit_intent >= max(1, p.exit_commit_steps // 2)
            return

        alpha = float(np.clip(p.alpha_punish_revalue, 0.0, 1.0))
        if alpha <= 0.0:
            punish_exit_term = 0.5 * self.punished
            punish_retention_term = 0.0
        else:
            punishment_received = float(self.punished)
            punish_exit_term = 0.5 * punishment_received * (1.0 - alpha)
            retention_strength = 1.0
            punish_retention_term = 0.5 * punishment_received * alpha * retention_strength
        mu = float(np.clip(p.mu_membership_reward, 0.0, 1.0))
        exit_drive = (p.exit_threshold - self.u) + punish_exit_term - punish_retention_term - 0.02 * deg - mu
        p_desire = sigmoid(p.exit_prob_slope * exit_drive)
        if endogenous_ec:
            # v3.3 WILLINGNESS CHANNEL. an agent with no outside ties and no
            # independent livelihood does not merely fail to get out, it stops
            # wanting to: scale the desire-vs-threshold comparison by capacity.
            # separate coefficient from the opportunity channel, applied once.
            p_desire = float(np.clip(p_desire * (e_i ** p.lambda_exit_willingness), 0.0, 1.0))
        if rng.random() < p_desire:
            self.exit_intent += 1
        else:
            self.exit_intent = max(0, self.exit_intent - 1)
        self.disengaged = self.exit_intent >= max(1, p.exit_commit_steps // 2)

        if self.exit_intent < p.exit_commit_steps:
            return

        exit_cost_eff = p.exit_cost * (1.0 + p.exit_degree_coeff * deg) + p.exit_epc_lockin_coeff * self.s
        exit_cost_eff = max(exit_cost_eff, p.exit_min_cost)
        self.exit_cost_eff_last = float(exit_cost_eff)

        if rng.random() >= self.last_p_opp:
            if p.exit_cooldown > 0:
                self.exit_cooldown_left = p.exit_cooldown
            return

        self.exited = True
        self.exit_time = self.model.t
        self.u -= exit_cost_eff
        self.s = 0
        self.disengaged = False
        self.model.exit_successes_step += 1

        neigh_ids = list(self.model.G.neighbors(self.node_id))
        if not neigh_ids:
            return
        n_drop = int(round(p.exit_rewire_fraction * len(neigh_ids)))
        n_drop = max(0, min(len(neigh_ids), n_drop))
        if n_drop <= 0:
            return
        drop_ids = self.model.rng.choice(neigh_ids, size=n_drop, replace=False)
        for j in drop_ids:
            self.model.G.remove_edge(self.node_id, int(j))


class ReligionABM(Model):
    def __init__(self, params: Params):
        super().__init__(seed=params.seed)
        self.params = params
        self.rng = np.random.default_rng(params.seed)

        self.G = self._make_graph(params)

        self.people: Dict[int, Person] = {}
        for i in range(params.n):
            a = Person(i, self)
            self.people[i] = a

        self.y0 = 0.50
        self.threat = 0.0
        self.shock_schedule = set(params.shock_schedule)
        self.baseline_pi = params.pi_reward if params.baseline_pi < 0 else params.baseline_pi
        self.baseline_lam = params.lam_punish if params.baseline_lam < 0 else params.baseline_lam
        self.baseline_d0 = params.d0 if params.baseline_d0 < 0 else params.baseline_d0
        self.params.pi_reward = self.baseline_pi
        self.params.lam_punish = self.baseline_lam
        self.params.d0 = self.baseline_d0
        self.mean_L = float(np.mean([a.L for a in self.people.values()]))
        self.A = 0.0
        self.budget = 0.0
        self.monopoly_on = False
        self.delta_baseline = float(np.clip(params.delta_outside_degrade, 0.0, 1.0))
        self.current_delta = float(self.delta_baseline)
        self.punish_intensity_step = 0.0

        self.t = 0
        self.exit_successes_step = 0
        self.punish_events_step = 0
        self.enforcer_punish_events_step = 0
        self.n_cadre_fallback_step = 0
        self.n_deaths_step = 0
        # v3.3 directional test: per-step per-agent panel (only filled when emit_panel)
        self._panel_rows: List[dict] = []

    def _make_graph(self, p: Params) -> nx.Graph:
        if p.graph == "scale_free":
            m = max(2, int(round(math.log(p.n + 1))))
            return nx.barabasi_albert_graph(p.n, m, seed=int(p.seed))
        if p.graph == "small_world":
            k = max(4, int(round(math.sqrt(p.n))))
            if k % 2 == 1:
                k += 1
            return nx.watts_strogatz_graph(p.n, k, 0.10, seed=int(p.seed))
        if p.graph == "erdos_renyi":
            p_edge = min(0.05, 8.0 / p.n)
            return nx.erdos_renyi_graph(p.n, p_edge, seed=int(p.seed))
        raise ValueError(f"Unknown graph type: {p.graph}")

    def step(self):
        self._update_controller()

        ids = list(self.people.keys())
        self.rng.shuffle(ids)
        for i in ids:
            self.people[i].step()

        ids = list(self.people.keys())
        self.rng.shuffle(ids)
        active_L = [self.people[i].L for i in ids if not self.people[i].exited]
        self.mean_L = float(np.mean(active_L)) if active_L else self.mean_L
        self._update_cadre_assignments()
        self.punish_events_step = 0
        self.enforcer_punish_events_step = 0
        self.punish_intensity_step = 0.0
        self.monopoly_on = self.A >= self.params.A_enforcer_monopoly
        for i in ids:
            self.people[i].police_phase()
        active_after_police = [a for a in self.people.values() if not a.exited]
        if active_after_police:
            self.punish_intensity_step = float(np.mean([a.punished > 0 for a in active_after_police]))
        else:
            self.punish_intensity_step = 0.0
        self._distribute_patronage()
        self._update_delta_drift()
        # v3.3: capacity is refreshed once per step, after the enforcement phase
        # but before exit decisions, so maybe_exit reads a current e_i. it is a
        # no-op (and makes no rng draws) when exit_capacity_mode="off".
        self._update_exit_capacity()

        # v3.3 directional test: snapshot each active agent AFTER this step's
        # enforcement + capacity update. a.punished is this step's punishment
        # RECEIVED (reset in Person.step, incremented in police_phase);
        # punish_issued is cumulative DELIVERED (diffed downstream). recorded
        # before maybe_exit so capacity_t pairs with the enforcement at step t.
        if self.params.emit_panel:
            t_now = self.t
            for i, a in self.people.items():
                if a.exited:
                    continue
                self._panel_rows.append(dict(
                    t=t_now, agent_id=i,
                    exit_capacity=float(a.exit_capacity),
                    outside_ties=float(a.outside_ties),
                    econ_independence=float(a.econ_independence),
                    tenure=int(a.tenure),
                    ec_hetero=float(a.ec_hetero),
                    received_step=int(a.punished),
                    issued_cum=int(a.punish_issued),
                    is_enforcer=int(bool(a.is_enforcer)),
                ))

        ids = list(self.people.keys())
        self.rng.shuffle(ids)
        self.exit_successes_step = 0
        for i in ids:
            self.people[i].maybe_exit()
        # v3.3: deaths resolve at the end of the step, after that step's actions.
        self._turnover()
        self.t += 1

    def _update_exit_capacity(self):
        """v3.3: refresh per-agent exit capacity e_i for all active agents.

        ANTI-CIRCULARITY: every term below reads only tenure, the agent's own
        outside-tie stock, its own economic independence, and the GENERIC
        membership benefit paid to all members (mu_membership_reward). No
        enforcement variable -- punishment received or delivered, enforcer or
        cadre status, enforcer share, the service-weighted patronage budget,
        practice/compliance, the exit rate -- appears anywhere in this method.
        That is the whole point of v3.3; do not add one.

        Ties erode by a compounding mechanism: renewal is proportional to the
        ties you still have, so a shrinking stock renews ever more slowly while
        decay and tenure crowd-out keep subtracting. Independence erodes as
        livelihood shifts onto the generic membership benefit.

        FIXED POINT. With a constant renewal floor the tie update is
            do/dt = renewal - decay
                  = (ec_tie_renewal_base + ec_tie_renewal*o)
                    - (ec_tie_decay*o + crowdout_term)
                  = (ec_tie_renewal_base - crowdout_term)
                    + (ec_tie_renewal - ec_tie_decay)*o
        Setting do/dt = 0 gives the interior equilibrium
            o* = (ec_tie_renewal_base - crowdout_term) / (ec_tie_decay - ec_tie_renewal)
        where crowdout_term = ec_tenure_crowdout * min(tenure/100, 1). Because
        ec_tie_renewal < ec_tie_decay the coefficient on o is negative, so o* is
        an ATTRACTING fixed point (not an absorbing zero). Its sign is the whole
        story: closure (o* <= 0, ties driven to the clip at 0) requires
            crowdout_term > ec_tie_renewal_base,
        i.e. tenure crowd-out must exceed the base renewal floor. When crowd-out
        stays below the floor, o* is a positive interior value and exit capacity
        settles there rather than closing -- a THRESHOLD in crowd-out, not a
        ratchet. ec_tie_renewal < ec_tie_decay remains required for stability.

        ECON CHANNEL FIXED POINT (now PROPERLY mirrors the tie channel: decay is
        econ-proportional, so the coefficient on ei is negative and ei* attracts).
        The update is
            dei/dt = econ_recovery - econ_decay
                   = ec_econ_recovery_base
                     - ec_dependence_rate*mu*ei
                   = ec_econ_recovery_base - (ec_dependence_rate*mu)*ei
        Setting dei/dt = 0 gives the interior equilibrium
            ei* = ec_econ_recovery_base / (ec_dependence_rate*mu)
        The coefficient on ei is -(ec_dependence_rate*mu) < 0, so ei* is an
        ATTRACTING fixed point. Independence closes (ei* -> 0) as the dependence
        pressure ec_dependence_rate*mu grows; ei* falls below 1 (interior, a live
        channel) once ec_dependence_rate*mu > ec_econ_recovery_base, i.e.
        mu > ec_econ_recovery_base/ec_dependence_rate (= 0.4 at defaults for an
        agent with ec_hetero=1). With the default mu=0 the decay is zero and
        independence recovers to the clip at 1 for every agent -- so the econ
        channel is INERT at mu=0 and identical to the pre-fix form there (both
        drive ei -> 1). It only becomes live, and heterogeneous via the per-agent
        ec_hetero factor on ec_econ_recovery_base, once mu > 0. NOTE: the old
        ec_econ_recovery (tie-of-ei recovery rate) is no longer used; recovery is
        the flat, hetero-scaled floor econ_recovery_base.
        """
        p = self.params
        if p.exit_capacity_mode != "endogenous":
            return

        # generic membership benefit: paid to every member alike, so it carries
        # no information about enforcement, service or patronage rank.
        mu_membership_reward_scaled = float(np.clip(p.mu_membership_reward, 0.0, 1.0))

        for a in self.people.values():
            if a.exited:
                continue
            a.tenure += 1
            # per-agent heterogeneity: scale BOTH recovery floors by the agent's factor
            tie_renewal_base = p.ec_tie_renewal_base * a.ec_hetero
            econ_recovery_base = p.ec_econ_recovery_base * a.ec_hetero
            # tie channel: constant floor + tie-proportional term -> interior o*
            renewal = tie_renewal_base + p.ec_tie_renewal * a.outside_ties
            decay = p.ec_tie_decay * a.outside_ties + p.ec_tenure_crowdout * min(a.tenure / 100.0, 1.0)
            a.outside_ties = float(np.clip(a.outside_ties + renewal - decay, 0.0, 1.0))
            # econ channel: constant recovery floor vs econ-PROPORTIONAL decay.
            # decay proportional to ei gives a NEGATIVE coefficient on ei, so the
            # fixed point attracts (properly mirroring the tie channel). the old
            # form (recovery proportional to ei, constant decay) was repelling.
            econ_recovery = econ_recovery_base
            econ_decay = p.ec_dependence_rate * mu_membership_reward_scaled * a.econ_independence
            a.econ_independence = float(
                np.clip(a.econ_independence + econ_recovery - econ_decay, 0.0, 1.0)
            )
            a.exit_capacity = 0.5 * a.outside_ties + 0.5 * a.econ_independence

    def _attach_node(self, node_id: int):
        """attach a replacement agent's node with the same generative rule used
        to build the initial graph in _make_graph.

        the dead member's edges are cleared first: a replacement enters the
        congregation as a fresh node rather than inheriting a dead person's
        social position. population size and node count stay constant.
        """
        p = self.params
        rng = self.rng
        G = self.G
        for j in list(G.neighbors(node_id)):
            G.remove_edge(node_id, int(j))
        others = [i for i in G.nodes if i != node_id]
        if not others:
            return

        if p.graph == "scale_free":
            # barabasi-albert preferential attachment, same m as _make_graph
            m = max(2, int(round(math.log(p.n + 1))))
            m = min(m, len(others))
            w = np.array([G.degree(i) + 1.0 for i in others], dtype=float)
            w = w / w.sum()
            picks = rng.choice(len(others), size=m, replace=False, p=w)
            for idx in picks:
                G.add_edge(node_id, others[int(idx)])
        elif p.graph == "small_world":
            # watts-strogatz ring lattice + 0.10 rewiring, same k as _make_graph
            k = max(4, int(round(math.sqrt(p.n))))
            if k % 2 == 1:
                k += 1
            for d in range(1, k // 2 + 1):
                for nb in ((node_id + d) % p.n, (node_id - d) % p.n):
                    if nb == node_id:
                        continue
                    if rng.random() < 0.10:
                        cand = int(rng.integers(0, p.n))
                        if cand != node_id:
                            G.add_edge(node_id, cand)
                    else:
                        G.add_edge(node_id, int(nb))
        else:  # erdos_renyi
            p_edge = min(0.05, 8.0 / p.n)
            for j in others:
                if rng.random() < p_edge:
                    G.add_edge(node_id, int(j))

    def _turnover(self):
        """v3.3: cohort turnover at constant population size.

        each active agent dies with probability death_hazard and is replaced in
        the same node slot. replacements draw traits from the same initial
        distributions as the founding population (Person.__init__) and are
        re-attached to the network by the same generative rule.

        born_inside_frac controls the cohort composition, which is the causal
        lever this subsystem exists to expose: members BORN into the group start
        with no outside ties and only partial economic independence, so a
        congregation that reproduces itself internally loses aggregate exit
        capacity even with no enforcement at all. born_inside_frac=0 (all
        joiners from outside) is the negative control.
        """
        p = self.params
        self.n_deaths_step = 0
        if p.turnover_mode != "on":
            return
        rng = self.rng
        for i, old in list(self.people.items()):
            if old.exited:
                continue
            if rng.random() >= p.death_hazard:
                continue

            born_inside = bool(rng.random() < p.born_inside_frac)
            new = Person(i, self)  # fresh trait draws from the initial distributions
            if born_inside:
                # raised inside: no outside ties, livelihood already half-tied
                # to the group. note this is a birth condition, not a
                # consequence of anything the enforcers did.
                new.outside_ties = 0.0
                new.econ_independence = 0.5
                new.born_inside = True
            else:
                # joiner from outside: arrives with a full outside-tie stock
                new.outside_ties = float(np.clip(p.ec_outside_ties_init, 0.0, 1.0))
                new.econ_independence = 1.0
                new.born_inside = False
            new.tenure = 0
            new.exit_capacity = 0.5 * new.outside_ties + 0.5 * new.econ_independence

            try:
                old.remove()  # drop the dead agent from mesa's registry
            except Exception:
                pass
            self.people[i] = new
            self._attach_node(i)
            self.n_deaths_step += 1

    def _update_cadre_assignments(self):
        p = self.params
        active = [a for a in self.people.values() if not a.exited]
        for a in self.people.values():
            a.is_enforcer = False
            a.cadre_fallback = False
        self.n_cadre_fallback_step = 0
        if not active:
            return

        quota = int(round(p.enforcer_quota_frac * len(active)))
        if p.enforcer_quota_frac > 0.0:
            quota = max(1, quota)
        quota = min(len(active), quota)
        if quota <= 0:
            return

        def suitability(agent: Person) -> float:
            return 0.6 * agent.cap + 0.3 * agent.L + 0.1 * (agent.r * agent.b)

        eligible = [a for a in active if a.cap >= p.cap_to_enforcer]
        if len(eligible) >= quota:
            chosen = sorted(eligible, key=suitability, reverse=True)[:quota]
        else:
            shortfall = quota - len(eligible)
            in_eligible = {id(a) for a in eligible}
            non_eligible = [a for a in active if id(a) not in in_eligible]
            fill = sorted(non_eligible, key=suitability, reverse=True)[:shortfall]
            for a in fill:
                a.cadre_fallback = True
            self.n_cadre_fallback_step = len(fill)
            chosen = list(eligible) + fill
        for a in chosen:
            a.is_enforcer = True

    def _distribute_patronage(self):
        if self.budget <= 0.0:
            return
        enforcers = [a for a in self.people.values() if (not a.exited and a.is_enforcer)]
        if not enforcers:
            return
        total_service = float(sum(max(0.0, a.service) for a in enforcers))
        if total_service <= 0.0:
            share = self.budget / len(enforcers)
            for a in enforcers:
                a.u += share
            return
        for a in enforcers:
            a.u += self.budget * (max(0.0, a.service) / total_service)

    def _update_controller(self):
        p = self.params
        if self.t in self.shock_schedule:
            self.threat += p.shock_strength
        else:
            self.threat *= max(0.0, 1.0 - p.relax_rate)
        self.A = float(np.clip(1.0 - math.exp(-p.A_gain_threat * self.threat), 0.0, 1.0))
        self.budget = float(max(0.0, p.budget_base + p.budget_threat_gain * self.threat))

        p.pi_reward = self.baseline_pi + p.tighten_gain_pi * self.threat
        p.lam_punish = self.baseline_lam + p.tighten_gain_lam * self.threat
        p.d0 = float(np.clip(self.baseline_d0 - p.tighten_gain_d0 * self.threat, 0.0, 1.0))

        if not p.fixed_y0:
            y_enforcers = [a.y for a in self.people.values() if (not a.exited and a.fundamentalism_index() > p.F_star)]
            if y_enforcers:
                y_target = float(np.mean(y_enforcers))
                self.y0 = float(np.clip(0.95 * self.y0 + 0.05 * y_target, 0.0, 1.0))

    def _update_delta_drift(self):
        mode = getattr(self.params, "delta_mode", "legacy")
        if mode == "exogenous":
            return  # delta held fixed at its baseline; set exogenously, no drift
        eta = float(np.clip(self.params.eta_delta_drift, 0.0, 0.5))
        if eta <= 0.0:
            return
        if self.punish_intensity_step < float(np.clip(self.params.punish_floor, 0.0, 1.0)):
            return
        eps = 1e-9
        if mode == "decoupled":
            cap = float(np.clip(self.params.delta_cap, 0.0, 1.0))
            kappa = float(self.params.delta_kappa)
            delta_target = float(min(cap, self.delta_baseline + kappa * self.punish_intensity_step))
        else:  # legacy
            enforcer_share = float(self.enforcer_punish_events_step / max(self.punish_events_step, eps))
            enforcer_share = float(np.clip(enforcer_share, 0.0, 1.0))
            delta_target = float(min(1.0, self.delta_baseline + enforcer_share))
        self.current_delta = float(np.clip(self.current_delta + eta * (delta_target - self.current_delta), 0.0, 1.0))

    def metrics(self) -> Dict[str, Any]:
        ps = self.params
        agents_all = list(self.people.values())
        active_agents = [a for a in agents_all if not a.exited]

        xs_all = np.array([a.x for a in agents_all], dtype=float)
        ys_all = np.array([a.y for a in agents_all], dtype=float)
        Ls = np.array([a.L for a in agents_all], dtype=float)
        caps = np.array([a.cap for a in agents_all], dtype=float)
        services = np.array([a.service for a in agents_all], dtype=float)
        ss_all = np.array([a.s for a in agents_all], dtype=float)
        rs_all = np.array([a.r for a in agents_all], dtype=float)
        bs_all = np.array([a.b for a in agents_all], dtype=float)
        Fs_all = rs_all * bs_all
        punished = np.array([a.punished for a in agents_all], dtype=float)
        exited = np.array([a.exited for a in agents_all], dtype=bool)
        exit_intent = np.array([a.exit_intent for a in agents_all], dtype=float)

        if active_agents:
            xs = np.array([a.x for a in active_agents], dtype=float)
            ys = np.array([a.y for a in active_agents], dtype=float)
            ss = np.array([a.s for a in active_agents], dtype=float)
            rs = np.array([a.r for a in active_agents], dtype=float)
            bs = np.array([a.b for a in active_agents], dtype=float)
            Fs = rs * bs
            mean_x = float(xs.mean())
            mean_y = float(ys.mean())
            mean_epc = float(ss.mean())
            mean_r = float(rs.mean())
            mean_b = float(bs.mean())
            fund_prevalence = float((Fs > ps.F_star).mean())
        else:
            mean_x = float("nan")
            mean_y = float("nan")
            mean_epc = float("nan")
            mean_r = float("nan")
            mean_b = float("nan")
            fund_prevalence = float("nan")
        active_ids = [i for i, a in self.people.items() if not a.exited]
        if active_ids:
            active_deg = [sum(1 for j in self.G.neighbors(i) if not self.people[j].exited) for i in active_ids]
            mean_degree_active = float(np.mean(active_deg))
            p_opp_mean = float(np.mean([self.people[i].last_p_opp for i in active_ids]))
            stay_value = float(np.mean([self.people[i].last_membership_gain for i in active_ids]))
            enforcer_frac = float(np.mean([self.people[i].is_enforcer for i in active_ids]))
            exit_attempt_rate = float(
                np.mean([self.people[i].exit_intent >= self.params.exit_commit_steps for i in active_ids])
            )
            # v3.3 exit-capacity block, active agents only
            mean_exit_capacity = float(np.mean([self.people[i].exit_capacity for i in active_ids]))
            mean_outside_ties = float(np.mean([self.people[i].outside_ties for i in active_ids]))
            mean_econ_independence = float(np.mean([self.people[i].econ_independence for i in active_ids]))
            frac_born_inside = float(np.mean([self.people[i].born_inside for i in active_ids]))
            mean_tenure = float(np.mean([self.people[i].tenure for i in active_ids]))
        else:
            mean_degree_active = 0.0
            p_opp_mean = 0.0
            stay_value = 0.0
            enforcer_frac = 0.0
            exit_attempt_rate = 0.0
            mean_exit_capacity = 0.0
            mean_outside_ties = 0.0
            mean_econ_independence = 0.0
            frac_born_inside = 0.0
            mean_tenure = 0.0
        return dict(
            t=self.t,
            mean_x=mean_x,
            mean_y=mean_y,
            mean_x_all=float(xs_all.mean()),
            mean_y_all=float(ys_all.mean()),
            mean_L=float(Ls.mean()),
            y0=float(self.y0),
            mean_epc=mean_epc,
            mean_r=mean_r,
            mean_b=mean_b,
            fund_prevalence=fund_prevalence,
            mean_epc_all=float(ss_all.mean()),
            mean_r_all=float(rs_all.mean()),
            mean_b_all=float(bs_all.mean()),
            fund_prevalence_all=float((Fs_all > ps.F_star).mean()),
            # v2.7.1: denominator restricted to active (non-exited) agents
            punish_rate=float((punished[~exited] > 0).mean()) if (~exited).any() else 0.0,
            mean_punished=float(punished.mean()),
            exit_rate=float(exited.mean()),
            mean_exit_intent=float(exit_intent.mean()),
            exit_attempt_rate=exit_attempt_rate,
            exit_success_rate=float(self.exit_successes_step / max(1, self.params.n)),
            p_opp_mean=p_opp_mean,
            stay_value=stay_value,
            mean_degree_active=mean_degree_active,
            threat=float(self.threat),
            A=float(self.A),
            budget=float(self.budget),
            enforcer_frac=enforcer_frac,
            n_cadre_fallback=int(self.n_cadre_fallback_step),
            cap_mean=float(caps.mean()),
            cap_p90=float(np.quantile(caps, 0.90)),
            service_mean=float(services.mean()),
            service_p90=float(np.quantile(services, 0.90)),
            monopoly_on=float(1.0 if self.monopoly_on else 0.0),
            enforcer_punish_share_step=float(
                self.enforcer_punish_events_step / self.punish_events_step
                if self.punish_events_step > 0
                else 0.0
            ),
            alpha_punish_revalue=float(ps.alpha_punish_revalue),
            delta_outside_degrade=float(ps.delta_outside_degrade),
            mu_membership_reward=float(ps.mu_membership_reward),
            current_delta=float(self.current_delta),
            eta_delta_drift=float(ps.eta_delta_drift),
            punish_floor=float(ps.punish_floor),
            punish_intensity_step=float(self.punish_intensity_step),
            pi_reward=float(ps.pi_reward),
            lam_punish=float(ps.lam_punish),
            # v3.3 exit-capacity + turnover diagnostics (active agents only)
            mean_exit_capacity=mean_exit_capacity,
            mean_outside_ties=mean_outside_ties,
            mean_econ_independence=mean_econ_independence,
            frac_born_inside=frac_born_inside,
            mean_tenure=mean_tenure,
            n_deaths_step=int(self.n_deaths_step),
        )

    def agent_summary(self, include_betweenness: bool = False) -> pd.DataFrame:
        degree = dict(self.G.degree())
        if include_betweenness:
            betweenness = nx.betweenness_centrality(self.G, normalized=True)
        else:
            betweenness = {i: np.nan for i in self.people}

        rows = []
        for i, agent in self.people.items():
            rows.append(
                dict(
                    agent_id=i,
                    punish_issued=int(agent.punish_issued),
                    punished_received=int(agent.punished_total),
                    final_r=float(agent.r),
                    final_b=float(agent.b),
                    final_x=float(agent.x),
                    y=float(agent.y),
                    L=float(agent.L),
                    cap=float(agent.cap),
                    service=float(agent.service),
                    is_enforcer=bool(agent.is_enforcer),
                    cadre_fallback=bool(agent.cadre_fallback),
                    exited=bool(agent.exited),
                    exit_time=int(agent.exit_time),
                    exit_intent=int(agent.exit_intent),
                    disengaged=bool(agent.disengaged),
                    exit_cost_eff_last=float(agent.exit_cost_eff_last),
                    degree=int(degree.get(i, 0)),
                    degree_at_end=int(degree.get(i, 0)),
                    betweenness=float(betweenness.get(i, np.nan)),
                )
            )
        return pd.DataFrame(rows)

    def agent_final(self) -> pd.DataFrame:
        """v3.3: minimal per-agent end-state table for the anti-circularity test.

        pairs each agent's final exit capacity with the enforcement quantities
        it is forbidden to depend on. if the invariant holds, exit_capacity
        should be uncorrelated with punishment_received, punishment_delivered
        and is_enforcer. the capacity-side covariates (tenure, born_inside,
        exited) are carried along so the correlation can be conditioned or
        restricted to active members during analysis.
        """
        rows = []
        for i, a in self.people.items():
            rows.append(
                dict(
                    agent_id=i,
                    exit_capacity=float(a.exit_capacity),
                    outside_ties=float(a.outside_ties),
                    econ_independence=float(a.econ_independence),
                    tenure=int(a.tenure),
                    born_inside=bool(a.born_inside),
                    punishment_received=int(a.punished_total),
                    punishment_delivered=int(a.punish_issued),
                    is_enforcer=bool(a.is_enforcer),
                    exited=bool(a.exited),
                )
            )
        return pd.DataFrame(rows)


def draw_frame(model: ReligionABM, pos: Dict[int, Any], out_png: str):
    p = model.params
    agents = model.people
    sizes = [80 + 520 * agents[i].fundamentalism_index() for i in agents]

    fig = plt.figure(figsize=(7.5, 7.5), dpi=140)
    ax = fig.add_subplot(111)
    ax.set_axis_off()

    nx.draw_networkx_edges(model.G, pos, ax=ax, width=0.4, alpha=0.25)
    nx.draw_networkx_nodes(model.G, pos, ax=ax, node_size=sizes, alpha=0.35, linewidths=0.0)

    m = model.metrics()
    ax.set_title(
        f"t={m['t']} EPC={m['mean_epc']:.2f} ITC(x)={m['mean_x']:.2f} "
        f"F_prev={m['fund_prevalence']:.2f} punish={m['punish_rate']:.2f}\n"
        f"sigma={p.sigma:.2f} v={p.v_obs:.2f} a={p.a_obs:.2f} "
        f"pi={p.pi_reward:.2f} lam={p.lam_punish:.2f} graph={p.graph}",
        fontsize=9
    )

    fig.tight_layout()
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)


def make_movie(frames_dir: str, out_mp4: str, fps: int = 20):
    os.makedirs(os.path.dirname(out_mp4), exist_ok=True)
    frame_files = sorted([os.path.join(frames_dir, f) for f in os.listdir(frames_dir) if f.endswith(".png")])
    if not frame_files:
        raise RuntimeError(f"No frames found in {frames_dir}")

    # Prefer bundled ffmpeg from imageio-ffmpeg; can be overridden via IMAGEIO_FFMPEG_EXE.
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    os.environ.setdefault("IMAGEIO_FFMPEG_EXE", ffmpeg_exe)
    writer = imageio.get_writer(out_mp4, fps=fps, codec="libx264")

    try:
        for fn in tqdm(frame_files, desc="Encoding MP4"):
            writer.append_data(imageio.imread(fn))
    finally:
        writer.close()


def parse_int_list(text: str) -> Tuple[int, ...]:
    if text is None:
        return tuple()
    text = text.strip()
    if not text:
        return tuple()
    values = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        values.append(int(part))
    return tuple(values)


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=str, default="runs/demo")
    ap.add_argument("--steps", type=int, default=350)
    ap.add_argument("--fps", type=int, default=20)
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--graph", type=str, default="scale_free", choices=["scale_free", "small_world", "erdos_renyi"])
    ap.add_argument("--seed", type=int, default=1)

    ap.add_argument("--sigma", type=float, default=0.75)
    ap.add_argument("--v_obs", type=float, default=0.90)
    ap.add_argument("--a_obs", type=float, default=0.05)
    ap.add_argument("--h_obs", type=float, default=0.15)
    ap.add_argument("--w_heresy", type=float, default=0.6)
    ap.add_argument("--d0", type=float, default=0.18)

    ap.add_argument("--pi_reward", type=float, default=0.22)
    ap.add_argument("--kappa_cost", type=float, default=0.08)
    ap.add_argument("--lam_punish", type=float, default=0.25)
    ap.add_argument("--backlash_base", type=float, default=0.25)
    ap.add_argument("--backlash_cost", type=float, default=0.30)
    ap.add_argument("--backlash_sensitivity", type=float, default=1.0)
    ap.add_argument("--exit_cost", type=float, default=0.40)
    ap.add_argument("--exit_threshold", type=float, default=-1.0)
    ap.add_argument("--exit_prob_slope", type=float, default=3.0)
    ap.add_argument("--exit_rewire_fraction", type=float, default=0.90)
    ap.add_argument("--exit_degree_coeff", type=float, default=0.03)
    ap.add_argument("--exit_epc_lockin_coeff", type=float, default=0.25)
    ap.add_argument("--exit_min_cost", type=float, default=0.0)
    ap.add_argument("--exit_opportunity_base", type=float, default=0.6)
    ap.add_argument("--exit_opportunity_deg_coeff", type=float, default=0.03)
    ap.add_argument("--exit_opportunity_threat_coeff", type=float, default=1.5)
    ap.add_argument("--exit_block_exponent", type=float, default=2.5)
    ap.add_argument("--exit_block_floor", type=float, default=0.02)
    ap.add_argument("--exit_commit_steps", type=int, default=8)
    ap.add_argument("--exit_cooldown", type=int, default=0)
    ap.add_argument("--alpha_punish_revalue", type=float, default=0.0)
    ap.add_argument("--delta_outside_degrade", type=float, default=0.0)
    ap.add_argument("--mu_membership_reward", type=float, default=0.0)
    ap.add_argument("--eta_delta_drift", type=float, default=0.0)
    ap.add_argument("--punish_floor", type=float, default=0.08)
    ap.add_argument("--delta_mode", type=str, default="legacy", choices=["legacy", "decoupled", "exogenous"])
    ap.add_argument("--delta_cap", type=float, default=0.85)
    ap.add_argument("--delta_kappa", type=float, default=3.0)
    # v3.3 endogenous exit capacity
    ap.add_argument("--exit_capacity_mode", type=str, default="off", choices=["off", "endogenous"],
                    help="off reproduces v2.7 exactly; endogenous replaces global delta with per-agent e_i.")
    ap.add_argument("--ec_outside_ties_init", type=float, default=1.0)
    ap.add_argument("--ec_init_random", dest="ec_init_random", action="store_true", default=True,
                    help="draw per-agent outside_ties, econ_independence ~ Beta(2,2) at init (default on)")
    ap.add_argument("--no_ec_init_random", dest="ec_init_random", action="store_false",
                    help="homogeneous init instead (founders at ec_outside_ties_init / 1.0)")
    ap.add_argument("--ec_tie_decay", type=float, default=0.01)
    ap.add_argument("--ec_tie_renewal_base", type=float, default=0.006)
    ap.add_argument("--ec_tie_renewal", type=float, default=0.004)
    ap.add_argument("--ec_tenure_crowdout", type=float, default=0.002)
    ap.add_argument("--ec_econ_recovery_base", type=float, default=0.004)
    ap.add_argument("--ec_econ_recovery", type=float, default=0.002)
    ap.add_argument("--ec_hetero_sd", type=float, default=0.25)
    ap.add_argument("--panel", dest="emit_panel", action="store_true", default=False,
                    help="emit per-step per-agent panel.csv for the directional anti-circularity test")
    ap.add_argument("--ec_dependence_rate", type=float, default=0.01)
    ap.add_argument("--lambda_exit_opportunity", type=float, default=1.0)
    ap.add_argument("--lambda_exit_willingness", type=float, default=1.0)
    # v3.3 cohort turnover
    ap.add_argument("--turnover_mode", type=str, default="off", choices=["off", "on"])
    ap.add_argument("--death_hazard", type=float, default=0.002)
    ap.add_argument("--born_inside_frac", type=float, default=0.8)
    ap.add_argument("--membership_benefit", type=float, default=0.03)
    ap.add_argument("--membership_benefit_sigma", type=float, default=0.08)
    ap.add_argument("--membership_benefit_threat", type=float, default=0.10)
    ap.add_argument("--L_alpha", type=float, default=1.5)
    ap.add_argument("--L_beta", type=float, default=4.5)
    ap.add_argument("--theta_L_gain", type=float, default=0.12)
    ap.add_argument("--d0_L_gain", type=float, default=0.08)
    ap.add_argument("--A_gain_threat", type=float, default=2.0)
    ap.add_argument("--A_enforcer_monopoly", type=float, default=0.35)
    ap.add_argument("--budget_base", type=float, default=0.15)
    ap.add_argument("--budget_threat_gain", type=float, default=0.60)
    ap.add_argument("--enforcer_quota_frac", type=float, default=0.08)
    ap.add_argument("--cap_decay", type=float, default=0.005)
    ap.add_argument("--cap_gain_per_punish", type=float, default=0.15)
    ap.add_argument("--cap_to_enforcer", type=float, default=0.25)
    ap.add_argument("--cap_max", type=float, default=2.0)
    ap.add_argument("--service_decay", type=float, default=0.02)
    ap.add_argument("--non_enforcer_punish_mult", type=float, default=0.25)
    ap.add_argument("--non_enforcer_punish_eps", type=float, default=0.02)
    ap.add_argument("--enforcer_punish_mult", type=float, default=1.5)
    ap.add_argument("--kappa_cap_discount", type=float, default=0.20)
    ap.add_argument("--enforcer_backlash_mult", type=float, default=0.25)
    ap.add_argument("--enforcer_kappa_mult", type=float, default=0.30)
    ap.add_argument("--disable_exit", action="store_true")
    ap.add_argument("--shock_schedule", type=str, default="100,220,320")
    ap.add_argument("--shock_strength", type=float, default=0.25)
    ap.add_argument("--tighten_gain_pi", type=float, default=0.20)
    ap.add_argument("--tighten_gain_lam", type=float, default=0.20)
    ap.add_argument("--tighten_gain_d0", type=float, default=0.08)
    ap.add_argument("--relax_rate", type=float, default=0.03)
    ap.add_argument("--baseline_pi", type=float, default=-1.0)
    ap.add_argument("--baseline_lam", type=float, default=-1.0)
    ap.add_argument("--baseline_d0", type=float, default=-1.0)
    ap.add_argument("--fixed_y0", action="store_true", help="Disable orthodoxy drift; keep y0 fixed at initialization.")
    ap.add_argument("--no_movie", action="store_true", help="Skip frame rendering and MP4 encoding.")
    ap.add_argument("--compute_betweenness", action="store_true", help="Include network betweenness centrality in agent_summary.csv.")
    return ap.parse_args()


def main():
    args = parse_args()
    params = Params(
        n=args.n, graph=args.graph, seed=args.seed,
        sigma=args.sigma, v_obs=args.v_obs, a_obs=args.a_obs, h_obs=args.h_obs,
        w_heresy=args.w_heresy, d0=args.d0,
        pi_reward=args.pi_reward,
        kappa_cost=args.kappa_cost,
        lam_punish=args.lam_punish,
        backlash_base=args.backlash_base,
        backlash_cost=args.backlash_cost,
        backlash_sensitivity=args.backlash_sensitivity,
        exit_cost=args.exit_cost,
        exit_threshold=args.exit_threshold,
        exit_prob_slope=args.exit_prob_slope,
        exit_rewire_fraction=args.exit_rewire_fraction,
        exit_degree_coeff=args.exit_degree_coeff,
        exit_epc_lockin_coeff=args.exit_epc_lockin_coeff,
        exit_min_cost=args.exit_min_cost,
        exit_opportunity_base=args.exit_opportunity_base,
        exit_opportunity_deg_coeff=args.exit_opportunity_deg_coeff,
        exit_opportunity_threat_coeff=args.exit_opportunity_threat_coeff,
        exit_block_exponent=args.exit_block_exponent,
        exit_block_floor=args.exit_block_floor,
        exit_commit_steps=args.exit_commit_steps,
        exit_cooldown=args.exit_cooldown,
        alpha_punish_revalue=args.alpha_punish_revalue,
        delta_outside_degrade=args.delta_outside_degrade,
        mu_membership_reward=args.mu_membership_reward,
        eta_delta_drift=args.eta_delta_drift,
        punish_floor=args.punish_floor,
        delta_mode=args.delta_mode,
        delta_cap=args.delta_cap,
        delta_kappa=args.delta_kappa,
        exit_capacity_mode=args.exit_capacity_mode,
        ec_outside_ties_init=args.ec_outside_ties_init,
        ec_init_random=args.ec_init_random,
        ec_tie_decay=args.ec_tie_decay,
        ec_tie_renewal_base=args.ec_tie_renewal_base,
        ec_tie_renewal=args.ec_tie_renewal,
        ec_tenure_crowdout=args.ec_tenure_crowdout,
        ec_econ_recovery_base=args.ec_econ_recovery_base,
        ec_econ_recovery=args.ec_econ_recovery,
        ec_hetero_sd=args.ec_hetero_sd,
        emit_panel=args.emit_panel,
        ec_dependence_rate=args.ec_dependence_rate,
        lambda_exit_opportunity=args.lambda_exit_opportunity,
        lambda_exit_willingness=args.lambda_exit_willingness,
        turnover_mode=args.turnover_mode,
        death_hazard=args.death_hazard,
        born_inside_frac=args.born_inside_frac,
        membership_benefit=args.membership_benefit,
        membership_benefit_sigma=args.membership_benefit_sigma,
        membership_benefit_threat=args.membership_benefit_threat,
        L_alpha=args.L_alpha,
        L_beta=args.L_beta,
        theta_L_gain=args.theta_L_gain,
        d0_L_gain=args.d0_L_gain,
        A_gain_threat=args.A_gain_threat,
        A_enforcer_monopoly=args.A_enforcer_monopoly,
        budget_base=args.budget_base,
        budget_threat_gain=args.budget_threat_gain,
        enforcer_quota_frac=args.enforcer_quota_frac,
        cap_decay=args.cap_decay,
        cap_gain_per_punish=args.cap_gain_per_punish,
        cap_to_enforcer=args.cap_to_enforcer,
        cap_max=args.cap_max,
        service_decay=args.service_decay,
        non_enforcer_punish_mult=args.non_enforcer_punish_mult,
        non_enforcer_punish_eps=args.non_enforcer_punish_eps,
        enforcer_punish_mult=args.enforcer_punish_mult,
        kappa_cap_discount=args.kappa_cap_discount,
        enforcer_backlash_mult=args.enforcer_backlash_mult,
        enforcer_kappa_mult=args.enforcer_kappa_mult,
        enable_exit=not args.disable_exit,
        shock_schedule=parse_int_list(args.shock_schedule),
        shock_strength=args.shock_strength,
        tighten_gain_pi=args.tighten_gain_pi,
        tighten_gain_lam=args.tighten_gain_lam,
        tighten_gain_d0=args.tighten_gain_d0,
        relax_rate=args.relax_rate,
        baseline_pi=args.baseline_pi,
        baseline_lam=args.baseline_lam,
        baseline_d0=args.baseline_d0,
        fixed_y0=args.fixed_y0,
    )

    outdir = args.outdir
    os.makedirs(outdir, exist_ok=True)

    model = ReligionABM(params)

    frames_dir = os.path.join(outdir, "frames")
    pos = None
    if not args.no_movie:
        os.makedirs(frames_dir, exist_ok=True)
        # Deterministic layout when seed fixed.
        pos = nx.spring_layout(model.G, seed=int(params.seed), iterations=80)

    rows = []
    # terminal-window exit metric: snapshot the agents active (not exited) at the
    # metrics row for step 349, then measure how many of THOSE exit by the end.
    # captures late-window exit closure that the cumulative rate washes out.
    last100_anchor = max(0, args.steps - 100 - 1)  # step 349 when steps=450
    active_at_anchor = None
    for t in tqdm(range(args.steps), desc="Simulating"):
        if not args.no_movie:
            draw_frame(model, pos, os.path.join(frames_dir, f"frame_{t:05d}.png"))
        rows.append(model.metrics())
        if t == last100_anchor:
            active_at_anchor = {i for i, a in model.people.items() if not a.exited}
        model.step()

    # cumulative exit rate = fraction of all agents currently exited
    exited_end = {i for i, a in model.people.items() if a.exited}
    cumulative_exit_rate = len(exited_end) / max(1, len(model.people))
    # exit_rate_last100 = of agents active at the anchor and still present, the
    # fraction now in an exited state. under turnover a slot may have been
    # refilled by death (not exit); those simply read as non-exited here.
    if active_at_anchor:
        present = [i for i in active_at_anchor if i in model.people]
        n_present = len(present)
        exit_rate_last100 = (
            sum(1 for i in present if model.people[i].exited) / n_present
            if n_present else float("nan")
        )
    else:
        n_present = 0
        exit_rate_last100 = float("nan")

    df_metrics = pd.DataFrame(rows)
    # broadcast the terminal scalars as constant columns so metrics.csv carries them too
    df_metrics["exit_rate_last100"] = exit_rate_last100
    df_metrics["cumulative_exit_rate"] = cumulative_exit_rate
    df_metrics.to_csv(os.path.join(outdir, "metrics.csv"), index=False)

    # one-row run_summary.csv with the headline terminal statistics
    enf_share_final = float(df_metrics["enforcer_punish_share_step"].tail(50).median())
    run_summary = pd.DataFrame([dict(
        seed=int(params.seed),
        steps=int(args.steps),
        sigma=float(params.sigma),
        pi_reward=float(params.pi_reward),
        mu_membership_reward=float(params.mu_membership_reward),
        exit_capacity_mode=str(params.exit_capacity_mode),
        turnover_mode=str(params.turnover_mode),
        born_inside_frac=float(params.born_inside_frac),
        ec_tie_renewal_base=float(params.ec_tie_renewal_base),
        ec_tie_renewal=float(params.ec_tie_renewal),
        ec_tie_decay=float(params.ec_tie_decay),
        ec_tenure_crowdout=float(params.ec_tenure_crowdout),
        cumulative_exit_rate=cumulative_exit_rate,
        exit_rate_last100=exit_rate_last100,
        n_active_at_anchor=int(len(active_at_anchor) if active_at_anchor else 0),
        n_present_at_end=int(n_present),
        mean_exit_capacity_final=float(df_metrics["mean_exit_capacity"].iloc[-1]),
        enforcer_punish_share_final=enf_share_final,
    )])
    run_summary.to_csv(os.path.join(outdir, "run_summary.csv"), index=False)
    model.agent_summary(include_betweenness=args.compute_betweenness).to_csv(
        os.path.join(outdir, "agent_summary.csv"), index=False
    )
    # v3.3: per-agent end state for the anti-circularity test
    model.agent_final().to_csv(os.path.join(outdir, "agent_final.csv"), index=False)
    # v3.3: per-step per-agent panel for the directional (lagged) anti-circularity test
    if args.emit_panel:
        pd.DataFrame(model._panel_rows).to_csv(os.path.join(outdir, "panel.csv"), index=False)
    if not args.no_movie:
        make_movie(frames_dir, os.path.join(outdir, "movie.mp4"), fps=args.fps)

    if args.no_movie:
        print(f"Done.\nMetrics: {os.path.join(outdir, 'metrics.csv')}")
    else:
        print(f"Done.\nMP4: {os.path.join(outdir, 'movie.mp4')}\nMetrics: {os.path.join(outdir, 'metrics.csv')}")


if __name__ == "__main__":
    main()
