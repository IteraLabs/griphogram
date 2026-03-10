"""Tests for Graph, GraphBuilder, Node, CurvedEdge."""

from __future__ import annotations

import math

import pytest

from griphogram import Graph, GraphBuilder, Node, Theme
from griphogram.graph import CurvedEdge
from griphogram.types import AdjacencyMatrix, EdgeStyle, ParticleShape


class TestNode:
    def test_defaults(self):
        n = Node(idx=0, x=10.0, y=20.0, label="W0")
        assert not n.is_leader
        assert n.radius == 34

    def test_leader_radius_overridable(self):
        n = Node(idx=0, x=0, y=0, label="L0", is_leader=True, radius=50)
        assert n.radius == 50


class TestCurvedEdge:
    @pytest.fixture
    def sample_edge(self):
        src = Node(0, 0.0, 0.0, "A")
        dst = Node(1, 100.0, 0.0, "B")
        style = EdgeStyle((255, 0, 0), ParticleShape.CIRCLE)
        return CurvedEdge(src=src, dst=dst, weight=0.7, style=style,
                          ctrl_x=50.0, ctrl_y=-30.0)

    def test_key_is_canonical(self, sample_edge: CurvedEdge):
        assert sample_edge.key == (0, 1)

    def test_bezier_endpoints(self, sample_edge: CurvedEdge):
        p0 = sample_edge.bezier_point(0.0)
        p1 = sample_edge.bezier_point(1.0)
        assert math.isclose(p0[0], 0.0, abs_tol=1e-6)
        assert math.isclose(p1[0], 100.0, abs_tol=1e-6)

    def test_bezier_midpoint_displaced(self, sample_edge: CurvedEdge):
        """Midpoint should be displaced from the straight-line midpoint."""
        mid = sample_edge.bezier_point(0.5)
        # ctrl_y = -30, so midpoint should be above the line (y < 0)
        assert mid[1] < 0

    def test_bezier_points_count(self, sample_edge: CurvedEdge):
        pts = sample_edge.bezier_points(n=20)
        assert len(pts) == 21

    def test_to_descriptor_preserves_topology(self, sample_edge: CurvedEdge):
        d = sample_edge.to_descriptor()
        assert d.src_idx == 0
        assert d.dst_idx == 1
        assert d.weight == 0.7
        # Descriptor's bezier_fn should agree with edge
        p_edge = sample_edge.bezier_point(0.3)
        p_desc = d.bezier_fn(0.3)
        assert math.isclose(p_edge[0], p_desc[0])


class TestGraphBuilder:
    def test_ring_layout_node_count(self, theme: Theme):
        graph = (
            GraphBuilder(theme)
            .with_ring_layout(5, center=(100, 100), radius=50)
            .build()
        )
        assert len(graph.nodes) == 5

    def test_ring_layout_first_node_at_top(self, theme: Theme):
        graph = (
            GraphBuilder(theme)
            .with_ring_layout(4, center=(100.0, 100.0), radius=50.0)
            .build()
        )
        top = graph.nodes[0]
        # First node at -π/2 → y should be center_y - radius
        assert math.isclose(top.y, 50.0, abs_tol=1.0)

    def test_adjacency_matrix_edge_count(self, k3_matrix: AdjacencyMatrix, theme: Theme):
        graph = (
            GraphBuilder(theme)
            .with_adjacency_matrix(k3_matrix, center=(100, 100), radius=50)
            .build()
        )
        assert len(graph.edges) == 3  # K₃ has 3 edges

    def test_k5_has_10_edges(self, k5_matrix: AdjacencyMatrix, theme: Theme):
        graph = (
            GraphBuilder(theme)
            .with_adjacency_matrix(k5_matrix, center=(400, 300), radius=100)
            .build()
        )
        assert len(graph.edges) == 10

    def test_sparse_matrix_skips_zeros(self, theme: Theme):
        matrix = [
            [0.0, 0.5, 0.0],
            [0.5, 0.0, 0.0],
            [0.0, 0.0, 0.0],
        ]
        graph = (
            GraphBuilder(theme)
            .with_adjacency_matrix(matrix, center=(100, 100), radius=50)
            .build()
        )
        assert len(graph.edges) == 1

    def test_mark_leaders(self, k3_matrix: AdjacencyMatrix, theme: Theme):
        graph = (
            GraphBuilder(theme)
            .with_adjacency_matrix(k3_matrix, center=(100, 100), radius=50)
            .mark_leaders({0, 2})
            .build()
        )
        assert graph.nodes[0].is_leader
        assert not graph.nodes[1].is_leader
        assert graph.nodes[2].is_leader

    def test_relabel(self, k3_matrix: AdjacencyMatrix, theme: Theme):
        graph = (
            GraphBuilder(theme)
            .with_adjacency_matrix(k3_matrix, center=(100, 100), radius=50)
            .relabel({0: "PS", 2: "Leader"})
            .build()
        )
        assert graph.nodes[0].label == "PS"
        assert graph.nodes[2].label == "Leader"

    def test_empty_graph_raises(self, theme: Theme):
        with pytest.raises(ValueError, match="at least one node"):
            GraphBuilder(theme).build()

    def test_edge_descriptors(self, k3_graph: Graph):
        descs = k3_graph.edge_descriptors()
        assert len(descs) == 3
        assert all(d.weight > 0 for d in descs)

    def test_custom_positions(self, theme: Theme):
        graph = (
            GraphBuilder(theme)
            .with_custom_positions([(0, 0, "A"), (100, 0, "B")])
            .build()
        )
        assert len(graph.nodes) == 2
        assert graph.nodes[1].label == "B"
