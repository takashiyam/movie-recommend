"""Bash command execution tool."""

from __future__ import annotations

import asyncio
from typing import Any

from codecli.tools.base import Tool, ToolResult


class BashTool(Tool):
    name = "bash"
    description = (
        "Execute a bash command and return its output (stdout + stderr). "
        "Commands run in the current working directory. "
        "Use this for git, build tools, tests, and other shell operations."
    )
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command to execute.",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds. Default: 120",
            },
        },
        "required": ["command"],
    }

    async def execute(self, command: str, timeout: int = 120, **_: Any) -> ToolResult:
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()  # type: ignore[union-attr]
            return ToolResult(
                output=f"Command timed out after {timeout}s: {command}",
                is_error=True,
            )
        except Exception as e:
            return ToolResult(output=f"Failed to execute: {e}", is_error=True)

        output_parts = []
        if stdout:
            output_parts.append(stdout.decode("utf-8", errors="replace"))
        if stderr:
            output_parts.append(stderr.decode("utf-8", errors="replace"))

        output = "\n".join(output_parts).strip()

        # Truncate very long output
        max_chars = 50_000
        if len(output) > max_chars:
            output = output[:max_chars] + f"\n\n... (truncated, {len(output)} total chars)"

        if proc.returncode != 0:
            return ToolResult(
                output=f"Exit code: {proc.returncode}\n{output}",
                is_error=True,
            )

        return ToolResult(output=output if output else "(no output)")
