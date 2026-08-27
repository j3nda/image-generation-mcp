"""OpenAI provider request shape and response handling."""

import base64
from typing import Any

import pytest

from image_generation_mcp.openai_provider import OpenAIProvider
from image_generation_mcp.types import ImagePart


class RecordingImages:
    """Stands in for client.images, capturing kwargs and returning a canned response."""

    def __init__(self, payload: str | None) -> None:
        self._payload = payload
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def generate(self, **kwargs: Any) -> Any:
        self.calls.append(("generate", kwargs))
        return self._response()

    async def edit(self, **kwargs: Any) -> Any:
        self.calls.append(("edit", kwargs))
        return self._response()

    def _response(self) -> Any:
        datum = type("Datum", (), {"b64_json": self._payload})()
        return type(
            "Response",
            (),
            {"data": [datum], "model_dump_json": lambda self: "{}"},
        )()


@pytest.fixture
def provider(monkeypatch: pytest.MonkeyPatch, pixel_png: bytes) -> OpenAIProvider:
    instance = OpenAIProvider("key", "gpt-image-2")
    images = RecordingImages(base64.b64encode(pixel_png).decode("ascii"))
    monkeypatch.setattr(instance, "_client", type("Client", (), {"images": images})())
    return instance


def calls(provider: OpenAIProvider) -> list[tuple[str, dict[str, Any]]]:
    return provider._client.images.calls  # type: ignore[attr-defined,no-any-return]


async def test_generate_without_sources(provider: OpenAIProvider, pixel_png: bytes) -> None:
    result = await provider.generate("a cat", [], "16:9")
    assert result.data == pixel_png
    assert result.mime_type == "image/png"
    method, kwargs = calls(provider)[0]
    assert method == "generate"
    assert kwargs["size"] == "1536x1024"
    assert kwargs["output_format"] == "png"
    assert "input_fidelity" not in kwargs


async def test_edit_with_sources(provider: OpenAIProvider, pixel_png: bytes) -> None:
    await provider.generate("restyle", [ImagePart(pixel_png, "image/jpeg")], "9:16")
    method, kwargs = calls(provider)[0]
    assert method == "edit"
    assert kwargs["size"] == "1024x1536"
    assert kwargs["image"] == [("reference-0.jpg", pixel_png, "image/jpeg")]
    assert "input_fidelity" not in kwargs


async def test_unsupported_reference_format(provider: OpenAIProvider, pixel_png: bytes) -> None:
    with pytest.raises(ValueError, match="reference images must be one of"):
        await provider.generate("x", [ImagePart(pixel_png, "image/gif")], "1:1")


async def test_missing_payload_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    instance = OpenAIProvider("key", "gpt-image-2")
    images = RecordingImages(None)
    monkeypatch.setattr(instance, "_client", type("Client", (), {"images": images})())
    with pytest.raises(RuntimeError, match="returned no image data"):
        await instance.generate("a cat", [], "1:1")
