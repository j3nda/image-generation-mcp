"""Gemini provider request shape and response handling."""

import base64
from typing import Any

import pytest

from image_generation_mcp.gemini_provider import GeminiProvider
from image_generation_mcp.types import ImagePart


class RecordingInteractions:
    """Stands in for client.aio.interactions, capturing kwargs."""

    def __init__(self, image: Any) -> None:
        self._image = image
        self.calls: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return type(
            "Interaction",
            (),
            {
                "output_image": self._image,
                "output_text": None,
                "status": "FAILED",
                "errors": ["blocked"],
            },
        )()


def install(
    provider: GeminiProvider, image: Any, monkeypatch: pytest.MonkeyPatch
) -> RecordingInteractions:
    interactions = RecordingInteractions(image)
    aio = type("Aio", (), {"interactions": interactions})()
    monkeypatch.setattr(provider, "_client", type("Client", (), {"aio": aio})())
    return interactions


async def test_sends_prompt_and_references(
    monkeypatch: pytest.MonkeyPatch, pixel_png: bytes
) -> None:
    provider = GeminiProvider("key", "gemini-3.1-flash-image")
    encoded = base64.b64encode(pixel_png).decode("ascii")
    image = type("Image", (), {"data": encoded, "mime_type": "image/jpeg"})()
    interactions = install(provider, image, monkeypatch)

    result = await provider.generate("a cat", [ImagePart(pixel_png, "image/png")], "21:9")

    assert result.data == pixel_png
    assert result.mime_type == "image/jpeg"
    kwargs = interactions.calls[0]
    assert kwargs["model"] == "gemini-3.1-flash-image"
    assert kwargs["response_format"] == {"type": "image", "aspect_ratio": "21:9"}
    assert kwargs["input"] == [
        {"type": "text", "text": "a cat"},
        {"type": "image", "data": encoded, "mime_type": "image/png"},
    ]


async def test_defaults_missing_mime_to_png(
    monkeypatch: pytest.MonkeyPatch, pixel_png: bytes
) -> None:
    provider = GeminiProvider("key", "m")
    encoded = base64.b64encode(pixel_png).decode("ascii")
    install(provider, type("Image", (), {"data": encoded, "mime_type": None})(), monkeypatch)
    assert (await provider.generate("a cat", [], "1:1")).mime_type == "image/png"


async def test_no_image_reports_status_and_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = GeminiProvider("key", "m")
    install(provider, None, monkeypatch)
    with pytest.raises(RuntimeError, match="status='FAILED' errors=\\['blocked'\\]"):
        await provider.generate("a cat", [], "1:1")
