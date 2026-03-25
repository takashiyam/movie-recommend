"""OpenAI-compatible backend (OpenAI, vLLM, llama.cpp server, LiteLLM, etc.)."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

import httpx

from codecli.llm.base import (
    Done,
    LLMBackend,
    StreamChunk,
    TextDelta,
    ToolCallArgDelta,
    ToolCallEnd,
    ToolCallStart,
)


class OpenAICompatBackend(LLMBackend):
    name = "openai"
    supports_native_tools = True

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "",
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _convert_tools(self, tools: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
        if not tools:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("parameters", {}),
                },
            }
            for t in tools
        ]

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        converted_tools = self._convert_tools(tools)
        if converted_tools:
            payload["tools"] = converted_tools

        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._build_headers(),
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or line == "data: [DONE]":
                        if line == "data: [DONE]":
                            yield Done(stop_reason="stop")
                            return
                        continue
                    if line.startswith("data: "):
                        line = line[6:]

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    choices = data.get("choices", [])
                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})
                    finish_reason = choices[0].get("finish_reason")

                    # Text content
                    if delta.get("content"):
                        yield TextDelta(text=delta["content"])

                    # Tool calls
                    for tc in delta.get("tool_calls", []):
                        func = tc.get("function", {})
                        idx = str(tc.get("index", 0))
                        call_id = tc.get("id", "")

                        if call_id:
                            yield ToolCallStart(
                                id=call_id,
                                name=func.get("name", ""),
                            )
                        if func.get("arguments"):
                            yield ToolCallArgDelta(
                                id=call_id or idx,
                                delta=func["arguments"],
                            )

                    if finish_reason:
                        # Emit ToolCallEnd for any active tool calls
                        if finish_reason == "tool_calls":
                            for tc in delta.get("tool_calls", []):
                                cid = tc.get("id", str(tc.get("index", 0)))
                                yield ToolCallEnd(id=cid)
                        yield Done(stop_reason=finish_reason)
                        return
