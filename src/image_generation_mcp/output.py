"""Write generated images to the output directory."""

import secrets
from datetime import datetime
from pathlib import Path
from typing import Final

_EXTENSIONS: Final[dict[str, str]] = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/bmp": ".bmp",
    "image/heic": ".heic",
    "image/heif": ".heif",
    "image/tiff": ".tiff",
}


def write_image(out_dir: Path, data: bytes, mime_type: str) -> Path:
    """Save image bytes under a timestamped unique name and return the absolute path."""
    extension = _EXTENSIONS.get(mime_type)
    if extension is None:
        raise ValueError(f"Provider returned unsupported image type {mime_type!r}")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = out_dir / f"{stamp}-{secrets.token_hex(2)}{extension}"
    path.write_bytes(data)
    return path.resolve()
