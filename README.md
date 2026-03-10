# griphogram

Animated visualization of **gradient flow** across distributed ML graph topologies.

Generates publication-quality GIFs showing how gradient tensors propagate between
model replicas under different aggregation strategies — AllReduce, Gossip Protocol,
and Parameter Server — on fully-connected or custom graph topologies.

## Installation

```bash
pip install griphogram
```

**Requires Python ≥ 3.11** and [Pillow](https://pillow.readthedocs.io/) ≥ 10.0.

## Quick Start

```python
from griphogram import GraphBuilder, GIFRenderer, AllReduceStrategy

# Define a weighted adjacency matrix (edge weights = gradient magnitudes)
adj_matrix = [
    [0.0, 0.82, 0.57, 0.93, 0.68],
    [0.82, 0.0, 0.45, 0.71, 0.86],
    [0.57, 0.45, 0.0, 0.63, 0.39],
    [0.93, 0.71, 0.63, 0.0, 0.78],
    [0.68, 0.86, 0.39, 0.78, 0.0],
]

graph = (
    GraphBuilder()
    .with_adjacency_matrix(adj_matrix, center=(800, 620), radius=330)
    .build()
)

GIFRenderer(graph, AllReduceStrategy()).render_gif("allreduce.gif")
```

## CLI

```bash
# Generate all three canonical GIFs
griphogram --output-dir ./gifs --width 800 --height 600 --fps 18 --duration 6.0

# Or via module
python -m griphogram -o ./gifs
```

### Package Layout

```
src/griphogram/
├── __init__.py           # Public API surface
├── __main__.py           # CLI entry point
├── types.py              # StrEnum, dataclasses, Protocol, TypeAlias
├── graph.py              # Node, CurvedEdge, Graph, GraphBuilder
├── particles.py          # Shape renderers (match/case dispatch)
├── renderer.py           # GIFRenderer (Template Method)
├── theme.py              # Visual theme configuration
└── strategy/
    ├── allreduce.py       # Ring-AllReduce
    ├── gossip.py          # Decentralized SGD
    └── parameter_server.py
```

## Custom Strategies

Any class that satisfies the `AggregationStrategy` protocol works — no
inheritance is required:

```python
from griphogram.types import EdgeDescriptor, Particle

class MyCustomStrategy:
    @property
    def title(self) -> str:
        return "My Strategy"

    @property
    def subtitle(self) -> str:
        return "custom gradient exchange"

    def get_phase_text(self, frame: int, total_frames: int) -> str:
        return f"Step {frame}"

    def get_edge_alpha(self, src: int, dst: int, frame: int, total_frames: int) -> float:
        return 1.0

    def get_particles(
        self, edges: list[EdgeDescriptor], frame: int, total_frames: int,
    ) -> list[Particle]:
        particles = []
        for edge in edges:
            t = (frame / total_frames) % 1.0
            x, y = edge.bezier_fn(t)
            particles.append(Particle(x, y, edge.style.color, edge.style.shape))
        return particles
```

## Development

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest                    # fast tests only
pytest -m slow            # GIF rendering tests
pytest --cov=griphogram # with coverage

# Lint & type-check
ruff check src/ tests/
mypy src/
```

