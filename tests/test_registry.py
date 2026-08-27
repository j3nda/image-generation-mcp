"""Provider selection."""

from pathlib import Path

import pytest

from image_generation_mcp.config import Config
from image_generation_mcp.gemini_provider import GeminiProvider
from image_generation_mcp.openai_provider import OpenAIProvider
from image_generation_mcp.registry import select_provider


def make_config(
    gemini_api_key: str | None, openai_api_key: str | None, provider: str | None
) -> Config:
    return Config(
        gemini_api_key=gemini_api_key,
        openai_api_key=openai_api_key,
        provider=provider,
        gemini_model="gemini-model",
        openai_model="openai-model",
        out_dir=Path("/tmp/out"),
        transport="stdio",
        port=8000,
    )


def test_gemini_wins_when_both_keys_present() -> None:
    assert isinstance(select_provider(make_config("g", "o", None)), GeminiProvider)


def test_falls_back_to_openai() -> None:
    assert isinstance(select_provider(make_config(None, "o", None)), OpenAIProvider)


def test_explicit_provider_is_honoured() -> None:
    provider = select_provider(make_config("g", "o", "openai"))
    assert isinstance(provider, OpenAIProvider)
    assert provider.label == "openai/openai-model"


def test_explicit_provider_without_key_raises() -> None:
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not set"):
        select_provider(make_config("g", None, "openai"))
