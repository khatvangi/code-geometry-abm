#!/usr/bin/env python3
import os, math, argparse
from dataclasses import dataclass
from typing import Dict, Any, List

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
    rho_r: float = 0.04
    rho_b: float = 0.03

    # Social dynamics
    norm_weight: float = 0.55
    shame_weight: float = 0.70
    noise_x: float = 0.02
    cult_step: float = 0.04

    # Fundamentalism measurement threshold
    F_star: float = 0.45


class Person(Agent):
    def __init__(self, unique_id: int, model: "ReligionABM"):
        super().__init__(model)
        self.node_id = unique_id
        rng = self.model.rng

        self.x = float(np.clip(rng.normal(0.35, 0.12), 0.0, 1.0))  # ITC
        self.s = 0  # EPC marker
        self.b = float(np.clip(rng.beta(2.0, 4.0), 0.0, 1.0))  # rigidity
        self.r = float(np.clip(rng.beta(2.0, 4.0), 0.0, 1.0))  # enforcement propensity
        self.u = 0.0
        self.punished = 0
        self.punish_issued = 0
        self.punished_total = 0

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

    def fundamentalism_index(self) -> float:
        return self.r * self.b

    def step(self):
        p = self.model.params
        rng = self.model.rng

        neigh_ids = list(self.model.G.neighbors(self.node_id))
        neigh: List[Person] = [self.model.people[j] for j in neigh_ids] if neigh_ids else []

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

        self.punished = 0

    def police_phase(self):
        p = self.model.params
        rng = self.model.rng
        neigh_ids = list(self.model.G.neighbors(self.node_id))
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

            theta = 0.55 - 0.20 * self.b
            p_pun = (self.r) * sigmoid(p.beta_pun * (theta - m_hat))

            if rng.random() < p_pun:
                target.u -= p.lam_punish
                target.punished += 1
                target.punished_total += 1
                self.punish_issued += 1

                legibility = p.sigma * p.v_obs + (1.0 - p.sigma) * p.a_obs
                delta_u = (p.pi_reward * legibility) - p.kappa_cost
                self.u += delta_u

                p_backlash = float(
                    np.clip(p.backlash_base + p.backlash_sensitivity * (1.0 - legibility), 0.0, 1.0)
                )
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

        self.t = 0

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
        ids = list(self.people.keys())
        self.rng.shuffle(ids)
        for i in ids:
            self.people[i].step()

        ids = list(self.people.keys())
        self.rng.shuffle(ids)
        for i in ids:
            self.people[i].police_phase()
        self.t += 1

    def metrics(self) -> Dict[str, Any]:
        ps = self.params
        xs = np.array([a.x for a in self.people.values()], dtype=float)
        ss = np.array([a.s for a in self.people.values()], dtype=float)
        rs = np.array([a.r for a in self.people.values()], dtype=float)
        bs = np.array([a.b for a in self.people.values()], dtype=float)
        Fs = rs * bs
        punished = np.array([a.punished for a in self.people.values()], dtype=float)
        return dict(
            t=self.t,
            mean_x=float(xs.mean()),
            mean_epc=float(ss.mean()),
            mean_r=float(rs.mean()),
            mean_b=float(bs.mean()),
            fund_prevalence=float((Fs > ps.F_star).mean()),
            punish_rate=float((punished > 0).mean()),
            mean_punished=float(punished.mean()),
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
                    degree=int(degree.get(i, 0)),
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

    ap.add_argument("--pi_reward", type=float, default=0.22)
    ap.add_argument("--kappa_cost", type=float, default=0.08)
    ap.add_argument("--lam_punish", type=float, default=0.25)
    ap.add_argument("--backlash_base", type=float, default=0.25)
    ap.add_argument("--backlash_cost", type=float, default=0.30)
    ap.add_argument("--backlash_sensitivity", type=float, default=1.0)
    ap.add_argument("--no_movie", action="store_true", help="Skip frame rendering and MP4 encoding.")
    ap.add_argument("--compute_betweenness", action="store_true", help="Include network betweenness centrality in agent_summary.csv.")
    return ap.parse_args()


def main():
    args = parse_args()
    params = Params(
        n=args.n, graph=args.graph, seed=args.seed,
        sigma=args.sigma, v_obs=args.v_obs, a_obs=args.a_obs,
        pi_reward=args.pi_reward,
        kappa_cost=args.kappa_cost,
        lam_punish=args.lam_punish,
        backlash_base=args.backlash_base,
        backlash_cost=args.backlash_cost,
        backlash_sensitivity=args.backlash_sensitivity,
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

    pd.DataFrame(rows).to_csv(os.path.join(outdir, "metrics.csv"), index=False)
    model.agent_summary(include_betweenness=args.compute_betweenness).to_csv(
        os.path.join(outdir, "agent_summary.csv"), index=False
    )
    if not args.no_movie:
        make_movie(frames_dir, os.path.join(outdir, "movie.mp4"), fps=args.fps)

    if args.no_movie:
        print(f"Done.\nMetrics: {os.path.join(outdir, 'metrics.csv')}")
    else:
        print(f"Done.\nMP4: {os.path.join(outdir, 'movie.mp4')}\nMetrics: {os.path.join(outdir, 'metrics.csv')}")


if __name__ == "__main__":
    main()
