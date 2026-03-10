"""Tests for shape renderers and particle glow compositing."""

from __future__ import annotations

from PIL import Image, ImageDraw

from griphogram.particles import draw_particle_with_glow, draw_shape
from griphogram.types import ParticleShape


class TestDrawShape:
    def test_all_shapes_render_without_error(self):
        """Smoke test: every ParticleShape variant renders on a blank canvas."""
        img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        for shape in ParticleShape:
            draw_shape(draw, 50, 50, (255, 128, 0), shape, size=10)

    def test_circle_modifies_pixels(self):
        img = Image.new("RGBA", (60, 60), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw_shape(draw, 30, 30, (255, 0, 0), ParticleShape.CIRCLE, size=10)
        # Centre pixel should be non-transparent
        px = img.getpixel((30, 30))
        assert isinstance(px, tuple)
        assert px[3] > 0, "Circle should draw at the centre"

    def test_custom_alpha(self):
        img = Image.new("RGBA", (60, 60), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw_shape(draw, 30, 30, (255, 0, 0), ParticleShape.SQUARE, size=10, alpha=100)
        px = img.getpixel((30, 30))
        assert isinstance(px, tuple)
        assert px[3] == 100


class TestDrawParticleWithGlow:
    def test_glow_extends_beyond_core(self):
        """Glow halo should colour pixels beyond the core shape radius."""
        img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        draw_particle_with_glow(img, 50, 50, (0, 200, 255), ParticleShape.CIRCLE, 8)
        # A pixel well outside the core radius (8px) but inside glow (8*2.8=22px)
        px = img.getpixel((50 + 18, 50))
        assert isinstance(px, tuple)
        assert px[3] > 0, "Glow should extend beyond core radius"
