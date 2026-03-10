"""
Gossip Protocol (Decentralised SGD) strategy.

Each round, nodes randomly select 1-2 neighbours for gradient exchange.
Not all edges active simultaneously -- staggered, asynchronous.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from griphogram.types import EdgeDescriptor, Particle


def _precompute_rounds(
    n_nodes: int, n_rounds: int, seed: int = 42,
) -> list[set[tuple[int, int]]]:
    """Pre-compute deterministic gossip round edge selections."""
    rng = random.Random(seed)
    rounds: list[set[tuple[int, int]]] = []
    for _ in range(n_rounds):
        active: set[tuple[int, int]] = set()
        for node_idx in range(n_nodes):
            neighbours = [j for j in range(n_nodes) if j != node_idx]
            picked = rng.sample(neighbours, rng.choice([1, 2]))
            for p in picked:
                active.add((min(node_idx, p), max(node_idx, p)))
        rounds.append(active)
    return rounds


@dataclass(slots=True)
class GossipStrategy:
    """
    Gossip Protocol — decentralised partial gradient exchange.

    Each gossip round, a stochastic subset of edges activates.  Particle
    flow is bidirectional on active edges only.
    """

    n_nodes: int = 5
    n_rounds: int = 5
    seed: int = 42
    _round_edges: list[set[tuple[int, int]]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "_round_edges",
            _precompute_rounds(self.n_nodes, self.n_rounds, self.seed),
        )

    @property
    def title(self) -> str:
        return "Gossip Protocol"

    @property
    def subtitle(self) -> str:
        return "Decentralized SGD  |  stochastic partial exchange"

    def _current_round(self, frame: int, total_frames: int) -> int:
        fpr = total_frames // self.n_rounds
        return (frame // max(fpr, 1)) % self.n_rounds

    def get_phase_text(self, frame: int, total_frames: int) -> str:
        r = self._current_round(frame, total_frames)
        return f"Gossip Round {r + 1}/{self.n_rounds}"

    def get_edge_alpha(
        self, src: int, dst: int, frame: int, total_frames: int,
    ) -> float:
        r = self._current_round(frame, total_frames)
        key = (min(src, dst), max(src, dst))
        return 1.0 if key in self._round_edges[r] else 0.15

    def get_particles(
        self, edges: list[EdgeDescriptor], frame: int, total_frames: int,
    ) -> list[Particle]:
        particles: list[Particle] = []
        r = self._current_round(frame, total_frames)
        active = self._round_edges[r]
        speed = 0.9

        for edge in edges:
            if edge.key not in active:
                continue
            n_dots = max(2, int(edge.weight * 4))
            base_t = frame * speed / total_frames

            for k in range(n_dots):
                progress = (base_t + k / n_dots) % 1.0
                px, py = edge.bezier_fn(progress)
                particles.append(Particle(px, py, edge.style.color, edge.style.shape))
                px2, py2 = edge.bezier_fn(1.0 - progress)
                particles.append(Particle(px2, py2, edge.style.color, edge.style.shape))

        return particles
