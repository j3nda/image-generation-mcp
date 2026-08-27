"""Aspect ratio validation and per-provider translation."""

from typing import Final

# Ratios accepted by the Gemini Interactions API image response format.
ASPECT_RATIOS: Final[tuple[str, ...]] = (
    "1:1",
    "2:3",
    "3:2",
    "3:4",
    "4:3",
    "4:5",
    "5:4",
    "9:16",
    "16:9",
    "21:9",
)

# OpenAI only accepts three sizes, so every ratio collapses to the nearest one.
_LANDSCAPE: Final[frozenset[str]] = frozenset({"3:2", "4:3", "5:4", "16:9", "21:9"})
_PORTRAIT: Final[frozenset[str]] = frozenset({"2:3", "3:4", "4:5", "9:16"})


def validate_aspect_ratio(value: str) -> str:
    """Return the ratio unchanged, or raise ValueError listing the accepted ones."""
    if value not in ASPECT_RATIOS:
        raise ValueError(
            f"Unsupported aspect_ratio {value!r}. Supported: {', '.join(ASPECT_RATIOS)}"
        )
    return value


def openai_size(aspect_ratio: str) -> str:
    """Map a validated aspect ratio to an OpenAI image size string."""
    if aspect_ratio in _LANDSCAPE:
        return "1536x1024"
    if aspect_ratio in _PORTRAIT:
        return "1024x1536"
    return "1024x1024"
