"""
Value objects, enumerations, and type aliases.

Python 3.11+ features used:
    - ``StrEnum`` for shape identifiers
    - ``dataclass(slots=True, frozen=True)`` for zero-overhead immutable values
    - ``Protocol`` with ``@runtime_checkable`` for structural subtyping
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, TypeAlias, runtime_checkable

# ── Type aliases ──────────────────────────────────────────────────────────────

Color: TypeAlias = tuple[int, int, int]
Point2D: TypeAlias = tuple[float, float]
AdjacencyMatrix: TypeAlias = list[list[float]]
BezierFn: TypeAlias = Callable[[float], Point2D]


# ── Enumerations ──────────────────────────────────────────────────────────────


class ParticleShape(StrEnum):
    """Glyph primitives for gradient-packet visualisation."""

    CIRCLE = "circle"
    SQUARE = "square"
    TRIANGLE_UP = "triangle_up"
    TRIANGLE_DOWN = "triangle_down"
    DIAMOND = "diamond"
    HEXAGON = "hexagon"
    CROSS = "cross"
    PENTAGON = "pentagon"
    STAR4 = "star4"
    ARROW_RIGHT = "arrow_right"


# ── Immutable value objects ───────────────────────────────────────────────────


@dataclass(slots=True, frozen=True)
class EdgeStyle:
    """Unique ``(color, shape)`` visual identity assigned to one edge."""

    color: Color
    shape: ParticleShape


@dataclass(slots=True, frozen=True)
class Particle:
    """Single renderable gradient-packet in a frame."""

    x: float
    y: float
    color: Color
    shape: ParticleShape


@dataclass(slots=True, frozen=True)
class EdgeDescriptor:
    """
    Lightweight edge handle passed to strategies.

    Strategies receive these instead of rendering-layer ``CurvedEdge``
    objects — topology in, particles out.  Clean dependency boundary.
    """

    src_idx: int
    dst_idx: int
    weight: float
    style: EdgeStyle
    bezier_fn: BezierFn

    @property
    def key(self) -> tuple[int, int]:
        """Canonical undirected key ``(min, max)``."""
        return (min(self.src_idx, self.dst_idx), max(self.src_idx, self.dst_idx))


@dataclass(slots=True, frozen=True)
class RenderConfig:
    """Immutable rendering parameters — canvas, timing, particle sizing."""

    width: int = 800
    height: int = 600
    scale: int = 2
    fps: int = 18
    duration: float = 6.0
    particle_size: int = 10

    @property
    def rw(self) -> int:
        return self.width * self.scale

    @property
    def rh(self) -> int:
        return self.height * self.scale

    @property
    def total_frames(self) -> int:
        return int(self.fps * self.duration)

    @property
    def frame_ms(self) -> int:
        return int(1000 / self.fps)


# ── Strategy protocol ─────────────────────────────────────────────────────────


@runtime_checkable
class AggregationStrategy(Protocol):
    """
    Strategy protocol (structural subtyping) for gradient exchange algorithms.

    Any class with matching signatures satisfies this — no base class needed.

    See: https://refactoring.guru/design-patterns/strategy
    """

    @property
    def title(self) -> str: ...

    @property
    def subtitle(self) -> str: ...

    def get_phase_text(self, frame: int, total_frames: int) -> str: ...

    def get_edge_alpha(
        self, src: int, dst: int, frame: int, total_frames: int,
    ) -> float: ...

    def get_particles(
        self, edges: list[EdgeDescriptor], frame: int, total_frames: int,
    ) -> list[Particle]: ...
