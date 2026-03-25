"""Anthropic Messages API backend."""

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


class AnthropicBackend(LLMBackend):
    name = "anthropic"
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
        return {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

    def _convert_messages(
        self, messages: list[dict[str, Any]]
    ) -> tuple[str, list[dict[str, Any]]]:
        """Separate system prompt and convert messages to Anthropic format."""
        system = ""
        converted = []

        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            elif msg["role"] == "tool":
                converted.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.get("tool_call_id", ""),
                            "content": msg["content"],
                        }
                    ],
                })
            elif msg["role"] == "assistant" and msg.get("tool_calls"):
                content: list[dict[str, Any]] = []
                if msg.get("content"):
                    content.append({"type": "text", "text": msg["content"]})
                for tc in msg["tool_calls"]:
                    func = tc["function"]
                    args = func.get("arguments", "{}")
                    if isinstance(args, str):
                        args = json.loads(args)
                    content.append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": func["name"],
                        "input": args,
                    })
                converted.append({"role": "assistant", "content": content})
            else:
                converted.append({"role": msg["role"], "content": msg["content"]})

        return system, converted

    def _convert_tools(self, tools: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
        if not tools:
            return None
        return [
            {
                "name": t["name"],
                "description": t.get("description", ""),
                "input_schema": t.get("parameters", {}),
            }
            for t in tools
        ]

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        system, converted_messages = self._convert_messages(messages)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": converted_messages,
            "max_tokens": self.max_tokens,
            "stream": True,
        }
        if system:
            payload["system"] = system
        if self.temperature > 0:
            payload["temperature"] = self.temperature

        converted_tools = self._convert_tools(tools)
        if converted_tools:
            payload["tools"] = converted_tools

        current_tool_id = ""

        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/v1/messages",
                json=payload,
                headers=self._build_headers(),
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    raw = line[6:]
                    if raw == "[DONE]":
                        yield Done(stop_reason="stop")
                        return

                    try:
                        event = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    event_type = event.get("type", "")

                    if event_type == "content_block_start":
                        block = event.get("content_block", {})
                        if block.get("type") == "tool_use":
                            current_tool_id = block.get("id", "")
                            yield ToolCallStart(
                                id=current_tool_id,
                                name=block.get("name", ""),
                            )
                        elif block.get("type") == "text":
                            text = block.get("text", "")
                            if text:
                                yield TextDelta(text=text)

                    elif event_type == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("type") == "text_delta":
                            yield TextDelta(text=delta.get("text", ""))
                        elif delta.get("type") == "input_json_delta":
                            yield ToolCallArgDelta(
                                id=current_tool_id,
                                delta=delta.get("partial_json", ""),
                            )

                    elif event_type == "content_block_stop":
                        if current_tool_id:
                            yield ToolCallEnd(id=current_tool_id)
                            current_tool_id = ""

                    elif event_type == "message_delta":
                        stop = event.get("delta", {}).get("stop_reason", "")
                        if stop:
                            yield Done(stop_reason=stop)
                            return

                    elif event_type == "message_stop":
                        yield Done(stop_reason="end_turn")
                        return
