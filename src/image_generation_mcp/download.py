"""Download reference images over http(s) with a hard size cap."""

from typing import Final

import httpx

MAX_DOWNLOAD_BYTES: Final[int] = 20 * 1024 * 1024
DOWNLOAD_TIMEOUT_SECONDS: Final[float] = 30.0


def _too_large(url: str, size: int | str) -> ValueError:
    return ValueError(
        f"Reference image at {url} is {size} bytes, over the {MAX_DOWNLOAD_BYTES} byte limit"
    )


async def download_image(url: str) -> bytes:
    """Stream a URL into memory, aborting as soon as the size cap is exceeded."""
    async with (
        httpx.AsyncClient(timeout=DOWNLOAD_TIMEOUT_SECONDS, follow_redirects=True) as client,
        client.stream("GET", url) as response,
    ):
        response.raise_for_status()
        declared = response.headers.get("content-length")
        if declared is not None and declared.isdigit() and int(declared) > MAX_DOWNLOAD_BYTES:
            raise _too_large(url, declared)
        chunks: list[bytes] = []
        total = 0
        async for chunk in response.aiter_bytes():
            total += len(chunk)
            if total > MAX_DOWNLOAD_BYTES:
                raise _too_large(url, f"over {total}")
            chunks.append(chunk)
    return b"".join(chunks)
