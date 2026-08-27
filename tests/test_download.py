"""Reference image downloads."""

from collections.abc import AsyncIterator, Callable
from typing import Any

import httpx
import pytest

from image_generation_mcp import download
from image_generation_mcp.download import MAX_DOWNLOAD_BYTES, download_image

Handler = Callable[[httpx.Request], httpx.Response]
InstallHandler = Callable[[Handler], None]


@pytest.fixture
def mock_http(monkeypatch: pytest.MonkeyPatch) -> InstallHandler:
    """Route every AsyncClient through a MockTransport running the given handler."""

    def install(handler: Handler) -> None:
        original = httpx.AsyncClient.__init__

        def patched(self: httpx.AsyncClient, **kwargs: Any) -> None:
            original(self, transport=httpx.MockTransport(handler), **kwargs)

        monkeypatch.setattr(httpx.AsyncClient, "__init__", patched)

    return install


async def _stream(total: int, chunk: int) -> AsyncIterator[bytes]:
    for offset in range(0, total, chunk):
        yield b"x" * min(chunk, total - offset)


async def test_downloads_body(mock_http: InstallHandler, pixel_png: bytes) -> None:
    mock_http(lambda request: httpx.Response(200, content=pixel_png))
    assert await download_image("https://example.test/a.png") == pixel_png


async def test_rejects_declared_oversize(mock_http: InstallHandler) -> None:
    mock_http(
        lambda request: httpx.Response(
            200, content=b"x", headers={"content-length": str(MAX_DOWNLOAD_BYTES + 1)}
        )
    )
    with pytest.raises(ValueError, match="over the"):
        await download_image("https://example.test/big.png")


async def test_aborts_mid_stream_without_content_length(
    mock_http: InstallHandler, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(download, "MAX_DOWNLOAD_BYTES", 8)
    mock_http(lambda request: httpx.Response(200, content=_stream(64, 4)))
    # "is over N" proves the abort came from the streaming loop, not a content-length header.
    with pytest.raises(ValueError, match="is over 12 bytes"):
        await download_image("https://example.test/chunked.png")


async def test_raises_on_http_error(mock_http: InstallHandler) -> None:
    mock_http(lambda request: httpx.Response(404))
    with pytest.raises(httpx.HTTPStatusError):
        await download_image("https://example.test/missing.png")
