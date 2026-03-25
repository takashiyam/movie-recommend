"""Grep search tool using ripgrep or fallback to grep."""

from __future__ import annotations

import asyncio
import shutil
from typing import Any

from codecli.tools.base import Tool, ToolResult


class GrepSearchTool(Tool):
    name = "grep_search"
    description = (
        "Search file contents using regex patterns. Uses ripgrep (rg) if available, "
        "falls back to grep. Returns matching lines with file paths and line numbers."
    )
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Regex pattern to search for.",
            },
            "path": {
                "type": "string",
                "description": "Directory or file to search in. Default: current directory.",
            },
            "glob": {
                "type": "string",
                "description": "File glob pattern to filter (e.g. '*.py', '*.ts').",
            },
            "case_insensitive": {
                "type": "boolean",
                "description": "Case insensitive search. Default: false",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of matching lines. Default: 100",
            },
        },
        "required": ["pattern"],
    }

    async def execute(
        self,
        pattern: str,
        path: str = ".",
        glob: str = "",
        case_insensitive: bool = False,
        max_results: int = 100,
        **_: Any,
    ) -> ToolResult:
        has_rg = shutil.which("rg") is not None

        if has_rg:
            cmd = ["rg", "--no-heading", "-n", f"--max-count={max_results}"]
            if case_insensitive:
                cmd.append("-i")
            if glob:
                cmd.extend(["--glob", glob])
            cmd.extend([pattern, path])
        else:
            cmd = ["grep", "-rn"]
            if case_insensitive:
                cmd.append("-i")
            if glob:
                cmd.extend(["--include", glob])
            cmd.extend([pattern, path])

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        except asyncio.TimeoutError:
            return ToolResult(output="Search timed out after 30s", is_error=True)
        except FileNotFoundError:
            return ToolResult(output="Neither rg nor grep found on system", is_error=True)

        output = stdout.decode("utf-8", errors="replace").strip()

        if proc.returncode == 1 and not output:
            return ToolResult(output="No matches found.")

        if stderr and proc.returncode not in (0, 1):
            return ToolResult(
                output=stderr.decode("utf-8", errors="replace").strip(),
                is_error=True,
            )

        # Truncate if too long
        lines = output.split("\n")
        if len(lines) > max_results:
            output = "\n".join(lines[:max_results]) + f"\n\n... ({len(lines)} total matches)"

        return ToolResult(output=output if output else "No matches found.")
