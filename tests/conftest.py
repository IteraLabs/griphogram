"""Shared fixtures for the gradflow_viz test suite."""

from __future__ import annotations

import pytest

from griphogram import GraphBuilder, RenderConfig, Theme
from griphogram.types import AdjacencyMatrix


@pytest.fixture
def theme() -> Theme:
    return Theme()


@pytest.fixture
def render_config() -> RenderConfig:
    """Minimal config for fast tests."""
    return RenderConfig(width=200, height=150, scale=1, fps=4, duration=1.0)


@pytest.fixture
def k3_matrix() -> AdjacencyMatrix:
    """Simple K₃ adjacency matrix."""
    return [
        [0.0, 0.5, 0.8],
        [0.5, 0.0, 0.6],
        [0.8, 0.6, 0.0],
    ]


@pytest.fixture
def k5_matrix() -> AdjacencyMatrix:
    return [
        [0.0, 0.82, 0.57, 0.93, 0.68],
        [0.82, 0.0, 0.45, 0.71, 0.86],
        [0.57, 0.45, 0.0, 0.63, 0.39],
        [0.93, 0.71, 0.63, 0.0, 0.78],
        [0.68, 0.86, 0.39, 0.78, 0.0],
    ]


@pytest.fixture
def k3_graph(k3_matrix: AdjacencyMatrix, theme: Theme):
    return (
        GraphBuilder(theme).with_adjacency_matrix(k3_matrix, center=(200, 150), radius=80).build()
    )


@pytest.fixture
def k5_graph(k5_matrix: AdjacencyMatrix, theme: Theme):
    return (
        GraphBuilder(theme).with_adjacency_matrix(k5_matrix, center=(400, 310), radius=160).build()
    )
