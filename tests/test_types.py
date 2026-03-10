"""Tests for value objects, enums, and the Strategy protocol."""

from __future__ import annotations

import pytest

from griphogram.types import (
    AggregationStrategy,
    EdgeDescriptor,
    EdgeStyle,
    Particle,
    ParticleShape,
    RenderConfig,
)


class TestParticleShape:
    def test_is_str_enum(self):
        assert isinstance(ParticleShape.CIRCLE, str)
        assert ParticleShape.CIRCLE == "circle"

    def test_all_variants_unique(self):
        values = [s.value for s in ParticleShape]
        assert len(values) == len(set(values)) == 10

    def test_membership(self):
        assert "hexagon" in ParticleShape._value2member_map_


class TestEdgeStyle:
    def test_frozen(self):
        es = EdgeStyle(color=(255, 0, 0), shape=ParticleShape.CIRCLE)
        with pytest.raises(AttributeError):
            es.color = (0, 0, 0)  # type: ignore[misc]

    def test_slots(self):
        es = EdgeStyle(color=(255, 0, 0), shape=ParticleShape.CIRCLE)
        assert not hasattr(es, "__dict__")


class TestParticle:
    def test_creation(self):
        p = Particle(x=1.0, y=2.0, color=(255, 0, 0), shape=ParticleShape.STAR4)
        assert p.x == 1.0
        assert p.shape == ParticleShape.STAR4


class TestEdgeDescriptor:
    def test_key_is_canonical(self):
        ed = EdgeDescriptor(
            src_idx=3, dst_idx=1, weight=0.5,
            style=EdgeStyle((0, 0, 0), ParticleShape.CIRCLE),
            bezier_fn=lambda t: (t, t),
        )
        assert ed.key == (1, 3)  # always (min, max)


class TestRenderConfig:
    def test_defaults(self):
        rc = RenderConfig()
        assert rc.width == 800
        assert rc.height == 600
        assert rc.scale == 2
        assert rc.rw == 1600
        assert rc.rh == 1200

    def test_total_frames(self):
        rc = RenderConfig(fps=10, duration=3.0)
        assert rc.total_frames == 30

    def test_frame_ms(self):
        rc = RenderConfig(fps=20)
        assert rc.frame_ms == 50


class TestAggregationStrategyProtocol:
    def test_protocol_is_runtime_checkable(self):
        """Verify that the Protocol can be used with isinstance()."""
        from griphogram.strategy import AllReduceStrategy
        # Structural subtyping: AllReduceStrategy has all required members
        assert isinstance(AllReduceStrategy(), AggregationStrategy)
