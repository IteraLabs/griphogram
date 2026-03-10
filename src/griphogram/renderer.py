"""
GIF renderer using the **Template Method** pattern.

The ``render_frame`` pipeline defines a fixed sequence of compositing
steps (edges → weights → particles → nodes → chrome) while allowing
each step to be overridden in subclasses.

See: https://refactoring.guru/design-patterns/template-method
"""

from __future__ import annotations

import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from griphogram.graph import CurvedEdge, Graph, Node
from griphogram.particles import draw_particle_with_glow, draw_shape
from griphogram.theme import Theme
from griphogram.types import (
    AggregationStrategy,
    Color,
    RenderConfig,
)


class GIFRenderer:
    """
    Renders animated GIFs of gradient flow across a graph topology.

    Follows the **Template Method** pattern: ``render_frame`` orchestrates
    a fixed pipeline of drawing steps.  Override individual ``_draw_*``
    methods to customise without changing the pipeline order.
    """

    def __init__(
        self,
        graph: Graph,
        strategy: AggregationStrategy,
        config: RenderConfig | None = None,
        theme: Theme | None = None,
    ) -> None:
        self.graph = graph
        self.strategy = strategy
        self.config = config or RenderConfig()
        self.theme = theme or Theme()
        self._fonts = _load_fonts(self.theme)

    # ── Template method ───────────────────────────────────────────────────

    def render_frame(self, frame: int) -> Image.Image:
        """
        Render a single animation frame (Template Method).

        Pipeline order:
            1. Background
            2. Edges
            3. Weight labels
            4. Particles with glow
            5. Nodes
            6. Title + phase + progress bar
            7. Legend
        """
        cfg = self.config
        img = Image.new("RGBA", (cfg.rw, cfg.rh), (*self.theme.background, 255))
        draw = ImageDraw.Draw(img)
        total = cfg.total_frames
        descriptors = self.graph.edge_descriptors()

        # 1 — Edges
        for edge in self.graph.edges:
            alpha = self.strategy.get_edge_alpha(
                edge.src.idx,
                edge.dst.idx,
                frame,
                total,
            )
            self._draw_edge(draw, edge, alpha)

        # 2 — Weight labels
        for edge in self.graph.edges:
            alpha = self.strategy.get_edge_alpha(
                edge.src.idx,
                edge.dst.idx,
                frame,
                total,
            )
            self._draw_weight_label(draw, edge, alpha)

        # 3 — Particles
        for p in self.strategy.get_particles(descriptors, frame, total):
            draw_particle_with_glow(
                img,
                p.x,
                p.y,
                p.color,
                p.shape,
                cfg.particle_size,
            )

        # 4 — Nodes (re-acquire draw after alpha_composite)
        draw = ImageDraw.Draw(img)
        for node in self.graph.nodes:
            self._draw_node(draw, node)

        # 5 — Chrome
        self._draw_title(draw)
        self._draw_phase(draw, frame)
        self._draw_progress_bar(draw, frame)

        # 6 — Legend
        self._draw_legend(img)

        return img

    # ── Individual drawing steps ──────────────────────────────────────────

    def _draw_edge(self, draw: ImageDraw.ImageDraw, edge: CurvedEdge, alpha: float) -> None:
        thickness = max(2, int(4 * alpha + edge.weight * 3 * alpha))
        col = _lerp_color(self.theme.edge_dim, self.theme.edge_base, alpha)
        for a, b in _pairwise(edge.bezier_points(40)):
            draw.line([a, b], fill=col, width=thickness)

    def _draw_weight_label(
        self,
        draw: ImageDraw.ImageDraw,
        edge: CurvedEdge,
        alpha: float,
    ) -> None:
        if alpha < 0.3:
            return
        mx, my = edge.midpoint()
        cx, cy = self.config.rw / 2, self.config.rh / 2
        dx, dy = mx - cx, my - cy
        dist = max(math.sqrt(dx * dx + dy * dy), 1e-6)
        off = 20
        lx = mx + (dx / dist) * off - 18
        ly = my + (dy / dist) * off - 8
        draw.text(
            (lx, ly), f"{edge.weight:.2f}", fill=self.theme.weight_text, font=self._fonts["weight"]
        )

    def _draw_node(self, draw: ImageDraw.ImageDraw, node: Node) -> None:
        r = node.radius
        is_ld = node.is_leader
        fill = self.theme.node_ps_fill if is_ld else self.theme.node_fill
        stroke = self.theme.node_ps_stroke if is_ld else self.theme.node_stroke
        sw = 5 if is_ld else 3

        draw.ellipse(
            [node.x - r, node.y - r, node.x + r, node.y + r], fill=fill, outline=stroke, width=sw
        )
        if is_ld:
            r2 = r + 10
            draw.ellipse(
                [node.x - r2, node.y - r2, node.x + r2, node.y + r2], outline=stroke, width=2
            )

        bbox = draw.textbbox((0, 0), node.label, font=self._fonts["label"])
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(
            (node.x - tw / 2, node.y - th / 2 - 2),
            node.label,
            fill=stroke,
            font=self._fonts["label"],
        )

    def _draw_title(self, draw: ImageDraw.ImageDraw) -> None:
        rw = self.config.rw
        t = self.strategy.title
        bbox = draw.textbbox((0, 0), t, font=self._fonts["title"])
        draw.text(
            ((rw - (bbox[2] - bbox[0])) / 2, 26),
            t,
            fill=self.theme.title_color,
            font=self._fonts["title"],
        )

        s = self.strategy.subtitle
        bbox2 = draw.textbbox((0, 0), s, font=self._fonts["subtitle"])
        draw.text(
            ((rw - (bbox2[2] - bbox2[0])) / 2, 72),
            s,
            fill=self.theme.text_dim,
            font=self._fonts["subtitle"],
        )

    def _draw_phase(self, draw: ImageDraw.ImageDraw, frame: int) -> None:
        text = self.strategy.get_phase_text(frame, self.config.total_frames)
        bbox = draw.textbbox((0, 0), text, font=self._fonts["phase"])
        rw, rh = self.config.rw, self.config.rh
        draw.text(
            ((rw - (bbox[2] - bbox[0])) / 2, rh - 60),
            text,
            fill=self.theme.phase_color,
            font=self._fonts["phase"],
        )

    def _draw_progress_bar(self, draw: ImageDraw.ImageDraw, frame: int) -> None:
        rw, rh = self.config.rw, self.config.rh
        bar_x, bar_y, bar_h = 60, rh - 16, 6
        full_w = rw - 120
        frac = frame / max(self.config.total_frames - 1, 1)
        draw.rounded_rectangle(
            [bar_x, bar_y, bar_x + full_w, bar_y + bar_h], radius=3, fill=(30, 35, 55)
        )
        fill_w = int(full_w * frac)
        if fill_w > 3:
            draw.rounded_rectangle(
                [bar_x, bar_y, bar_x + fill_w, bar_y + bar_h],
                radius=3,
                fill=self.theme.phase_color,
            )

    def _draw_legend(self, img: Image.Image) -> None:
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        lx, ly = 24, self.config.rh - 330
        n_edges = len(self.graph.edges)
        box_h = 38 + n_edges * 24
        od.rounded_rectangle([lx, ly, lx + 210, ly + box_h], radius=10, fill=(15, 20, 38, 200))
        od.text(
            (lx + 14, ly + 10),
            "Edge Legend",
            fill=(180, 190, 210, 240),
            font=self._fonts["legend"],
        )

        for idx, edge in enumerate(self.graph.edges):
            row_y = ly + 38 + idx * 24
            draw_shape(od, lx + 24, row_y + 4, edge.style.color, edge.style.shape, 7)
            src_l = edge.src.label
            dst_l = edge.dst.label
            label = f"{src_l}↔{dst_l}  {edge.weight:.2f}"
            od.text(
                (lx + 42, row_y - 5), label, fill=(160, 170, 190, 220), font=self._fonts["legend"]
            )

        img.alpha_composite(overlay)

    # ── Full render ───────────────────────────────────────────────────────

    def render_gif(self, output: str | Path, *, verbose: bool = True) -> Path:
        """
        Render all frames and save as an animated GIF.

        Returns the resolved output path.
        """
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        cfg = self.config
        total = cfg.total_frames

        if verbose:
            print(f"  Rendering {self.strategy.title} ({total} frames)...")

        frames: list[Image.Image] = []
        for f in range(total):
            if verbose and f % 20 == 0:
                print(f"    frame {f}/{total}")
            img_2x = self.render_frame(f)
            img_1x = img_2x.convert("RGB").resize(
                (cfg.width, cfg.height),
                Image.Resampling.LANCZOS,
            )
            frames.append(
                img_1x.quantize(
                    colors=256,
                    method=Image.Quantize.MEDIANCUT,
                    dither=Image.Dither.NONE,
                )
            )

        frames[0].save(
            str(output),
            save_all=True,
            append_images=frames[1:],
            duration=cfg.frame_ms,
            loop=0,
            optimize=False,
        )
        size_kb = os.path.getsize(output) / 1024
        if verbose:
            print(f"  ✓ Saved: {output} ({size_kb:.0f} KB)")
        return output


# ── Helpers ───────────────────────────────────────────────────────────────────


def _lerp_color(a: Color, b: Color, t: float) -> Color:
    """Linearly interpolate between two RGB colours."""
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def _pairwise(seq: list) -> list[tuple]:
    """Yield consecutive pairs: ``[a, b, c] → [(a,b), (b,c)]``."""
    return [(seq[i], seq[i + 1]) for i in range(len(seq) - 1)]


def _load_fonts(theme: Theme) -> dict[str, ImageFont.FreeTypeFont | ImageFont.ImageFont]:
    """Load fonts from theme paths, falling back to default."""
    fonts: dict[str, ImageFont.FreeTypeFont | ImageFont.ImageFont] = {}
    _pairs = [
        ("title", theme.font_title_path, theme.font_title_size),
        ("subtitle", theme.font_body_path, theme.font_subtitle_size),
        ("label", theme.font_label_path, theme.font_label_size),
        ("phase", theme.font_body_path, theme.font_phase_size),
        ("weight", theme.font_mono_path, theme.font_weight_size),
        ("legend", theme.font_body_path, theme.font_legend_size),
    ]
    for key, path, size in _pairs:
        try:
            fonts[key] = ImageFont.truetype(str(path), size)
        except OSError:
            fonts[key] = ImageFont.load_default()
    return fonts
