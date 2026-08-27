"""Shared types for image inputs and provider implementations."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ImagePart:
    """A decoded reference image handed to a provider."""

    data: bytes
    mime_type: str


@dataclass(frozen=True)
class GeneratedImage:
    """Raw image bytes returned by a provider, with the MIME type it reported."""

    data: bytes
    mime_type: str


class ImageProvider(Protocol):
    """Connector to an external image generation API."""

    @property
    def label(self) -> str:
        """Provider and model identifier, used for logging and error messages."""
        ...

    async def generate(
        self, prompt: str, sources: list[ImagePart], aspect_ratio: str
    ) -> GeneratedImage: ...
