"""
``griphogram`` — Animated gradient-flow visualisation for distributed ML.

Quick start::

    from griphogram import GraphBuilder, GIFRenderer, AllReduceStrategy, Theme

    matrix = [
        [0.0, 0.8, 0.6],
        [0.8, 0.0, 0.5],
        [0.6, 0.5, 0.0],
    ]

    graph = (
        GraphBuilder()
        .with_adjacency_matrix(matrix, center=(800, 620), radius=300)
        .build()
    )

    GIFRenderer(graph, AllReduceStrategy()).render_gif("allreduce.gif")
"""

from griphogram.graph import CurvedEdge, Graph, GraphBuilder, Node
from griphogram.renderer import GIFRenderer
from griphogram.strategy import (
    AllReduceStrategy,
    GossipStrategy,
    ParameterServerStrategy,
)
from griphogram.theme import Theme
from griphogram.types import (
    AggregationStrategy,
    EdgeDescriptor,
    EdgeStyle,
    Particle,
    ParticleShape,
    RenderConfig,
)

__all__ = [
    "AggregationStrategy",
    "AllReduceStrategy",
    "CurvedEdge",
    "EdgeDescriptor",
    "EdgeStyle",
    "GIFRenderer",
    "GossipStrategy",
    "Graph",
    "GraphBuilder",
    "Node",
    "ParameterServerStrategy",
    "Particle",
    "ParticleShape",
    "RenderConfig",
    "Theme",
]

__version__ = "0.1.0"
