"""Tests for GIFRenderer -- frame rendering and GIF assembly."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import GifImagePlugin, Image

from griphogram import (
    AllReduceStrategy,
    GIFRenderer,
    GossipStrategy,
    Graph,
    ParameterServerStrategy,
    RenderConfig,
)


class TestRenderFrame:
    @pytest.fixture
    def renderer(self, k3_graph: Graph, render_config: RenderConfig) -> GIFRenderer:
        return GIFRenderer(k3_graph, AllReduceStrategy(), render_config)

    def test_frame_returns_rgba_image(self, renderer: GIFRenderer):
        img = renderer.render_frame(0)
        assert isinstance(img, Image.Image)
        assert img.mode == "RGBA"

    def test_frame_dimensions_match_config(self, renderer: GIFRenderer):
        img = renderer.render_frame(0)
        cfg = renderer.config
        assert img.size == (cfg.rw, cfg.rh)

    def test_frame_not_blank(self, renderer: GIFRenderer):
        img = renderer.render_frame(0)
        # Should have non-background pixels (nodes, edges, text)
        # getextrema() on RGBA returns a tuple of (min, max) per channel
        extrema = img.getextrema()
        assert isinstance(extrema, (list, tuple))
        assert any(isinstance(band, tuple) and band[0] != band[1] for band in extrema)

    def test_different_frames_differ(self, renderer: GIFRenderer):
        f0 = renderer.render_frame(0)
        f1 = renderer.render_frame(renderer.config.total_frames // 2)
        assert f0.tobytes() != f1.tobytes()


class TestRenderGIF:
    @pytest.mark.slow
    def test_gif_is_written(self, k3_graph: Graph, render_config: RenderConfig, tmp_path: Path):
        renderer = GIFRenderer(k3_graph, AllReduceStrategy(), render_config)
        out = renderer.render_gif(tmp_path / "test.gif", verbose=False)
        assert out.exists()
        assert out.stat().st_size > 100

    @pytest.mark.slow
    def test_gif_frame_count(self, k3_graph: Graph, render_config: RenderConfig, tmp_path: Path):
        renderer = GIFRenderer(k3_graph, AllReduceStrategy(), render_config)
        out = renderer.render_gif(tmp_path / "test.gif", verbose=False)
        img = Image.open(out)
        assert isinstance(img, GifImagePlugin.GifImageFile)
        assert img.n_frames == render_config.total_frames

    @pytest.mark.slow
    def test_gif_dimensions(self, k3_graph: Graph, render_config: RenderConfig, tmp_path: Path):
        renderer = GIFRenderer(k3_graph, AllReduceStrategy(), render_config)
        out = renderer.render_gif(tmp_path / "test.gif", verbose=False)
        img = Image.open(out)
        assert img.size == (render_config.width, render_config.height)


class TestAllStrategiesRender:
    """Smoke tests: every strategy renders at least one frame without error."""

    @pytest.fixture(params=["allreduce", "gossip", "parameter_server"])
    def strategy(self, request: pytest.FixtureRequest):
        match request.param:
            case "allreduce":
                return AllReduceStrategy()
            case "gossip":
                return GossipStrategy(n_nodes=3, n_rounds=2)
            case "parameter_server":
                return ParameterServerStrategy(ps_idx=0)

    def test_renders_without_error(
        self,
        strategy: AllReduceStrategy | GossipStrategy | ParameterServerStrategy,
        k3_graph: Graph,
        render_config: RenderConfig,
    ):
        renderer = GIFRenderer(k3_graph, strategy, render_config)
        img = renderer.render_frame(0)
        assert img.mode == "RGBA"
