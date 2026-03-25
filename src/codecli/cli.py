"""Main CLI entry point and orchestrator loop."""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

import click

from codecli.config import Config
from codecli.conversation import Conversation
from codecli.llm import (
    Done,
    StreamChunk,
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
from codecli.ui.prompt import create_prompt_session, get_user_input
from codecli.ui.terminal import TerminalUI


class Orchestrator:
    """Main orchestrator that wires LLM, tools, and UI together."""

    def __init__(
        self,
        config: Config,
        backend: LLMBackend,
        tools: ToolRegistry,
        ui: TerminalUI,
    ) -> None:
        self.config = config
        self.backend = backend
        self.tools = tools
        self.ui = ui
        self.conversation = Conversation(system_prompt=config.system_prompt)
        self._use_native_tools = self._should_use_native_tools()

    def _should_use_native_tools(self) -> bool:
        if self.config.tool_calling_mode == "native":
            return True
        if self.config.tool_calling_mode == "prompt":
            return False
        # auto: use native if backend supports it
        return self.backend.supports_native_tools

    async def process_message(self, user_input: str) -> None:
        """Process a user message through the full tool-calling loop."""
        self.conversation.add_user(user_input)
        self.conversation.truncate_if_needed()

        max_iterations = 20  # Safety limit for tool-calling loops

        for _ in range(max_iterations):
            messages = self.conversation.get_messages_for_api()

            # Inject tool prompt for prompt-based mode
            if not self._use_native_tools:
                tool_prompt = build_tool_prompt(self.tools.get_schemas())
                # Prepend to system message
                if messages and messages[0]["role"] == "system":
                    messages[0]["content"] += "\n\n" + tool_prompt
                else:
                    messages.insert(0, {"role": "system", "content": tool_prompt})

            tool_schemas = self.tools.get_schemas() if self._use_native_tools else None

            # Stream the LLM response
            text_content, tool_calls = await self._stream_response(messages, tool_schemas)

            # For prompt-based mode, parse tool calls from text
            if not self._use_native_tools and has_tool_calls(text_content):
                tool_calls = parse_tool_calls(text_content)
                display_text = strip_tool_calls(text_content)
                if display_text:
                    text_content = display_text

            if not tool_calls:
                # No tool calls - we're done
                self.conversation.add_assistant(text_content)
                break

            # Record assistant message with tool calls
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

            # Execute each tool call
            for tc in tool_calls:
                args = tc["arguments"]
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}

                self.ui.print_tool_call(tc["name"], args)
                result = await self.tools.execute(tc["name"], args)
                self.ui.print_tool_result(tc["name"], result.output, result.is_error)

                self.conversation.add_tool_result(
                    tool_call_id=tc["id"],
                    name=tc["name"],
                    content=result.output,
                )

            # Continue loop - LLM will see tool results and respond
        else:
            self.ui.print_error("Reached maximum tool-calling iterations (20)")

    async def _stream_response(
        self,
        messages: list[dict[str, Any]],
        tool_schemas: list[dict[str, Any]] | None,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Stream LLM response, rendering text and collecting tool calls.

        Returns (text_content, tool_calls).
        """
        display = self.ui.create_streaming_display()
        display.start()

        tool_calls: dict[str, dict[str, Any]] = {}  # id -> {name, arguments}
        current_tool_id = ""

        try:
            async for chunk in self.backend.stream_chat(messages, tool_schemas):
                if isinstance(chunk, TextDelta):
                    display.update(chunk.text)

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
                        # Parse arguments JSON
                        raw_args = tool_calls[tc_id]["arguments"]
                        try:
                            tool_calls[tc_id]["arguments"] = json.loads(raw_args)
                        except json.JSONDecodeError:
                            tool_calls[tc_id]["arguments"] = {"raw": raw_args}

                elif isinstance(chunk, Done):
                    break

        except Exception as e:
            display.finish()
            self.ui.print_error(f"Stream error: {type(e).__name__}: {e}")
            return "", []

        text = display.finish()

        # Handle tool calls that weren't properly closed
        for tc_id, tc in tool_calls.items():
            if isinstance(tc["arguments"], str):
                try:
                    tc["arguments"] = json.loads(tc["arguments"])
                except json.JSONDecodeError:
                    tc["arguments"] = {"raw": tc["arguments"]}

        return text, list(tool_calls.values())

    def handle_command(self, command: str) -> bool:
        """Handle slash commands. Returns True if the REPL should continue."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "/help":
            self.ui.print_help()
        elif cmd == "/clear":
            self.conversation.clear()
            self.ui.print_info("Conversation cleared.")
        elif cmd == "/config":
            self.ui.print_info(
                f"Backend: {self.config.backend}\n"
                f"Model: {self.config.model}\n"
                f"Base URL: {self.config.base_url}\n"
                f"Tool calling: {'native' if self._use_native_tools else 'prompt-based'}\n"
                f"Temperature: {self.config.temperature}\n"
                f"Max tokens: {self.config.max_tokens}"
            )
        elif cmd == "/model" and arg:
            self.config.model = arg
            self.backend = create_backend(self.config)
            self._use_native_tools = self._should_use_native_tools()
            self.ui.print_info(f"Model changed to: {arg}")
        elif cmd == "/backend" and arg:
            self.config.backend = arg
            self.config.model = ""
            self.config.base_url = ""
            self.config.__post_init__()
            self.backend = create_backend(self.config)
            self._use_native_tools = self._should_use_native_tools()
            self.ui.print_info(
                f"Backend changed to: {arg} (model: {self.config.model})"
            )
        elif cmd == "/compact":
            self.conversation.truncate_if_needed()
            self.ui.print_info(
                f"Conversation compacted. {len(self.conversation.messages)} messages remaining."
            )
        elif cmd in ("/exit", "/quit"):
            return False
        else:
            self.ui.print_error(f"Unknown command: {cmd}. Type /help for help.")

        return True


def run_repl(config: Config) -> None:
    """Run the interactive REPL (synchronous, uses asyncio.run for LLM calls)."""
    ui = TerminalUI()
    backend = create_backend(config)
    tools = get_default_registry()
    orchestrator = Orchestrator(config, backend, tools, ui)

    ui.print_welcome(config.backend, config.model)

    session = create_prompt_session()

    while True:
        try:
            user_input = get_user_input(session)

            if user_input is None:
                continue

            if not user_input:
                continue

            # Handle slash commands
            if user_input.startswith("/"):
                if not orchestrator.handle_command(user_input):
                    break
                continue

            # Process through LLM (async call from sync context)
            asyncio.run(orchestrator.process_message(user_input))

        except KeyboardInterrupt:
            ui.console.print("\n[dim]Interrupted. Press Ctrl+C again or type /exit to quit.[/dim]")
            try:
                user_input = get_user_input(session)
                if user_input is None:
                    break
            except KeyboardInterrupt:
                break

    ui.console.print("\n[dim]Goodbye![/dim]")


@click.command()
@click.option("--backend", "-b", default=None, help="LLM backend (ollama/openai/anthropic/mock)")
@click.option("--model", "-m", default=None, help="Model name")
@click.option("--base-url", "-u", default=None, help="API base URL")
@click.option("--api-key", "-k", default=None, help="API key")
@click.option(
    "--tool-mode",
    "-t",
    default=None,
    type=click.Choice(["auto", "native", "prompt"]),
    help="Tool calling mode",
)
@click.option("--temperature", default=None, type=float, help="Sampling temperature")
@click.option("--web", is_flag=True, default=False, help="Launch web GUI instead of terminal")
@click.option("--port", default=8080, type=int, help="Web server port (default: 8080)")
def main(
    backend: str | None,
    model: str | None,
    base_url: str | None,
    api_key: str | None,
    tool_mode: str | None,
    temperature: float | None,
    web: bool,
    port: int,
) -> None:
    """Local Code Agent - AI coding assistant for local/on-prem/private cloud."""
    overrides = {}
    if backend:
        overrides["backend"] = backend
    if model:
        overrides["model"] = model
    if base_url:
        overrides["base_url"] = base_url
    if api_key:
        overrides["api_key"] = api_key
    if tool_mode:
        overrides["tool_calling_mode"] = tool_mode
    if temperature is not None:
        overrides["temperature"] = str(temperature)

    config = Config.load(**overrides)

    if web:
        from codecli.web.server import run_web_server
        run_web_server(config, port=port)
    else:
        run_repl(config)


if __name__ == "__main__":
    main()
