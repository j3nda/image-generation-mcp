"""MCP server exposing a single image generation tool."""

import logging
import time

from mcp.server.mcpserver import MCPServer

from .aspect import validate_aspect_ratio
from .config import load_config
from .output import write_image
from .registry import select_provider
from .sources import resolve_sources

logger = logging.getLogger(__name__)

mcp = MCPServer(name="image-generation")


@mcp.tool()
async def generate_image(
    prompt: str,
    images: list[str] | None = None,
    aspect_ratio: str = "1:1",
) -> str:
    """Generate an image from a text prompt and optional reference images.

    Args:
        prompt: What the image should show.
        images: Up to 4 reference images, each a local file path, an http(s) URL,
            or base64-encoded image data.
        aspect_ratio: One of 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9.

    Returns:
        The absolute path of the generated image file.
    """
    ratio = validate_aspect_ratio(aspect_ratio)
    sources = await resolve_sources(images or [])
    config = load_config()
    provider = select_provider(config)
    started = time.monotonic()
    generated = await provider.generate(prompt, sources, ratio)
    path = write_image(config.out_dir, generated.data, generated.mime_type)
    logger.info(
        "generated image provider=%s aspect_ratio=%s sources=%d duration_ms=%d path=%s",
        provider.label,
        ratio,
        len(sources),
        round((time.monotonic() - started) * 1000),
        path,
    )
    return str(path)
