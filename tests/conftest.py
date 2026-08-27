"""Shared fixtures."""

import base64
from pathlib import Path

import pytest

PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


@pytest.fixture
def pixel_png() -> bytes:
    return PIXEL_PNG


@pytest.fixture
def pixel_file(tmp_path: Path) -> Path:
    path = tmp_path / "pixel.png"
    path.write_bytes(PIXEL_PNG)
    return path
