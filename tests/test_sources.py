"""Reference image resolution."""

import base64
from pathlib import Path

import pytest

from image_generation_mcp.sources import (
    MAX_SOURCES,
    detect_mime_type,
    resolve_source,
    resolve_sources,
)


async def test_resolves_local_file(pixel_file: Path, pixel_png: bytes) -> None:
    part = await resolve_source(str(pixel_file))
    assert part.data == pixel_png
    assert part.mime_type == "image/png"


async def test_resolves_bare_base64(pixel_png: bytes) -> None:
    part = await resolve_source(base64.b64encode(pixel_png).decode("ascii"))
    assert part.data == pixel_png


async def test_resolves_data_uri(pixel_png: bytes) -> None:
    encoded = base64.b64encode(pixel_png).decode("ascii")
    part = await resolve_source(f"data:image/png;base64,{encoded}")
    assert part.data == pixel_png


async def test_missing_path_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        await resolve_source(str(tmp_path / "nope.png"))


async def test_non_image_bytes_raise(pixel_png: bytes) -> None:
    with pytest.raises(ValueError, match="Unrecognized image format"):
        await resolve_source(base64.b64encode(b"not an image at all").decode("ascii"))


async def test_too_many_sources(pixel_file: Path) -> None:
    with pytest.raises(ValueError, match="At most 4"):
        await resolve_sources([str(pixel_file)] * (MAX_SOURCES + 1))


def test_detects_webp() -> None:
    assert detect_mime_type(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "image/webp"


async def test_resolves_base64_containing_slash(pixel_png: bytes) -> None:
    # Base64 payloads routinely contain "/", which must not be read as a path separator.
    blob = pixel_png + b"\xff" * 12
    encoded = base64.b64encode(blob).decode("ascii")
    assert "/" in encoded
    assert (await resolve_source(encoded)).data == blob


async def test_existing_file_wins_over_base64_shape(tmp_path: Path, pixel_png: bytes) -> None:
    path = tmp_path / "QUJDRA=="
    path.write_bytes(pixel_png)
    assert (await resolve_source(str(path))).data == pixel_png


async def test_short_garbage_reports_missing_file() -> None:
    with pytest.raises(FileNotFoundError, match="not-an-image"):
        await resolve_source("not-an-image")


async def test_long_base64_is_not_probed_as_a_path(pixel_png: bytes) -> None:
    # A payload longer than the OS filename limit must not blow up in stat().
    blob = pixel_png + bytes(range(256)) * 4
    encoded = base64.b64encode(blob).decode("ascii")
    assert len(encoded) > 1024
    assert (await resolve_source(encoded)).data == blob
