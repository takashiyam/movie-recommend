"""Abstract base for LLM backends and streaming chunk types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterator


# --- Stream Chunk Types ---

@dataclass
class TextDelta:
    text: str


@dataclass
class ToolCallStart:
    id: str
    name: str


@dataclass
class ToolCallArgDelta:
    id: str
    delta: str


@dataclass
class ToolCallEnd:
    id: str


@dataclass
class Done:
    stop_reason: str


StreamChunk = TextDelta | ToolCallStart | ToolCallArgDelta | ToolCallEnd | Done


# --- Backend Protocol ---

class LLMBackend(ABC):
    """Abstract base class for LLM backends."""

    name: str
    supports_native_tools: bool

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a chat completion response.

        Args:
            messages: Conversation messages in OpenAI-like format.
            tools: Tool schemas (JSON Schema format). May be ignored if
                   the backend doesn't support native tool calling.

        Yields:
            StreamChunk instances.
        """
        ...
        # Make this an async generator
        if False:
            yield  # pragma: no cover
