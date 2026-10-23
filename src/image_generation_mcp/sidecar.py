"""Write a JSON sidecar recording how a generated image was made."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def describe_source(spec: str) -> str:
    """A readable record of a reference spec, without inlining base64 payloads."""
    if spec.startswith(("http://", "https://")):
        return spec
    path = Path(spec).expanduser()
    try:
        if path.is_file():
            return str(path.resolve())
    except OSError:
        pass
    return f"<inline base64 image, {len(spec)} chars>"


def write_sidecar(
    image_path: Path,
    *,
    prompt: str,
    references: list[str],
    parent: str | None,
    intent: str | None,
    provider: str,
    aspect_ratio: str,
) -> Path:
    """Save `<image stem>.json` next to the image and return its path.

    `provider` is the provider label, `<provider>/<model>`, recorded as two fields.
    """
    provider_name, _, model = provider.partition("/")
    record: dict[str, Any] = {
        "image": image_path.name,
        "date": datetime.now().astimezone().isoformat(timespec="seconds"),
        "intent": intent,
        "prompt": prompt,
        "references": [describe_source(spec) for spec in references],
        "parent": describe_source(parent) if parent else None,
        "provider": provider_name,
        "model": model or None,
        "aspect_ratio": aspect_ratio,
    }
    path = image_path.with_suffix(".json")
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
