"""Writing generated images to disk."""

import re
from pathlib import Path

import pytest

from image_generation_mcp.output import write_image


def test_writes_png_with_timestamped_name(tmp_path: Path, pixel_png: bytes) -> None:
    path = write_image(tmp_path / "out", pixel_png, "image/png")
    assert path.is_absolute()
    assert path.read_bytes() == pixel_png
    assert re.fullmatch(r"\d{8}-\d{6}-[0-9a-f]{4}\.png", path.name)


def test_jpeg_gets_jpg_extension(tmp_path: Path, pixel_png: bytes) -> None:
    assert write_image(tmp_path, pixel_png, "image/jpeg").suffix == ".jpg"


def test_names_do_not_collide(tmp_path: Path, pixel_png: bytes) -> None:
    paths = {write_image(tmp_path, pixel_png, "image/png") for _ in range(20)}
    assert len(paths) == 20


def test_heic_is_kept_rather_than_discarded(tmp_path: Path, pixel_png: bytes) -> None:
    assert write_image(tmp_path, pixel_png, "image/heic").suffix == ".heic"


def test_unsupported_mime_type_raises(tmp_path: Path, pixel_png: bytes) -> None:
    with pytest.raises(ValueError, match="unsupported image type"):
        write_image(tmp_path, pixel_png, "image/svg+xml")
