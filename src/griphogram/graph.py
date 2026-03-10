"""
Graph topology: nodes, curved edges, and a **Builder** for construction.

Design patterns:
    - **Builder** — ``GraphBuilder`` fluent API for assembling complex graphs.
    - **Composite** — ``Graph`` composes ``Node`` and ``CurvedEdge`` lists.

See: https://refactoring.guru/design-patterns/builder
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Self

from griphogram.theme import Theme
from griphogram.types import (
    AdjacencyMatrix,
    EdgeDescriptor,
    EdgeStyle,
    Point2D,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Primitives
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass(slots=True)
class Node:
    """Graph vertex with render coordinates and optional role annotation."""

    idx: int
    x: float
    y: float
    label: str
    is_leader: bool = False
    radius: int = 34


@dataclass(slots=True)
class CurvedEdge:
    """
    Quadratic Bézier edge that bows **away** from a reference point,
    giving circular / arc layouts instead of straight-line pentagram looks.
    """

    src: Node
    dst: Node
    weight: float
    style: EdgeStyle

    ctrl_x: float = 0.0
    ctrl_y: float = 0.0

    @property
    def key(self) -> tuple[int, int]:
        return (min(self.src.idx, self.dst.idx), max(self.src.idx, self.dst.idx))

    def bezier_point(self, t: float) -> Point2D:
        """Evaluate quadratic Bézier ``B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂``."""
        u = 1.0 - t
        x = u * u * self.src.x + 2 * u * t * self.ctrl_x + t * t * self.dst.x
        y = u * u * self.src.y + 2 * u * t * self.ctrl_y + t * t * self.dst.y
        return (x, y)

    def bezier_points(self, n: int = 40) -> list[Point2D]:
        """Sample ``n + 1`` evenly-spaced points along the curve."""
        return [self.bezier_point(i / n) for i in range(n + 1)]

    def midpoint(self) -> Point2D:
        return self.bezier_point(0.5)

    def to_descriptor(self) -> EdgeDescriptor:
        """Project into a strategy-facing descriptor (no render state)."""
        return EdgeDescriptor(
            src_idx=self.src.idx,
            dst_idx=self.dst.idx,
            weight=self.weight,
            style=self.style,
            bezier_fn=self.bezier_point,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Composite
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass(slots=True)
class Graph:
    """
    Immutable-ish topology container.

    Composed of ``Node`` and ``CurvedEdge`` lists — created exclusively
    through ``GraphBuilder`` to guarantee invariants.
    """

    nodes: list[Node] = field(default_factory=list)
    edges: list[CurvedEdge] = field(default_factory=list)

    def edge_descriptors(self) -> list[EdgeDescriptor]:
        """Return strategy-facing descriptors for every edge."""
        return [e.to_descriptor() for e in self.edges]


# ═══════════════════════════════════════════════════════════════════════════════
# Builder
# ═══════════════════════════════════════════════════════════════════════════════


class GraphBuilder:
    """
    Fluent builder for ``Graph`` instances.

    Typical usage::

        graph = (
            GraphBuilder(theme=Theme())
            .with_adjacency_matrix(matrix, center=(800, 620), radius=330)
            .mark_leaders({0, 3, 6})
            .build()
        )

    See: https://refactoring.guru/design-patterns/builder
    """

    def __init__(self, theme: Theme | None = None) -> None:
        self._theme = theme or Theme()
        self._nodes: list[Node] = []
        self._edges: list[CurvedEdge] = []

    # ── Node placement ────────────────────────────────────────────────────

    def with_ring_layout(
        self,
        n: int,
        center: Point2D,
        radius: float,
        *,
        labels: list[str] | None = None,
    ) -> Self:
        """Place *n* nodes on a regular polygon centred at *center*."""
        self._nodes.clear()
        for i in range(n):
            angle = -math.pi / 2 + i * 2 * math.pi / n
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            lbl = labels[i] if labels else f"W{i}"
            self._nodes.append(Node(idx=i, x=x, y=y, label=lbl))
        return self

    def with_custom_positions(
        self, positions: list[tuple[float, float, str]]
    ) -> Self:
        """Place nodes at explicit ``(x, y, label)`` triples."""
        self._nodes = [
            Node(idx=i, x=x, y=y, label=lbl)
            for i, (x, y, lbl) in enumerate(positions)
        ]
        return self

    # ── Edge construction ─────────────────────────────────────────────────

    def with_adjacency_matrix(
        self,
        matrix: AdjacencyMatrix,
        center: Point2D,
        radius: float,
        *,
        curvature: float = 0.35,
        labels: list[str] | None = None,
    ) -> Self:
        """
        Build a complete graph from a dense adjacency / mixing matrix.

        Nodes are placed in a ring layout.  Edges are created for every
        ``matrix[i][j] > 0`` where ``i < j``.  Control points are pushed
        radially outward from *center* to produce curved arcs.
        """
        n = len(matrix)
        self.with_ring_layout(n, center, radius, labels=labels)
        self._edges.clear()

        style_idx = 0
        for i in range(n):
            for j in range(i + 1, n):
                w = matrix[i][j]
                if w <= 0:
                    continue

                style = self._theme.edge_style_for(style_idx)
                edge = self._make_curved_edge(
                    self._nodes[i], self._nodes[j], w, style, center, curvature,
                )
                self._edges.append(edge)
                style_idx += 1
        return self

    def with_edges_from_matrix(
        self, matrix: AdjacencyMatrix, center: Point2D, curvature: float = 0.35,
    ) -> Self:
        """Add edges from *matrix* using already-placed nodes."""
        self._edges.clear()
        style_idx = 0
        for i in range(len(matrix)):
            for j in range(i + 1, len(matrix)):
                w = matrix[i][j]
                if w <= 0:
                    continue
                style = self._theme.edge_style_for(style_idx)
                edge = self._make_curved_edge(
                    self._nodes[i], self._nodes[j], w, style, center, curvature,
                )
                self._edges.append(edge)
                style_idx += 1
        return self

    # ── Node annotation ───────────────────────────────────────────────────

    def mark_leaders(self, indices: set[int], *, radius: int = 42) -> Self:
        """Flag nodes as leaders (rendered with double-ring + larger radius)."""
        for node in self._nodes:
            if node.idx in indices:
                node.is_leader = True
                node.radius = radius
        return self

    def relabel(self, mapping: dict[int, str]) -> Self:
        """Override labels for specific node indices."""
        for node in self._nodes:
            if node.idx in mapping:
                node.label = mapping[node.idx]
        return self

    # ── Build ─────────────────────────────────────────────────────────────

    def build(self) -> Graph:
        """Freeze the builder state into an immutable ``Graph``."""
        if not self._nodes:
            msg = "Graph must have at least one node"
            raise ValueError(msg)
        return Graph(nodes=list(self._nodes), edges=list(self._edges))

    # ── Internal ──────────────────────────────────────────────────────────

    @staticmethod
    def _make_curved_edge(
        src: Node,
        dst: Node,
        weight: float,
        style: EdgeStyle,
        center: Point2D,
        curvature: float,
    ) -> CurvedEdge:
        mx = (src.x + dst.x) / 2
        my = (src.y + dst.y) / 2
        dx = mx - center[0]
        dy = my - center[1]
        dist = max(math.sqrt(dx * dx + dy * dy), 1e-6)

        edge_len = math.sqrt((dst.x - src.x) ** 2 + (dst.y - src.y) ** 2)
        push = edge_len * curvature

        ctrl_x = mx + (dx / dist) * push
        ctrl_y = my + (dy / dist) * push

        return CurvedEdge(
            src=src, dst=dst, weight=weight, style=style,
            ctrl_x=ctrl_x, ctrl_y=ctrl_y,
        )
