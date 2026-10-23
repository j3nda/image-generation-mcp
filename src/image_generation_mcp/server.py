"""MCP server exposing a single image generation tool."""

import logging
import time

from mcp.server.mcpserver import MCPServer

from .aspect import validate_aspect_ratio
from .config import load_config
from .output import write_image
from .registry import select_provider
from .sidecar import write_sidecar
from .sources import resolve_sources

logger = logging.getLogger(__name__)

mcp = MCPServer(name="image-generation")


@mcp.tool()
async def generate_image(
    prompt: str,
    images: list[str] | None = None,
    aspect_ratio: str = "1:1",
    parent: str | None = None,
    intent: str | None = None,
) -> str:
    """Generate an image from a text prompt and optional reference images.

    Args:
        prompt: What the image should show.
        images: Up to 4 reference images, each a local file path, an http(s) URL,
            or base64-encoded image data.
        aspect_ratio: One of 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9.
        parent: The image being edited, if this is an edit. Same formats as `images`;
            it is sent to the model first and counts toward the 4-image limit.
        intent: One sentence on what the image is for, e.g.
            "top-down tile, transparent background, readable at 64px".

    Returns:
        The absolute path of the generated image file. A sidecar `<name>.json` with
        prompt, references, parent, date and intent is written next to it.
    """
    ratio = validate_aspect_ratio(aspect_ratio)
    references = images or []
    sources = await resolve_sources([parent, *references] if parent else references)
    config = load_config()
    provider = select_provider(config)
    started = time.monotonic()
    generated = await provider.generate(prompt, sources, ratio)
    path = write_image(config.out_dir, generated.data, generated.mime_type)
    write_sidecar(
        path,
        prompt=prompt,
        references=references,
        parent=parent,
        intent=intent,
        provider=provider.label,
        aspect_ratio=ratio,
    )
    logger.info(
        "generated image provider=%s aspect_ratio=%s sources=%d duration_ms=%d path=%s",
        provider.label,
        ratio,
        len(sources),
        round((time.monotonic() - started) * 1000),
        path,
    )
    return str(path)
