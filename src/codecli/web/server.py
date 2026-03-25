"""Web server with WebSocket for GUI chat interface."""

from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any

from aiohttp import web

from codecli.config import Config
from codecli.conversation import Conversation
from codecli.llm import (
    Done,
    TextDelta,
    ToolCallArgDelta,
    ToolCallEnd,
    ToolCallStart,
    create_backend,
)
from codecli.llm.base import LLMBackend
from codecli.tool_calling.prompt_based import (
    build_tool_prompt,
    has_tool_calls,
    parse_tool_calls,
    strip_tool_calls,
)
from codecli.tools import ToolRegistry, get_default_registry

STATIC_DIR = Path(__file__).parent / "static"


class WebOrchestrator:
    """Orchestrator that sends events over WebSocket instead of terminal."""

    def __init__(
        self,
        config: Config,
        backend: LLMBackend,
        tools: ToolRegistry,
    ) -> None:
        self.config = config
        self.backend = backend
        self.tools = tools
        self.conversation = Conversation(system_prompt=config.system_prompt)
        self._use_native_tools = self._should_use_native_tools()

    def _should_use_native_tools(self) -> bool:
        if self.config.tool_calling_mode == "native":
            return True
        if self.config.tool_calling_mode == "prompt":
            return False
        return self.backend.supports_native_tools

    async def process_message(self, user_input: str, ws: web.WebSocketResponse) -> None:
        """Process user message, streaming events to WebSocket."""
        self.conversation.add_user(user_input)
        self.conversation.truncate_if_needed()

        max_iterations = 20

        for _ in range(max_iterations):
            messages = self.conversation.get_messages_for_api()

            if not self._use_native_tools:
                tool_prompt = build_tool_prompt(self.tools.get_schemas())
                if messages and messages[0]["role"] == "system":
                    messages[0]["content"] += "\n\n" + tool_prompt
                else:
                    messages.insert(0, {"role": "system", "content": tool_prompt})

            tool_schemas = self.tools.get_schemas() if self._use_native_tools else None

            text_content, tool_calls = await self._stream_response(messages, tool_schemas, ws)

            if not self._use_native_tools and has_tool_calls(text_content):
                tool_calls = parse_tool_calls(text_content)
                display_text = strip_tool_calls(text_content)
                if display_text:
                    text_content = display_text

            if not tool_calls:
                self.conversation.add_assistant(text_content)
                await ws.send_json({"type": "done"})
                break

            api_tool_calls = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": (
                            json.dumps(tc["arguments"])
                            if isinstance(tc["arguments"], dict)
                            else tc["arguments"]
                        ),
                    },
                }
                for tc in tool_calls
            ]
            self.conversation.add_assistant(text_content, tool_calls=api_tool_calls)

            for tc in tool_calls:
                args = tc["arguments"]
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}

                await ws.send_json({
                    "type": "tool_call",
                    "name": tc["name"],
                    "arguments": args,
                })

                result = await self.tools.execute(tc["name"], args)

                await ws.send_json({
                    "type": "tool_result",
                    "name": tc["name"],
                    "output": result.output[:5000],
                    "is_error": result.is_error,
                })

                self.conversation.add_tool_result(
                    tool_call_id=tc["id"],
                    name=tc["name"],
                    content=result.output,
                )
        else:
            await ws.send_json({"type": "error", "message": "Max iterations reached"})

    async def _stream_response(
        self,
        messages: list[dict[str, Any]],
        tool_schemas: list[dict[str, Any]] | None,
        ws: web.WebSocketResponse,
    ) -> tuple[str, list[dict[str, Any]]]:
        tool_calls: dict[str, dict[str, Any]] = {}
        current_tool_id = ""
        text_buffer = ""

        try:
            async for chunk in self.backend.stream_chat(messages, tool_schemas):
                if isinstance(chunk, TextDelta):
                    text_buffer += chunk.text
                    await ws.send_json({"type": "text_delta", "text": chunk.text})

                elif isinstance(chunk, ToolCallStart):
                    current_tool_id = chunk.id
                    tool_calls[chunk.id] = {
                        "id": chunk.id,
                        "name": chunk.name,
                        "arguments": "",
                    }

                elif isinstance(chunk, ToolCallArgDelta):
                    tc_id = chunk.id or current_tool_id
                    if tc_id in tool_calls:
                        tool_calls[tc_id]["arguments"] += chunk.delta

                elif isinstance(chunk, ToolCallEnd):
                    tc_id = chunk.id or current_tool_id
                    if tc_id in tool_calls:
                        raw_args = tool_calls[tc_id]["arguments"]
                        try:
                            tool_calls[tc_id]["arguments"] = json.loads(raw_args)
                        except json.JSONDecodeError:
                            tool_calls[tc_id]["arguments"] = {"raw": raw_args}

                elif isinstance(chunk, Done):
                    break

        except Exception as e:
            await ws.send_json({"type": "error", "message": f"{type(e).__name__}: {e}"})
            return "", []

        for tc_id, tc in tool_calls.items():
            if isinstance(tc["arguments"], str):
                try:
                    tc["arguments"] = json.loads(tc["arguments"])
                except json.JSONDecodeError:
                    tc["arguments"] = {"raw": tc["arguments"]}

        return text_buffer, list(tool_calls.values())


def create_app(config: Config) -> web.Application:
    """Create the aiohttp web application."""
    backend = create_backend(config)
    tools = get_default_registry()
    orchestrator = WebOrchestrator(config, backend, tools)

    app = web.Application()

    async def handle_index(request: web.Request) -> web.FileResponse:
        return web.FileResponse(STATIC_DIR / "index.html")

    async def handle_websocket(request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        # Send initial config
        await ws.send_json({
            "type": "config",
            "backend": config.backend,
            "model": config.model,
        })

        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except json.JSONDecodeError:
                    continue

                if data.get("type") == "message":
                    user_text = data.get("text", "").strip()
                    if not user_text:
                        continue

                    if user_text == "/clear":
                        orchestrator.conversation.clear()
                        await ws.send_json({"type": "cleared"})
                        continue

                    if user_text == "/config":
                        await ws.send_json({
                            "type": "config",
                            "backend": config.backend,
                            "model": config.model,
                        })
                        continue

                    await orchestrator.process_message(user_text, ws)

            elif msg.type == web.WSMsgType.ERROR:
                break

        return ws

    app.router.add_get("/", handle_index)
    app.router.add_get("/ws", handle_websocket)
    app.router.add_static("/static/", STATIC_DIR, name="static")

    return app


def run_web_server(config: Config, host: str = "0.0.0.0", port: int = 8080) -> None:
    """Start the web server."""
    app = create_app(config)
    print(f"\n  Local Code Agent - Web UI")
    print(f"  Backend: {config.backend} | Model: {config.model}")
    print(f"  Open http://localhost:{port} in your browser\n")
    web.run_app(app, host=host, port=port, print=None)
