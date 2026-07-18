#!/usr/bin/env python3
"""Consolidated canonical code-geometry ABM (v3.1).

Unifies the three enforcement-concentration mechanisms that were previously
split across separate experimental model files, and adds the "foolproof"
guardrails that close this project's documented failure modes.

three mechanism legs (all validated, inherited verbatim from v2.9 dynamics):
  1. selective enforcement benefit (patronage): punishing builds capital, capital
     compounds, patronage is distributed to enforcers -> a minority concentrates
     enforcement. this is the CORE engine (cap_gain_per_punish, _distribute_patronage).
  2. endogenous exit sealing (current_delta): the perceived outside option degrades,
     trapping members (delta_outside_degrade, eta_delta_drift).
  3. self-policing / acquiescence (q): trapped members functionally support the
     apparatus without believing (omega_*, gamma_q, acquiescence_threshold).

ablation control (NOT a driver): mu_membership_reward is a FLAT membership perk.
  prior sweeps showed a uniform benefit-of-staying does not by itself produce
  durable capture -- only selective (enforcement-conditional) benefit does.
  it defaults to 0.0 and exists here only so the ablation can be reproduced.

foolproof guardrails (each closes a known project failure):
  - single classifier: outcome regimes come from regime_classifier.classify(),
    never an inline rule. see src/regime_classifier.py.
  - active-rate baked in: punish_rate is already restricted to non-exited agents
    (inherited from v2.7.1), so the historical active-rate confound cannot recur.
  - self-policing counted: enforcement_pressure = overt punishment + latent
    deterrence (acquiescence), so a fear-compliant population is never mislabeled
    QUIET. the run summary reports BOTH the overt regime and the acquiescence-aware
    regime and flags any contradiction between them.

the dynamics are exactly v2.9's; this file adds only metrics, self-classification,
and guardrails. it does not alter agent behavior.

--- v3.2 addition: endogenous episodic recurrence (time-dependence) ---

Fundamentalist episodes recur: a leader emerges and seizes the enforcement
apparatus, enforcement concentrates and the exit seals (an episode); grievance
accumulates until pushback ends it (mass revolt and/or elite coup, blended by
elite_pushback_weight); the apparatus dissolves and the exit reopens; grievance
decays; and -- because the BOOK (sigma legibility, pi reward affordance) never
changes -- a new leader can later re-ignite the same latent exploit. Recurrence
is excitable/stochastic (a leader-emergence hazard gated on low grievance), so
inter-episode intervals are irregular. Leaders EMERGE from the symmetric
substrate (the top-suitability active agent), never pre-assigned -- so the time
domain extends the invariance thesis: interchangeable leaders, one recurring
exploit built into the code itself.

The episode controller drives the existing `threat` cascade (threat -> controller
A -> monopoly -> pi_reward tighten -> delta seal), so it reuses validated
dynamics rather than adding a parallel enforcement path. With episode_module off,
behavior is identical to v3.1 (exogenous shock schedule). This is the foolproof
check: turning the module off must recover v3.1.
"""
import os, math, argparse, sys
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

# single source of truth for outcome classification. when run as a script,
# sys.path[0] is this file's dir (src/), so a bare import works; the insert is a
# defensive fallback for when this module is imported from elsewhere.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import regime_classifier


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

    # acquiescence mechanism (v2.9)
    # q_i tracks each agent's functional support for the enforcement apparatus.
    # leaky integrator: forcing pushes q up, decay erodes it without pressure.
    # steady state q* = forcing / gamma (pressurized equilibrium, not ratchet).
    omega_x: float = 0.02           # sunk cost: practice investment -> system loyalty
    omega_delta: float = 0.03       # trapped: high delta -> acquiescence
    omega_e: float = 0.04           # normalization: seeing neighbors punished
    omega_t: float = 0.02           # resentment: being punished decreases q
    gamma_q: float = 0.08           # decay: acquiescence erodes without pressure
    acquiescence_threshold: float = 0.60  # q >= this -> "functionally captured"

    # --- v3.2 endogenous episodic recurrence ---
    episode_module: bool = False       # master switch; off -> exact v3.1 behavior
    episode_intensity: float = 0.50    # threat injected while a leader holds the apparatus
    grievance_gain: float = 0.015      # grievance accrual per unit enforcement+entrapment
    grievance_decay: float = 0.02      # grievance decay per step during quiescence
    pushback_threshold: float = 0.60   # mass channel: grievance level that topples the regime
    elite_pushback_weight: float = 0.50  # 0 = pure mass revolt, 1 = pure elite coup
    elite_coup_hazard: float = 0.010   # elite channel: constant per-step coup probability
    leader_emergence_hazard: float = 0.02  # per-step prob a new leader ignites (when grievance low)
    grievance_quiet_max: float = 0.25  # grievance must be below this for a new leader to emerge
    delta_relax_rate: float = 0.05     # how fast the sealed exit reopens during quiescence
    refractory: int = 25               # min steps after an episode before a new one can ignite

    # homophilic rewiring (n=1000 validation)
    # each step, each active agent rewires one edge with probability p_rewire.
    # candidate accepted if doctrinal distance |y_i - y_j'| <= rewire_threshold.
    # if rejected, accept with probability rewire_random_fallback (random fallback).
    p_rewire: float = 0.0                 # rewire probability per agent per step (0 = disabled)
    rewire_threshold: float = 0.20        # max doctrinal distance for acceptance
    rewire_random_fallback: float = 0.10  # fallback acceptance probability if threshold not met

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
        self.q = 0.0  # acquiescence: functional support for enforcement apparatus (v2.9)

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
        if delta <= 0.0:
            opp_base_eff = p.exit_opportunity_base
        else:
            opp_base_eff = p.exit_opportunity_base * (1.0 - delta)
        p_opp_raw = sigmoid(
            opp_base_eff
            - p.exit_opportunity_deg_coeff * deg
            - p.exit_opportunity_threat_coeff * self.model.threat
        )
        p_opp = p.exit_block_floor + (1.0 - p.exit_block_floor) * (p_opp_raw ** p.exit_block_exponent)
        if delta > 0.0:
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
        # v3.2 episode state  (note: self.G is the graph; grievance is self.grievance)
        self.grievance = 0.0             # grievance reservoir (slow negative feedback)
        self.episode_active = False
        self.leader_id = None
        self.episode_start = 0
        self.last_episode_end = -10**9   # far in the past: no refractory block at t=0
        self.episodes_started = 0
        self.episode_log = []            # list of (start, end, leader_id, peak_grievance)
        self._peak_grievance = 0.0
        self.delta_baseline = float(np.clip(params.delta_outside_degrade, 0.0, 1.0))
        self.current_delta = float(self.delta_baseline)
        self.punish_intensity_step = 0.0

        self.t = 0
        self.exit_successes_step = 0
        self.punish_events_step = 0
        self.enforcer_punish_events_step = 0
        self.n_cadre_fallback_step = 0

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
        self._episode_control()
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
        self._update_acquiescence()  # v2.9: update q after delta and punishment are fresh

        ids = list(self.people.keys())
        self.rng.shuffle(ids)
        self.exit_successes_step = 0
        for i in ids:
            self.people[i].maybe_exit()
        self._homophilic_rewire()  # rewire after exit: survivors adjust connections
        self.t += 1

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

    def _leader_pick(self):
        """the emergent leader is the top-suitability active agent (same rule the
        cadre uses). never pre-assigned -- whoever is best positioned seizes it."""
        active = [a for a in self.people.values() if not a.exited]
        if not active:
            return None
        def suitability(a):
            return 0.6 * a.cap + 0.3 * a.L + 0.1 * (a.r * a.b)
        return max(active, key=suitability)

    def _episode_control(self):
        """endogenous episodic recurrence (v3.2).

        drives `self.threat` from the leader/grievance state instead of the
        exogenous shock schedule, so an 'episode' activates the existing
        threat -> A -> monopoly -> pi -> delta-seal cascade. off -> no-op.
        """
        p = self.params
        if not p.episode_module:
            return
        rng = self.rng

        if self.episode_active:
            # grievance accumulates. a baseline term (resentment of prolonged rule)
            # guarantees monotone growth even under weak enforcement, so the mass
            # channel always eventually toppling the regime -> no stuck-on episodes.
            self.grievance = float(np.clip(
                self.grievance + p.grievance_gain * (0.25 + self.punish_intensity_step + self.current_delta),
                0.0, 1.0))
            self._peak_grievance = max(self._peak_grievance, self.grievance)
            # pushback = mass channel (grievance past threshold, deterministic) blended
            # with elite channel (a constant per-step coup hazard, independent of how
            # the episode is going). both channels independently guarantee termination.
            w = float(np.clip(p.elite_pushback_weight, 0.0, 1.0))
            mass_signal = 1.0 if self.grievance >= p.pushback_threshold else 0.0
            p_end = (1.0 - w) * mass_signal + w * p.elite_coup_hazard
            if rng.random() < float(np.clip(p_end, 0.0, 1.0)):
                # episode ends: apparatus dissolves, threat collapses, exit will reopen.
                self.episode_log.append(
                    (self.episode_start, self.t, self.leader_id, round(self._peak_grievance, 3)))
                self.episode_active = False
                self.leader_id = None
                self._peak_grievance = 0.0
                self.last_episode_end = self.t
                self.threat = 0.0
            else:
                self.threat = p.episode_intensity      # hold the apparatus during the episode
        else:
            # quiescence: grievance decays, the sealed exit reopens, apparatus dormant.
            self.grievance = float(self.grievance * (1.0 - p.grievance_decay))
            self.threat = 0.0
            self.current_delta = float(
                self.delta_baseline + (self.current_delta - self.delta_baseline) * (1.0 - p.delta_relax_rate))
            # excitable re-ignition: a new leader emerges only once grievance has cooled
            # AND a refractory period has passed since the last episode (prevents flicker).
            cooled = self.grievance < p.grievance_quiet_max
            rested = (self.t - self.last_episode_end) >= p.refractory
            if cooled and rested and rng.random() < p.leader_emergence_hazard:
                leader = self._leader_pick()
                if leader is not None:
                    self.leader_id = leader.unique_id
                    self.episode_active = True
                    self.episode_start = self.t
                    self.episodes_started += 1
                    self.threat = p.episode_intensity

    def _update_controller(self):
        p = self.params
        if not p.episode_module:
            # exogenous shock schedule (v3.1 behavior) only when episodes are off.
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
        eta = float(np.clip(self.params.eta_delta_drift, 0.0, 0.5))
        if eta <= 0.0:
            return
        if self.punish_intensity_step < float(np.clip(self.params.punish_floor, 0.0, 1.0)):
            return
        eps = 1e-9
        enforcer_share = float(self.enforcer_punish_events_step / max(self.punish_events_step, eps))
        enforcer_share = float(np.clip(enforcer_share, 0.0, 1.0))
        delta_target = float(min(1.0, self.delta_baseline + enforcer_share))
        self.current_delta = float(np.clip(self.current_delta + eta * (delta_target - self.current_delta), 0.0, 1.0))

    def _update_acquiescence(self):
        """update acquiescence q for each agent (v2.9).

        leaky integrator: q converges to q* = forcing / gamma.
        acquiescence requires active maintenance — erodes without pressure.

        forcing channels:
          +omega_x * x          sunk cost from practice investment (unmodulated)
          +omega_delta * delta / (1 + base_opp)  entrapment, modulated by structural opportunity
          +omega_e * obs_punish normalization from observing neighbors punished
          -omega_t * was_punished resentment from being personally punished

        structural modulation: omega_delta is scaled by 1/(1 + base_opp).
        base_opp represents objective availability of alternatives (structural reality),
        independent of the agent's perceptual state (delta). a regime can distort
        perception (delta->1) but cannot eliminate the structural reality that
        alternatives exist. agents in high-base_opp environments (urban, mobile,
        economically diverse) accumulate less entrapment-driven acquiescence than
        agents in low-base_opp environments (isolated, dependent), even at equal delta.
        this follows iannaccone's distinction between subjective and objective exit costs.

        decay: -gamma_q * q (acquiescence erodes without enforcement pressure)
        """
        p = self.params
        delta = self.current_delta
        # structural outside-option modulator: raw base_opp, not delta-degraded
        # high base_opp -> weaker entrapment channel (alternatives actually exist)
        entrapment_mod = 1.0 / (1.0 + p.exit_opportunity_base)

        for agent in self.people.values():
            # exited agents: q stays at 0
            if agent.exited:
                continue
            # disengaged agents still update q (they're still in community)

            # fraction of active neighbors punished this step
            neigh_ids = list(self.G.neighbors(agent.node_id))
            active_neighbors = [self.people[j] for j in neigh_ids if not self.people[j].exited]
            if active_neighbors:
                observed_punish = float(np.mean([n.punished > 0 for n in active_neighbors]))
            else:
                observed_punish = 0.0

            # binary: was this agent punished at all this step?
            was_punished = 1.0 if agent.punished > 0 else 0.0

            # forcing: what pushes q up
            # omega_delta modulated by structural opportunity (entrapment channel)
            # omega_x unmodulated (sunk cost is irrational, not responsive to alternatives)
            forcing = (
                p.omega_x * agent.x
                + p.omega_delta * delta * entrapment_mod
                + p.omega_e * observed_punish
                - p.omega_t * was_punished
            )
            # decay: acquiescence erodes without pressure
            decay = p.gamma_q * agent.q
            # net update
            agent.q = float(np.clip(agent.q + forcing - decay, 0.0, 1.0))

    def _homophilic_rewire(self):
        """homophilic rewiring: each active agent rewires one edge with prob p_rewire.

        for each rewiring attempt:
        1. pick a random active neighbor to disconnect from
        2. pick a random non-neighbor active agent as candidate
        3. if |y_i - y_candidate| <= rewire_threshold: accept (rewire)
        4. else: with prob rewire_random_fallback, accept anyway (10% random)
        5. else: reject, keep old edge

        runs at end of step() after exit phase.
        """
        p = self.params
        if p.p_rewire <= 0.0:
            return

        active_ids = [i for i in self.people if not self.people[i].exited]
        if len(active_ids) < 3:
            return

        # precompute active set for candidate sampling
        active_set = set(active_ids)

        for i in active_ids:
            if self.rng.random() >= p.p_rewire:
                continue

            agent = self.people[i]
            neighbors = list(self.G.neighbors(i))
            # only consider active neighbors for dropping
            active_neighbors = [j for j in neighbors if not self.people[j].exited]
            if not active_neighbors:
                continue

            # pick random active neighbor to potentially drop
            drop_j = int(self.rng.choice(active_neighbors))

            # pick random non-neighbor active agent as candidate
            neighbor_set = set(neighbors)
            neighbor_set.add(i)  # exclude self
            candidates = [j for j in active_ids if j not in neighbor_set]
            if not candidates:
                continue

            new_j = int(self.rng.choice(candidates))

            # check doctrinal distance
            dist = abs(agent.y - self.people[new_j].y)
            accept = dist <= p.rewire_threshold
            if not accept:
                # random fallback
                accept = self.rng.random() < p.rewire_random_fallback

            if accept:
                self.G.remove_edge(i, drop_j)
                self.G.add_edge(i, new_j)

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
            # v2.9 acquiescence metrics
            qs = np.array([a.q for a in active_agents], dtype=float)
            mean_q = float(qs.mean())
            q_above_threshold = float((qs >= ps.acquiescence_threshold).mean())
            # capture_prevalence: fraction with (r*b >= F_star) OR (q >= threshold)
            capture_prevalence = float(((Fs >= ps.F_star) | (qs >= ps.acquiescence_threshold)).mean())
        else:
            mean_x = float("nan")
            mean_y = float("nan")
            mean_epc = float("nan")
            mean_r = float("nan")
            mean_b = float("nan")
            fund_prevalence = float("nan")
            mean_q = float("nan")
            q_above_threshold = float("nan")
            capture_prevalence = float("nan")
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
        else:
            mean_degree_active = 0.0
            p_opp_mean = 0.0
            stay_value = 0.0
            enforcer_frac = 0.0
            exit_attempt_rate = 0.0
        active_punish_frac = float((punished[~exited] > 0).mean()) if (~exited).any() else 0.0
        _qat = 0.0 if np.isnan(q_above_threshold) else q_above_threshold
        # enforcement pressure: overt punishment PLUS latent self-policing. this is the
        # foolproof metric -- when deterrence works, overt punish -> 0 but pressure stays
        # high via acquiescence, so a fear-compliant population is not read as "quiet".
        enforcement_pressure = float(_qat + (1.0 - _qat) * active_punish_frac)
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
            # v2.7.1: denominator restricted to active (non-exited) agents -> active-rate
            # confound cannot recur. enforcement_pressure additionally counts self-policing.
            punish_rate=active_punish_frac,
            enforcement_pressure=enforcement_pressure,
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
            # v3.2 episode state
            grievance=float(self.grievance),
            episode_active=float(1.0 if self.episode_active else 0.0),
            leader_id=(int(self.leader_id) if self.leader_id is not None else -1),
            episodes_started=int(self.episodes_started),
            eta_delta_drift=float(ps.eta_delta_drift),
            punish_floor=float(ps.punish_floor),
            punish_intensity_step=float(self.punish_intensity_step),
            pi_reward=float(ps.pi_reward),
            lam_punish=float(ps.lam_punish),
            # v2.9 acquiescence metrics
            mean_q=mean_q,
            q_above_threshold=q_above_threshold,
            capture_prevalence=capture_prevalence,
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
                    q=float(agent.q),  # v2.9 acquiescence
                    exit_cost_eff_last=float(agent.exit_cost_eff_last),
                    degree=int(degree.get(i, 0)),
                    degree_at_end=int(degree.get(i, 0)),
                    betweenness=float(betweenness.get(i, np.nan)),
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
    # v2.9 acquiescence mechanism
    ap.add_argument("--omega_x", type=float, default=0.02)
    ap.add_argument("--omega_delta", type=float, default=0.03)
    ap.add_argument("--omega_e", type=float, default=0.04)
    ap.add_argument("--omega_t", type=float, default=0.02)
    ap.add_argument("--gamma_q", type=float, default=0.08)
    ap.add_argument("--acquiescence_threshold", type=float, default=0.60)
    # v3.2 endogenous episodic recurrence
    ap.add_argument("--episode_module", action="store_true",
                    help="enable endogenous episodic recurrence (off -> v3.1 behavior).")
    ap.add_argument("--episode_intensity", type=float, default=0.50)
    ap.add_argument("--grievance_gain", type=float, default=0.015)
    ap.add_argument("--grievance_decay", type=float, default=0.02)
    ap.add_argument("--pushback_threshold", type=float, default=0.60)
    ap.add_argument("--elite_pushback_weight", type=float, default=0.50)
    ap.add_argument("--elite_coup_hazard", type=float, default=0.004)
    ap.add_argument("--leader_emergence_hazard", type=float, default=0.02)
    ap.add_argument("--grievance_quiet_max", type=float, default=0.25)
    ap.add_argument("--delta_relax_rate", type=float, default=0.05)
    ap.add_argument("--refractory", type=int, default=25)
    # homophilic rewiring
    ap.add_argument("--p_rewire", type=float, default=0.0)
    ap.add_argument("--rewire_threshold", type=float, default=0.20)
    ap.add_argument("--rewire_random_fallback", type=float, default=0.10)
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


def summarize_run(df: pd.DataFrame, tail_frac: float = 0.10) -> Dict[str, Any]:
    """collapse a per-step metrics frame to one canonical run summary.

    classifies the run via regime_classifier (the single source of truth) under
    two views and flags any contradiction between them -- the foolproof guardrail
    against mislabeling a fear-compliant, self-policing population as QUIET.
    """
    n = len(df)
    k = max(1, int(round(tail_frac * n)))
    tail = df.tail(k)
    exit_rate = float(tail["exit_rate"].median())
    active_punish = float(tail["punish_rate"].median())          # already active-restricted
    enforcer_share = float(tail["enforcer_punish_share_step"].median())
    q_above = float(tail["q_above_threshold"].median())
    fund_prev = float(tail["fund_prevalence"].median())
    pressure = float(tail["enforcement_pressure"].median())

    # overt-only regime: the historical (published) view -- self-policing invisible.
    regime_overt = regime_classifier.classify(
        exit_rate, active_punish, enforcer_share, schema="hierarchical")
    # acquiescence-aware regime: sealed-exit self-policing counts as functional capture.
    regime_aware = regime_classifier.classify(
        exit_rate, active_punish, enforcer_share, schema="hierarchical", acquiescence=q_above)

    mislabeled_fear_capture = bool(
        q_above >= regime_classifier.ACQUIESCENCE_CAPTURE_MIN and regime_overt == "QUIET"
    )
    return dict(
        final_exit_rate=exit_rate,
        final_active_punish=active_punish,
        final_enforcer_share=enforcer_share,
        final_q_above_threshold=q_above,
        final_fund_prevalence=fund_prev,
        final_enforcement_pressure=pressure,
        regime_overt=regime_overt,
        regime_acquiescence_aware=regime_aware,
        mislabeled_fear_capture=mislabeled_fear_capture,
    )


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
        omega_x=args.omega_x,
        omega_delta=args.omega_delta,
        omega_e=args.omega_e,
        omega_t=args.omega_t,
        gamma_q=args.gamma_q,
        acquiescence_threshold=args.acquiescence_threshold,
        episode_module=args.episode_module,
        episode_intensity=args.episode_intensity,
        grievance_gain=args.grievance_gain,
        grievance_decay=args.grievance_decay,
        pushback_threshold=args.pushback_threshold,
        elite_pushback_weight=args.elite_pushback_weight,
        elite_coup_hazard=args.elite_coup_hazard,
        leader_emergence_hazard=args.leader_emergence_hazard,
        grievance_quiet_max=args.grievance_quiet_max,
        delta_relax_rate=args.delta_relax_rate,
        refractory=args.refractory,
        p_rewire=args.p_rewire,
        rewire_threshold=args.rewire_threshold,
        rewire_random_fallback=args.rewire_random_fallback,
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
    for t in tqdm(range(args.steps), desc="Simulating"):
        if not args.no_movie:
            draw_frame(model, pos, os.path.join(frames_dir, f"frame_{t:05d}.png"))
        rows.append(model.metrics())
        model.step()

    metrics_df = pd.DataFrame(rows)
    metrics_df.to_csv(os.path.join(outdir, "metrics.csv"), index=False)
    model.agent_summary(include_betweenness=args.compute_betweenness).to_csv(
        os.path.join(outdir, "agent_summary.csv"), index=False
    )

    # self-classification: emit the canonical regime so no downstream inline
    # classifier is ever needed (foolproof single source of truth).
    summary = summarize_run(metrics_df)
    summary_row = dict(
        seed=int(params.seed), sigma=float(params.sigma), pi_reward=float(params.pi_reward),
        delta_outside_degrade=float(params.delta_outside_degrade),
        eta_delta_drift=float(params.eta_delta_drift),
        exit_opportunity_base=float(params.exit_opportunity_base),
        **summary,
    )
    pd.DataFrame([summary_row]).to_csv(os.path.join(outdir, "run_summary.csv"), index=False)
    print(
        f"[v3.1] regime overt={summary['regime_overt']} | "
        f"acquiescence-aware={summary['regime_acquiescence_aware']} | "
        f"pressure={summary['final_enforcement_pressure']:.2f} | "
        f"self-policing={summary['final_q_above_threshold']:.2f} | "
        f"enforcer-share={summary['final_enforcer_share']:.2f}"
        + ("  [!] overt view would mislabel this fear-capture as QUIET"
           if summary['mislabeled_fear_capture'] else "")
    )

    # v3.2 episode statistics: episodic recurrence driven by a persistent book.
    if params.episode_module:
        log = list(model.episode_log)
        if model.episode_active:  # count the in-progress episode too
            log.append((model.episode_start, model.t, model.leader_id, round(model._peak_grievance, 3)))
        durations = [end - start for (start, end, _lid, _pg) in log]
        starts = [start for (start, _e, _l, _p) in log]
        peaks = [pg for (_s, _e, _l, pg) in log]           # grievance at the moment of toppling
        intervals = [starts[i] - log[i - 1][1] for i in range(1, len(starts))]  # gap since prev end
        leaders = [lid for (_s, _e, lid, _p) in log if lid is not None]
        distinct_leaders = len(set(leaders))

        def cv(xs):
            return (float(np.std(xs) / np.mean(xs))
                    if xs and np.mean(xs) > 0 else float("nan"))
        ep = dict(
            n_episodes=len(log),
            mean_duration=float(np.mean(durations)) if durations else 0.0,
            duration_cv=cv(durations),                     # low => regular (mass), high => memoryless (elite)
            mean_peak_grievance=float(np.mean(peaks)) if peaks else float("nan"),  # ~threshold => mass-toppled
            mean_interval=float(np.mean(intervals)) if intervals else float("nan"),
            interval_cv=cv(intervals),
            distinct_leaders=distinct_leaders,
            repeat_leader=bool(len(leaders) != distinct_leaders),
        )
        pd.DataFrame([ep]).to_csv(os.path.join(outdir, "episode_summary.csv"), index=False)
        print(
            f"[v3.2] episodes={ep['n_episodes']} | mean_duration={ep['mean_duration']:.0f} | "
            f"mean_gap={ep['mean_interval']:.0f} | gap_CV={ep['interval_cv']:.2f} "
            f"(higher=more irregular) | distinct_leaders={ep['distinct_leaders']} "
            f"(role re-filled across episodes; repeats allowed)"
        )
    if not args.no_movie:
        make_movie(frames_dir, os.path.join(outdir, "movie.mp4"), fps=args.fps)

    if args.no_movie:
        print(f"Done.\nMetrics: {os.path.join(outdir, 'metrics.csv')}")
    else:
        print(f"Done.\nMP4: {os.path.join(outdir, 'movie.mp4')}\nMetrics: {os.path.join(outdir, 'metrics.csv')}")


if __name__ == "__main__":
    main()
