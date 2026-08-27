"""Generate the usage screenshot: a Claude Code session driving this MCP server.

The frame, the prompt gutter and every line position are computed from the SESSION
data below, so the image is regenerated rather than edited. The numbers shown come
from a real run: gpt-image-2, 1536x1024, 28.6 s.

Run: uv run python media/generate_screenshot.py
"""

from pathlib import Path
from typing import Final

from svg import document, text

WIDTH: Final[int] = 940
PADDING: Final[float] = 26.0
TITLEBAR: Final[float] = 40.0
LINE_HEIGHT: Final[float] = 23.0
FONT_SIZE: Final[float] = 14.5
MONO: Final[str] = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

PALETTE: Final[dict[str, str]] = {
    "chrome": "#161b22",
    "screen": "#0d1117",
    "border": "#30363d",
    "muted": "#8b949e",
    "body": "#e6edf3",
    "user": "#ffffff",
    "tool": "#d2a8ff",
    "path": "#7ee787",
    "accent": "#f0883e",
}

# (style, text) - style selects colour and weight.
SESSION: Final[tuple[tuple[str, str], ...]] = (
    ("user", "> draw me a red bicycle on a white background, 16:9"),
    ("blank", ""),
    ("body", "  I'll generate that with the image-generation server."),
    ("blank", ""),
    ("tool", "● image-generation - generate_image (MCP)"),
    ("muted", '  └  prompt: "a red bicycle on a white background"'),
    ("muted", '     aspect_ratio: "16:9"'),
    ("path", "  └  /Users/you/project/out/20260827-172746-c9b3.png"),
    ("blank", ""),
    ("body", "  Done. 1536x1024 PNG via gpt-image-2, 28.6s. The file is on disk -"),
    ("body", "  only the path came back, so the image never entered the context."),
    ("blank", ""),
    ("user", "> now make the frame blue, keep everything else the same"),
    ("blank", ""),
    ("tool", "● image-generation - generate_image (MCP)"),
    ("muted", '  └  images: ["out/20260827-172746-c9b3.png"]'),
    ("path", "  └  /Users/you/project/out/20260827-173101-6ac3.png"),
)

STYLES: Final[dict[str, tuple[str, str]]] = {
    "user": (PALETTE["user"], "600"),
    "body": (PALETTE["body"], "400"),
    "muted": (PALETTE["muted"], "400"),
    "tool": (PALETTE["tool"], "500"),
    "path": (PALETTE["path"], "400"),
}


def chrome(height: float) -> list[str]:
    """Window frame: rounded shell, title bar, traffic lights, centred title."""
    lights = [
        f'<circle cx="{22 + index * 20}" cy="{TITLEBAR / 2}" r="6" fill="{colour}"/>'
        for index, colour in enumerate(("#ff5f57", "#febc2e", "#28c840"))
    ]
    return [
        f'<rect width="{WIDTH}" height="{height}" rx="12" fill="{PALETTE["screen"]}" '
        f'stroke="{PALETTE["border"]}"/>',
        f'<path d="M0 12a12 12 0 0 1 12-12h{WIDTH - 24}a12 12 0 0 1 12 12v{TITLEBAR - 12}H0z" '
        f'fill="{PALETTE["chrome"]}"/>',
        f'<line x1="0" y1="{TITLEBAR}" x2="{WIDTH}" y2="{TITLEBAR}" stroke="{PALETTE["border"]}"/>',
        *lights,
        f'<text x="{WIDTH / 2}" y="{TITLEBAR / 2 + 4.5}" fill="{PALETTE["muted"]}" '
        f'font-size="12.5" font-family="{MONO}" text-anchor="middle">'
        "claude - image-generation-mcp</text>",
    ]


def build() -> str:
    """Assemble the terminal document."""
    height = TITLEBAR + PADDING * 2 + LINE_HEIGHT * len(SESSION)
    body = chrome(height)
    baseline = TITLEBAR + PADDING + FONT_SIZE
    for index, (style, content) in enumerate(SESSION):
        if style == "blank":
            continue
        colour, weight = STYLES[style]
        y = baseline + index * LINE_HEIGHT
        body.append(text(content, PADDING, y, colour, FONT_SIZE, MONO, weight))
    return document(WIDTH, round(height), "Claude Code generating an image", body)


if __name__ == "__main__":
    output = Path(__file__).parent / "screenshot.svg"
    output.write_text(build(), encoding="utf-8")
    print(f"wrote {output}")
