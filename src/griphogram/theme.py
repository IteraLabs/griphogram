"""
Visual theme configuration.

Centralises every colour, font path, and size constant into a single
frozen dataclass.  Swap themes by constructing a different ``Theme``
instance — the renderer is parametric on it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from griphogram.types import Color, EdgeStyle, ParticleShape

# ── Defaults ──────────────────────────────────────────────────────────────────

_DEJAVU = Path("/usr/share/fonts/truetype/dejavu")

_DEFAULT_EDGE_STYLES: list[EdgeStyle] = [
    EdgeStyle((255, 100, 100), ParticleShape.CIRCLE),
    EdgeStyle((100, 220, 255), ParticleShape.SQUARE),
    EdgeStyle((255, 200,  60), ParticleShape.TRIANGLE_UP),
    EdgeStyle((140, 255, 140), ParticleShape.DIAMOND),
    EdgeStyle((200, 130, 255), ParticleShape.TRIANGLE_DOWN),
    EdgeStyle((255, 160,  80), ParticleShape.HEXAGON),
    EdgeStyle((100, 255, 200), ParticleShape.CROSS),
    EdgeStyle((255, 120, 200), ParticleShape.PENTAGON),
    EdgeStyle((180, 220, 100), ParticleShape.STAR4),
    EdgeStyle((120, 160, 255), ParticleShape.ARROW_RIGHT),
]


# ── Theme ─────────────────────────────────────────────────────────────────────


@dataclass(slots=True, frozen=True)
class Theme:
    """
    Complete visual theme.

    Every rendering constant lives here so the ``GIFRenderer`` carries
    zero hard-coded colours.  Construct alternative themes by passing
    different values at creation time.
    """

    # Canvas
    background: Color = (10, 14, 28)
    edge_base: Color = (50, 60, 85)
    edge_dim: Color = (22, 28, 42)

    # Nodes
    node_fill: Color = (20, 35, 65)
    node_stroke: Color = (80, 180, 255)
    node_ps_fill: Color = (60, 30, 10)
    node_ps_stroke: Color = (255, 160, 60)

    # Text
    title_color: Color = (230, 235, 245)
    text_dim: Color = (100, 110, 130)
    phase_color: Color = (255, 200, 100)
    weight_text: Color = (100, 110, 130)

    # Fonts (paths)
    font_label_path: Path = _DEJAVU / "DejaVuSansMono-Bold.ttf"
    font_title_path: Path = _DEJAVU / "DejaVuSans-Bold.ttf"
    font_body_path: Path = _DEJAVU / "DejaVuSans.ttf"
    font_mono_path: Path = _DEJAVU / "DejaVuSansMono.ttf"

    font_title_size: int = 38
    font_subtitle_size: int = 22
    font_label_size: int = 28
    font_phase_size: int = 26
    font_weight_size: int = 18
    font_legend_size: int = 17

    # Edge style palette (cycled for edges beyond len)
    edge_styles: tuple[EdgeStyle, ...] = tuple(_DEFAULT_EDGE_STYLES)

    def edge_style_for(self, index: int) -> EdgeStyle:
        """Return edge style, cycling if ``index >= len(edge_styles)``."""
        return self.edge_styles[index % len(self.edge_styles)]
