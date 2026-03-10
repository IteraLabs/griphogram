"""
CLI entry point: ``python -m griphogram`` or ``griphogram``.

Generates the three canonical aggregation GIFs to an output directory.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from griphogram import (
    AllReduceStrategy,
    GIFRenderer,
    GossipStrategy,
    GraphBuilder,
    ParameterServerStrategy,
    RenderConfig,
    Theme,
)

_K5_WEIGHTS = [
    [0.0, 0.82, 0.57, 0.93, 0.68],
    [0.82, 0.0, 0.45, 0.71, 0.86],
    [0.57, 0.45, 0.0, 0.63, 0.39],
    [0.93, 0.71, 0.63, 0.0, 0.78],
    [0.68, 0.86, 0.39, 0.78, 0.0],
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="griphogram",
        description="Generate gradient-flow GIFs for distributed ML topologies.",
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory for generated GIFs (default: ./output)",
    )
    parser.add_argument(
        "--width", type=int, default=800,
    )
    parser.add_argument(
        "--height", type=int, default=600,
    )
    parser.add_argument(
        "--fps", type=int, default=18,
    )
    parser.add_argument(
        "--duration", type=float, default=6.0,
        help="Animation loop duration in seconds",
    )
    args = parser.parse_args(argv)

    config = RenderConfig(
        width=args.width,
        height=args.height,
        fps=args.fps,
        duration=args.duration,
    )
    theme = Theme()
    center = (config.rw // 2, config.rh // 2 + 30)

    strategies: list[tuple[str, object]] = [
        ("allreduce_gradient_flow.gif", AllReduceStrategy()),
        ("gossip_gradient_flow.gif", GossipStrategy(n_nodes=5)),
        ("parameter_server_gradient_flow.gif", ParameterServerStrategy(ps_idx=0)),
    ]

    for i, (filename, strategy) in enumerate(strategies, 1):
        print(f"\n[{i}/{len(strategies)}] {strategy.title}")  # type: ignore[union-attr]
        builder = GraphBuilder(theme)
        builder.with_adjacency_matrix(_K5_WEIGHTS, center, radius=330)
        if isinstance(strategy, ParameterServerStrategy):
            builder.mark_leaders({0})
            builder.relabel({0: "PS"})
        graph = builder.build()

        renderer = GIFRenderer(graph, strategy, config, theme)  # type: ignore[arg-type]
        renderer.render_gif(args.output_dir / filename)

    print("\n═══ All GIFs generated ═══")
    return 0


if __name__ == "__main__":
    sys.exit(main())
