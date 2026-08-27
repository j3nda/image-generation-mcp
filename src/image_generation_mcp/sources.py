"""Resolve reference image specs (file path, http(s) URL, or base64) into bytes."""

import asyncio
import base64
import binascii
import re
from pathlib import Path
from typing import Final

from .download import download_image
from .types import ImagePart

MAX_SOURCES: Final[int] = 4

_BASE64_PATTERN: Final[re.Pattern[str]] = re.compile(r"[A-Za-z0-9+/]+={0,2}")
_MAGIC: Final[tuple[tuple[bytes, str], ...]] = (
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"BM", "image/bmp"),
)


def _abbreviate(spec: str) -> str:
    return spec if len(spec) <= 80 else f"{spec[:80]}... ({len(spec)} chars)"


def detect_mime_type(data: bytes) -> str:
    """Identify an image MIME type from its magic bytes."""
    for prefix, mime_type in _MAGIC:
        if data.startswith(prefix):
            return mime_type
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    raise ValueError(f"Unrecognized image format (first bytes: {data[:12]!r})")


def looks_like_base64(spec: str) -> bool:
    """Whether a spec has the shape of a base64 payload rather than a path."""
    return len(spec) >= 16 and len(spec) % 4 == 0 and _BASE64_PATTERN.fullmatch(spec) is not None


def _is_existing_file(path: Path) -> bool:
    """Whether the path points at a file, treating unusable paths as simply absent.

    A long base64 payload is a valid string but an illegal filename, and stat()
    raises ENAMETOOLONG for it rather than reporting "not found".
    """
    try:
        return path.is_file()
    except OSError:
        return False


def _decode_base64(spec: str) -> bytes:
    payload = spec.split(",", 1)[1] if spec.startswith("data:") else spec
    try:
        return base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError(f"Invalid base64 image data: {error}") from error


async def resolve_source(spec: str) -> ImagePart:
    """Turn a single image spec into decoded bytes plus its MIME type."""
    if spec.startswith(("http://", "https://")):
        data = await download_image(spec)
    elif spec.startswith("data:"):
        data = _decode_base64(spec)
    else:
        path = Path(spec).expanduser()
        # A real file always wins; otherwise fall back to treating the spec as base64.
        if await asyncio.to_thread(_is_existing_file, path):
            data = await asyncio.to_thread(path.read_bytes)
        elif looks_like_base64(spec):
            data = _decode_base64(spec)
        else:
            raise FileNotFoundError(f"Reference image not found: {_abbreviate(spec)}")
    return ImagePart(data=data, mime_type=detect_mime_type(data))


async def resolve_sources(specs: list[str]) -> list[ImagePart]:
    """Resolve every reference image spec, enforcing the per-call limit."""
    if len(specs) > MAX_SOURCES:
        raise ValueError(f"At most {MAX_SOURCES} reference images allowed, got {len(specs)}")
    return [await resolve_source(spec) for spec in specs]
