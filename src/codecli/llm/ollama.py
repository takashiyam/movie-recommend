"""Ollama backend using the /api/chat streaming endpoint."""

from __future__ import annotations

import json
import uuid
from typing import Any, AsyncIterator

import httpx

from codecli.llm.base import (
    Done,
    LLMBackend,
    StreamChunk,
    TextDelta,
    ToolCallEnd,
    ToolCallStart,
    ToolCallArgDelta,
)


class OllamaBackend(LLMBackend):
    name = "ollama"
    supports_native_tools = True

    def __init__(self, base_url: str, model: str, temperature: float = 0.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature

    def _convert_tools(self, tools: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
        """Convert tools to Ollama format."""
        if not tools:
            return None
        ollama_tools = []
        for tool in tools:
            ollama_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {}),
                },
            })
        return ollama_tools

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": self.temperature},
        }

        ollama_tools = self._convert_tools(tools)
        if ollama_tools:
            payload["tools"] = ollama_tools

        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    data = json.loads(line)

                    # Handle tool calls
                    msg = data.get("message", {})
                    if msg.get("tool_calls"):
                        for tc in msg["tool_calls"]:
                            func = tc.get("function", {})
                            call_id = str(uuid.uuid4())[:8]
                            yield ToolCallStart(id=call_id, name=func.get("name", ""))
                            args_str = json.dumps(func.get("arguments", {}))
                            yield ToolCallArgDelta(id=call_id, delta=args_str)
                            yield ToolCallEnd(id=call_id)

                    # Handle text content
                    content = msg.get("content", "")
                    if content:
                        yield TextDelta(text=content)

                    if data.get("done", False):
                        yield Done(stop_reason=data.get("done_reason", "stop"))
                        return
