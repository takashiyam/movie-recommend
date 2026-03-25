"""Backend registry: maps backend names to implementations."""

from __future__ import annotations

from codecli.config import Config
from codecli.llm.base import LLMBackend
from codecli.llm.anthropic import AnthropicBackend
from codecli.llm.mock import MockBackend
from codecli.llm.ollama import OllamaBackend
from codecli.llm.openai_compat import OpenAICompatBackend


def create_backend(config: Config) -> LLMBackend:
    """Create an LLM backend from configuration."""
    if config.backend == "mock":
        return MockBackend()
    elif config.backend == "ollama":
        return OllamaBackend(
            base_url=config.base_url,
            model=config.model,
            temperature=config.temperature,
        )
    elif config.backend in ("openai", "vllm", "llamacpp", "litellm"):
        return OpenAICompatBackend(
            base_url=config.base_url,
            model=config.model,
            api_key=config.api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    elif config.backend == "anthropic":
        return AnthropicBackend(
            base_url=config.base_url,
            model=config.model,
            api_key=config.api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    else:
        raise ValueError(
            f"Unknown backend: {config.backend}. "
            f"Supported: mock, ollama, openai, vllm, llamacpp, litellm, anthropic"
        )
