"""
Particle shape renderers using **Flyweight** pattern + ``match/case`` dispatch.

Each ``ParticleShape`` enum variant maps to a drawing routine.  The renderer
is stateless (pure function of position, colour, shape, size) — the flyweight
here is the *absence* of per-particle state: all rendering is shared logic.

See: https://refactoring.guru/design-patterns/flyweight
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw

from griphogram.types import Color, ParticleShape


def draw_shape(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    color: Color,
    shape: ParticleShape,
    size: float = 10,
    alpha: int = 220,
) -> None:
    """
    Render a single particle glyph centred at ``(cx, cy)``.

    Uses ``match/case`` (3.10+) for exhaustive, type-safe dispatch over
    the ``ParticleShape`` enum.
    """
    s = size
    r, g, b = color
    fill = (r, g, b, alpha)

    match shape:
        case ParticleShape.CIRCLE:
            draw.ellipse([cx - s, cy - s, cx + s, cy + s], fill=fill)

        case ParticleShape.SQUARE:
            hs = s * 0.82
            draw.rectangle([cx - hs, cy - hs, cx + hs, cy + hs], fill=fill)

        case ParticleShape.TRIANGLE_UP:
            draw.polygon(
                [(cx, cy - s), (cx - s * 0.95, cy + s * 0.7), (cx + s * 0.95, cy + s * 0.7)],
                fill=fill,
            )

        case ParticleShape.TRIANGLE_DOWN:
            draw.polygon(
                [(cx, cy + s), (cx - s * 0.95, cy - s * 0.7), (cx + s * 0.95, cy - s * 0.7)],
                fill=fill,
            )

        case ParticleShape.DIAMOND:
            draw.polygon(
                [(cx, cy - s), (cx + s * 0.7, cy), (cx, cy + s), (cx - s * 0.7, cy)],
                fill=fill,
            )

        case ParticleShape.HEXAGON:
            pts = [
                (cx + s * 0.85 * math.cos(math.pi / 6 + i * math.pi / 3),
                 cy + s * 0.85 * math.sin(math.pi / 6 + i * math.pi / 3))
                for i in range(6)
            ]
            draw.polygon(pts, fill=fill)

        case ParticleShape.CROSS:
            t = s * 0.35
            draw.rectangle([cx - t, cy - s * 0.8, cx + t, cy + s * 0.8], fill=fill)
            draw.rectangle([cx - s * 0.8, cy - t, cx + s * 0.8, cy + t], fill=fill)

        case ParticleShape.PENTAGON:
            pts = [
                (cx + s * 0.85 * math.cos(-math.pi / 2 + i * 2 * math.pi / 5),
                 cy + s * 0.85 * math.sin(-math.pi / 2 + i * 2 * math.pi / 5))
                for i in range(5)
            ]
            draw.polygon(pts, fill=fill)

        case ParticleShape.STAR4:
            pts = []
            for i in range(8):
                ang = -math.pi / 2 + i * math.pi / 4
                rv = s * 0.9 if i % 2 == 0 else s * 0.4
                pts.append((cx + rv * math.cos(ang), cy + rv * math.sin(ang)))
            draw.polygon(pts, fill=fill)

        case ParticleShape.ARROW_RIGHT:
            draw.polygon(
                [
                    (cx - s * 0.7, cy - s * 0.7),
                    (cx + s * 0.7, cy),
                    (cx - s * 0.7, cy + s * 0.7),
                    (cx - s * 0.2, cy),
                ],
                fill=fill,
            )


def draw_particle_with_glow(
    img: Image.Image,
    cx: float,
    cy: float,
    color: Color,
    shape: ParticleShape,
    size: float = 10,
) -> None:
    """Composite a particle glyph with concentric glow halos onto *img*."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    # Outer glow
    gr = size * 2.8
    od.ellipse([cx - gr, cy - gr, cx + gr, cy + gr], fill=(*color, 18))
    # Inner glow
    mr = size * 1.8
    od.ellipse([cx - mr, cy - mr, cx + mr, cy + mr], fill=(*color, 45))
    # Core shape
    draw_shape(od, cx, cy, color, shape, size)

    img.alpha_composite(overlay)
