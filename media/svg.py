"""Minimal SVG building blocks shared by the media generators."""

import colorsys
from typing import Final

INDENT: Final[str] = "  "


def escape(text: str) -> str:
    """Escape the five characters that cannot appear literally in SVG markup."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def hsl(hue: float, saturation: float, lightness: float) -> str:
    """Convert an HSL triple (hue in turns, others 0..1) to a hex color."""
    red, green, blue = colorsys.hls_to_rgb(hue % 1.0, lightness, saturation)
    return f"#{round(red * 255):02x}{round(green * 255):02x}{round(blue * 255):02x}"


def polygon(points: list[tuple[float, float]], fill: str, opacity: float) -> str:
    """Render a filled polygon from absolute coordinates."""
    coordinates = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f'<polygon points="{coordinates}" fill="{fill}" fill-opacity="{opacity:.3f}"/>'


def text(content: str, x: float, y: float, fill: str, size: float, family: str, weight: str) -> str:
    """Render a single line of text anchored at its left baseline."""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-size="{size:.1f}" '
        f'font-family="{family}" font-weight="{weight}" '
        f'xml:space="preserve">{escape(content)}</text>'
    )


def document(width: int, height: int, title: str, body: list[str]) -> str:
    """Wrap rendered elements in a self-contained, accessible SVG document."""
    lines = "\n".join(f"{INDENT}{line}" for line in body)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="{escape(title)}">\n'
        f"{INDENT}<title>{escape(title)}</title>\n"
        f"{lines}\n"
        f"</svg>\n"
    )
