"""
Ring-AllReduce strategy.

All edges active simultaneously with bidirectional particle flow.
Two-phase loop: ReduceScatter → AllGather.
"""

from __future__ import annotations

from dataclasses import dataclass

from griphogram.types import EdgeDescriptor, Particle


@dataclass(slots=True, frozen=True)
class AllReduceStrategy:
    """
    Ring-AllReduce on a fully-connected graph.

    Phase 1 (**ReduceScatter**): every node pushes gradient shards to all
    neighbours.  Phase 2 (**AllGather**): reduced shards broadcast back.
    """

    @property
    def title(self) -> str:
        return "AllReduce"

    @property
    def subtitle(self) -> str:
        return "ReduceScatter → AllGather  |  fully-connected"

    def get_phase_text(self, frame: int, total_frames: int) -> str:
        frac = (frame % total_frames) / total_frames
        if frac < 0.45:
            return "Phase: ReduceScatter"
        if frac < 0.55:
            return "Phase: Synchronize"
        return "Phase: AllGather"

    def get_edge_alpha(
        self, src: int, dst: int, frame: int, total_frames: int,
    ) -> float:
        return 1.0

    def get_particles(
        self, edges: list[EdgeDescriptor], frame: int, total_frames: int,
    ) -> list[Particle]:
        particles: list[Particle] = []
        t_norm = (frame % total_frames) / total_frames
        is_scatter = t_norm < 0.5
        speed = 1.2

        for edge in edges:
            n_dots = max(2, int(edge.weight * 4))
            base_t = frame * speed / total_frames

            for k in range(n_dots):
                progress = (base_t + k / n_dots) % 1.0
                t_fwd = progress if is_scatter else (1.0 - progress)
                t_rev = (1.0 - progress) if is_scatter else progress

                px, py = edge.bezier_fn(t_fwd)
                particles.append(Particle(px, py, edge.style.color, edge.style.shape))
                px2, py2 = edge.bezier_fn(t_rev)
                particles.append(Particle(px2, py2, edge.style.color, edge.style.shape))

        return particles
