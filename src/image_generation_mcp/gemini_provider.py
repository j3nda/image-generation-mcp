"""Gemini image generation via the Interactions API."""

import base64
from typing import Any

from google import genai

from .types import GeneratedImage, ImagePart


class GeminiProvider:
    """Connector to the Gemini Interactions API."""

    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    @property
    def label(self) -> str:
        return f"gemini/{self._model}"

    async def generate(
        self, prompt: str, sources: list[ImagePart], aspect_ratio: str
    ) -> GeneratedImage:
        """Generate one image and return its bytes with the MIME type Gemini reported."""
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        content.extend(
            {
                "type": "image",
                "data": base64.b64encode(part.data).decode("ascii"),
                "mime_type": part.mime_type,
            }
            for part in sources
        )
        interaction = await self._client.aio.interactions.create(
            model=self._model,
            input=content,
            response_format={"type": "image", "aspect_ratio": aspect_ratio},
        )
        # create() is typed as Interaction | AsyncStream and reached through **body: Any,
        # so the response is read defensively rather than through the union's attributes.
        image = getattr(interaction, "output_image", None)
        if image is None or image.data is None:
            raise RuntimeError(
                f"{self.label} returned no image. "
                f"status={getattr(interaction, 'status', None)!r} "
                f"errors={getattr(interaction, 'errors', None)!r} "
                f"output_text={getattr(interaction, 'output_text', None)!r}"
            )
        return GeneratedImage(
            data=base64.b64decode(image.data),
            mime_type=image.mime_type or "image/png",
        )
