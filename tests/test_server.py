"""End-to-end tool flow with a stubbed provider."""

import base64
import json
from pathlib import Path

import pytest

from image_generation_mcp.config import Config
from image_generation_mcp.server import generate_image
from image_generation_mcp.types import GeneratedImage, ImagePart


class StubProvider:
    """Records what the tool passed down and returns fixed bytes."""

    def __init__(self, data: bytes) -> None:
        self._data = data
        self.calls: list[tuple[str, list[ImagePart], str]] = []

    @property
    def label(self) -> str:
        return "stub/model"

    async def generate(
        self, prompt: str, sources: list[ImagePart], aspect_ratio: str
    ) -> GeneratedImage:
        self.calls.append((prompt, sources, aspect_ratio))
        return GeneratedImage(data=self._data, mime_type="image/png")


@pytest.fixture
def stub(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, pixel_png: bytes) -> StubProvider:
    provider = StubProvider(pixel_png)
    config = Config(
        gemini_api_key="k",
        openai_api_key=None,
        provider=None,
        gemini_model="m",
        openai_model="m",
        out_dir=tmp_path / "out",
        transport="stdio",
        port=8000,
    )
    monkeypatch.setattr("image_generation_mcp.server.load_config", lambda: config)
    monkeypatch.setattr("image_generation_mcp.server.select_provider", lambda _: provider)
    return provider


async def test_returns_path_of_written_file(stub: StubProvider, pixel_png: bytes) -> None:
    result = Path(await generate_image("a cat"))
    assert result.read_bytes() == pixel_png
    assert stub.calls == [("a cat", [], "1:1")]


async def test_passes_reference_images(stub: StubProvider, pixel_file: Path) -> None:
    await generate_image("restyle", images=[str(pixel_file)], aspect_ratio="16:9")
    prompt, sources, ratio = stub.calls[0]
    assert (prompt, ratio) == ("restyle", "16:9")
    assert [part.mime_type for part in sources] == ["image/png"]


async def test_invalid_aspect_ratio_raises(stub: StubProvider) -> None:
    with pytest.raises(ValueError, match="Unsupported aspect_ratio"):
        await generate_image("a cat", aspect_ratio="7:3")
    assert stub.calls == []


async def test_writes_sidecar_next_to_image(stub: StubProvider, pixel_file: Path) -> None:
    result = Path(
        await generate_image(
            "a tile",
            images=[str(pixel_file)],
            parent=str(pixel_file),
            intent="top-down tile, readable at 64px",
        )
    )
    sidecar = json.loads(result.with_suffix(".json").read_text())
    assert sidecar["image"] == result.name
    assert sidecar["prompt"] == "a tile"
    assert sidecar["intent"] == "top-down tile, readable at 64px"
    assert sidecar["references"] == [str(pixel_file.resolve())]
    assert sidecar["parent"] == str(pixel_file.resolve())
    assert (sidecar["provider"], sidecar["model"]) == ("stub", "model")
    assert "T" in sidecar["date"]
    # parent goes to the model first, before the references
    assert len(stub.calls[0][1]) == 2


async def test_sidecar_without_parent_or_intent(stub: StubProvider) -> None:
    result = Path(await generate_image("a cat"))
    sidecar = json.loads(result.with_suffix(".json").read_text())
    assert (sidecar["parent"], sidecar["intent"], sidecar["references"]) == (None, None, [])


async def test_sidecar_does_not_inline_base64(stub: StubProvider, pixel_png: bytes) -> None:
    payload = base64.b64encode(pixel_png).decode()
    result = Path(await generate_image("x", images=[payload]))
    sidecar = json.loads(result.with_suffix(".json").read_text())
    assert sidecar["references"] == [f"<inline base64 image, {len(payload)} chars>"]
