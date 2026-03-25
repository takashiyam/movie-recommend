"""Configuration management with layered precedence."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration.

    Precedence: CLI flags > env vars > .env file > defaults
    """

    backend: str = "ollama"
    model: str = ""
    base_url: str = ""
    api_key: str = ""
    temperature: float = 0.0
    max_tokens: int = 4096
    system_prompt: str = ""
    tool_calling_mode: str = "auto"  # "auto" | "native" | "prompt"

    # Default models per backend
    _default_models: dict[str, str] = field(
        default_factory=lambda: {
            "mock": "mock",
            "ollama": "qwen2.5-coder:14b",
            "openai": "gpt-4o",
            "anthropic": "claude-sonnet-4-20250514",
        },
        repr=False,
    )

    # Default base URLs per backend
    _default_urls: dict[str, str] = field(
        default_factory=lambda: {
            "mock": "",
            "ollama": "http://localhost:11434",
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com",
        },
        repr=False,
    )

    def __post_init__(self) -> None:
        if not self.model:
            self.model = self._default_models.get(self.backend, "")
        if not self.base_url:
            self.base_url = self._default_urls.get(self.backend, "")
        if not self.system_prompt:
            self.system_prompt = self._build_default_system_prompt()

    def _build_default_system_prompt(self) -> str:
        cwd = os.getcwd()
        return (
            "You are an expert AI coding assistant running in the user's terminal. "
            "You help with software engineering tasks: writing code, debugging, "
            "explaining code, and more.\n\n"
            "You have access to tools for reading/writing files, running bash commands, "
            "and searching code. Use them proactively to help the user.\n\n"
            "Be concise and direct. Lead with answers, not reasoning.\n\n"
            f"Working directory: {cwd}\n"
            f"Platform: {os.uname().sysname} {os.uname().machine}\n"
        )

    @classmethod
    def load(cls, **overrides: str) -> Config:
        """Load config from .env, environment variables, and overrides."""
        # Load .env from current dir, then home dir
        load_dotenv(Path.cwd() / ".env")
        load_dotenv(Path.home() / ".config" / "codecli" / ".env")

        env_map = {
            "backend": "CODECLI_BACKEND",
            "model": "CODECLI_MODEL",
            "base_url": "CODECLI_BASE_URL",
            "api_key": "CODECLI_API_KEY",
            "temperature": "CODECLI_TEMPERATURE",
            "max_tokens": "CODECLI_MAX_TOKENS",
            "tool_calling_mode": "CODECLI_TOOL_CALLING_MODE",
        }

        kwargs: dict[str, str | float | int] = {}
        for field_name, env_var in env_map.items():
            value = overrides.get(field_name) or os.environ.get(env_var)
            if value:
                if field_name == "temperature":
                    kwargs[field_name] = float(value)
                elif field_name == "max_tokens":
                    kwargs[field_name] = int(value)
                else:
                    kwargs[field_name] = value

        return cls(**kwargs)  # type: ignore[arg-type]
