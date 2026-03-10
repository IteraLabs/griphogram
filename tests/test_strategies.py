"""Tests for all three aggregation strategies."""

from __future__ import annotations

import pytest

from griphogram import (
    AllReduceStrategy,
    GossipStrategy,
    Graph,
    ParameterServerStrategy,
)
from griphogram.types import AggregationStrategy


class TestAllReduce:
    @pytest.fixture
    def strategy(self) -> AllReduceStrategy:
        return AllReduceStrategy()

    def test_satisfies_protocol(self, strategy: AllReduceStrategy):
        assert isinstance(strategy, AggregationStrategy)

    def test_title(self, strategy: AllReduceStrategy):
        assert strategy.title == "AllReduce"

    def test_all_edges_fully_active(self, strategy: AllReduceStrategy):
        assert strategy.get_edge_alpha(0, 1, frame=0, total_frames=100) == 1.0
        assert strategy.get_edge_alpha(3, 4, frame=50, total_frames=100) == 1.0

    def test_phase_text_scatter(self, strategy: AllReduceStrategy):
        text = strategy.get_phase_text(frame=10, total_frames=100)
        assert "ReduceScatter" in text

    def test_phase_text_gather(self, strategy: AllReduceStrategy):
        text = strategy.get_phase_text(frame=80, total_frames=100)
        assert "AllGather" in text

    def test_particles_nonempty(self, strategy: AllReduceStrategy, k3_graph: Graph):
        descs = k3_graph.edge_descriptors()
        particles = strategy.get_particles(descs, frame=5, total_frames=100)
        assert len(particles) > 0

    def test_particles_bidirectional(self, strategy: AllReduceStrategy, k3_graph: Graph):
        """Each edge should produce at least 2 particles (one per direction)."""
        descs = k3_graph.edge_descriptors()
        particles = strategy.get_particles(descs, frame=5, total_frames=100)
        # 3 edges x min 2 dots x 2 directions = 12 minimum
        assert len(particles) >= 12


class TestGossip:
    @pytest.fixture
    def strategy(self) -> GossipStrategy:
        return GossipStrategy(n_nodes=5, n_rounds=5, seed=42)

    def test_satisfies_protocol(self, strategy: GossipStrategy):
        assert isinstance(strategy, AggregationStrategy)

    def test_title(self, strategy: GossipStrategy):
        assert "Gossip" in strategy.title

    def test_some_edges_dimmed(self, strategy: GossipStrategy):
        """Not all edges can be active in gossip -- at least one must be dim."""
        alphas = [
            strategy.get_edge_alpha(i, j, frame=0, total_frames=100)
            for i in range(5) for j in range(i + 1, 5)
        ]
        assert any(a < 1.0 for a in alphas), "Gossip should dim inactive edges"

    def test_round_text_changes(self, strategy: GossipStrategy):
        t1 = strategy.get_phase_text(frame=0, total_frames=100)
        t2 = strategy.get_phase_text(frame=50, total_frames=100)
        # Rounds should differ
        assert "Round" in t1
        assert t1 != t2

    def test_deterministic_rounds(self):
        """Same seed -> same rounds."""
        s1 = GossipStrategy(n_nodes=5, n_rounds=3, seed=99)
        s2 = GossipStrategy(n_nodes=5, n_rounds=3, seed=99)
        assert s1._round_edges == s2._round_edges

    def test_different_seed_different_rounds(self):
        s1 = GossipStrategy(n_nodes=5, n_rounds=3, seed=1)
        s2 = GossipStrategy(n_nodes=5, n_rounds=3, seed=2)
        assert s1._round_edges != s2._round_edges


class TestParameterServer:
    @pytest.fixture
    def strategy(self) -> ParameterServerStrategy:
        return ParameterServerStrategy(ps_idx=0)

    def test_satisfies_protocol(self, strategy: ParameterServerStrategy):
        assert isinstance(strategy, AggregationStrategy)

    def test_ps_edges_active(self, strategy: ParameterServerStrategy):
        assert strategy.get_edge_alpha(0, 1, frame=0, total_frames=100) == 1.0
        assert strategy.get_edge_alpha(0, 4, frame=0, total_frames=100) == 1.0

    def test_non_ps_edges_dim(self, strategy: ParameterServerStrategy):
        assert strategy.get_edge_alpha(1, 2, frame=0, total_frames=100) == 0.12

    def test_push_phase(self, strategy: ParameterServerStrategy):
        text = strategy.get_phase_text(frame=10, total_frames=100)
        assert "Push" in text

    def test_pull_phase(self, strategy: ParameterServerStrategy):
        text = strategy.get_phase_text(frame=80, total_frames=100)
        assert "Pull" in text

    def test_only_ps_edges_produce_particles(
        self, strategy: ParameterServerStrategy, k5_graph: Graph,
    ):
        descs = k5_graph.edge_descriptors()
        particles = strategy.get_particles(descs, frame=10, total_frames=100)
        # All particles must lie on PS-adjacent edges
        assert len(particles) > 0
