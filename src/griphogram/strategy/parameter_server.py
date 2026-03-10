"""
Parameter Server strategy.

One designated node acts as the aggregator.  Workers push ∇L, then the
PS broadcasts updated θ.  Only PS-adjacent edges carry traffic.
"""

from __future__ import annotations

from dataclasses import dataclass

from griphogram.types import EdgeDescriptor, Particle


@dataclass(slots=True, frozen=True)
class ParameterServerStrategy:
    """
    Centralized parameter server on a graph where node ``ps_idx`` aggregates.

    Phase 1 (**Push**): workers → PS.
    Phase 2 (**Pull**): PS → workers.
    Non-PS edges remain visible but inactive.
    """

    ps_idx: int = 0

    @property
    def title(self) -> str:
        return "Parameter Server"

    @property
    def subtitle(self) -> str:
        return "centralized aggregation  |  marked coordinator"

    def get_phase_text(self, frame: int, total_frames: int) -> str:
        t = (frame % total_frames) / total_frames
        if t < 0.45:
            return "Phase: Push ∇L → PS"
        if t < 0.55:
            return "Phase: Aggregate"
        return "Phase: Pull θ ← PS"

    def _is_ps_edge(self, src: int, dst: int) -> bool:
        return src == self.ps_idx or dst == self.ps_idx

    def get_edge_alpha(
        self, src: int, dst: int, frame: int, total_frames: int,
    ) -> float:
        return 1.0 if self._is_ps_edge(src, dst) else 0.12

    def get_particles(
        self, edges: list[EdgeDescriptor], frame: int, total_frames: int,
    ) -> list[Particle]:
        particles: list[Particle] = []
        t_norm = (frame % total_frames) / total_frames
        is_push = t_norm < 0.5
        speed = 1.0

        for edge in edges:
            if not self._is_ps_edge(edge.src_idx, edge.dst_idx):
                continue

            src_is_ps = edge.src_idx == self.ps_idx
            n_dots = max(2, int(edge.weight * 4))
            base_t = frame * speed / total_frames

            for k in range(n_dots):
                progress = (base_t + k / n_dots) % 1.0
                if is_push:
                    t_val = (1.0 - progress) if src_is_ps else progress
                else:
                    t_val = progress if src_is_ps else (1.0 - progress)

                px, py = edge.bezier_fn(t_val)
                particles.append(Particle(px, py, edge.style.color, edge.style.shape))

        return particles
