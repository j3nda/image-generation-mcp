"""Generate the project logo: a procedural iris whose palette derives from the project name.

Every coordinate and colour is computed — nothing is hand-drawn. The blade geometry
comes from polar sampling, and the hue wheel is seeded by a hash of PROJECT, so the
same name always yields the same logo.

Run: uv run python media/generate_logo.py
"""

import hashlib
import math
from pathlib import Path
from typing import Final

from svg import document, hsl, polygon

PROJECT: Final[str] = "image-generation-mcp"
SIZE: Final[int] = 512
BLADES: Final[int] = 6
OUTER: Final[float] = 196.0
INNER: Final[float] = 62.0
TWIST: Final[float] = 0.62


def seed_hue() -> float:
    """Derive a base hue in turns from the project name."""
    digest = hashlib.sha256(PROJECT.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") / 0xFFFFFFFF


def polar(radius: float, angle: float) -> tuple[float, float]:
    """Map polar coordinates to the centre-origin canvas."""
    centre = SIZE / 2
    return (centre + radius * math.cos(angle), centre + radius * math.sin(angle))


def blade(index: int) -> list[tuple[float, float]]:
    """Build one iris blade as a quad spanning the outer arc down to the aperture."""
    step = 2 * math.pi / BLADES
    start = index * step
    return [
        polar(OUTER, start),
        polar(OUTER, start + step),
        polar(INNER, start + step + TWIST),
        polar(INNER, start + TWIST),
    ]


def defs(base: float) -> str:
    """Background and aperture gradients, both keyed off the seeded hue."""
    return (
        "<defs>"
        '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{hsl(base + 0.52, 0.55, 0.16)}"/>'
        f'<stop offset="1" stop-color="{hsl(base + 0.62, 0.60, 0.07)}"/>'
        "</linearGradient>"
        '<radialGradient id="core">'
        f'<stop offset="0" stop-color="{hsl(base + 0.08, 0.95, 0.86)}"/>'
        f'<stop offset="1" stop-color="{hsl(base, 0.90, 0.55)}" stop-opacity="0"/>'
        "</radialGradient>"
        "</defs>"
    )


def build() -> str:
    """Assemble the full logo document."""
    base = seed_hue()
    centre = SIZE / 2
    body = [
        defs(base),
        f'<rect width="{SIZE}" height="{SIZE}" rx="112" fill="url(#bg)"/>',
        f'<circle cx="{centre}" cy="{centre}" r="{OUTER + 14}" fill="none" '
        f'stroke="{hsl(base + 0.05, 0.70, 0.62)}" stroke-opacity="0.35" stroke-width="3"/>',
    ]
    for index in range(BLADES):
        hue = base + index / (BLADES * 1.7)
        body.append(polygon(blade(index), hsl(hue, 0.82, 0.60), 0.80))
    body.extend(
        [
            f'<circle cx="{centre}" cy="{centre}" r="{INNER + 34}" fill="url(#core)"/>',
            f'<circle cx="{centre}" cy="{centre}" r="{INNER * 0.42:.1f}" '
            f'fill="{hsl(base + 0.10, 1.0, 0.94)}"/>',
        ]
    )
    return document(SIZE, SIZE, f"{PROJECT} logo", body)


if __name__ == "__main__":
    output = Path(__file__).parent / "logo.svg"
    output.write_text(build(), encoding="utf-8")
    print(f"wrote {output}")
