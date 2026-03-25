"""Glob file search tool."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from codecli.tools.base import Tool, ToolResult


class GlobSearchTool(Tool):
    name = "glob_search"
    description = (
        "Find files matching a glob pattern. "
        "Returns file paths sorted by modification time (newest first)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Glob pattern (e.g. '**/*.py', 'src/**/*.ts').",
            },
            "path": {
                "type": "string",
                "description": "Base directory to search from. Default: current directory.",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results. Default: 100",
            },
        },
        "required": ["pattern"],
    }

    async def execute(
        self,
        pattern: str,
        path: str = ".",
        max_results: int = 100,
        **_: Any,
    ) -> ToolResult:
        base = Path(path).expanduser().resolve()

        if not base.exists():
            return ToolResult(output=f"Directory not found: {base}", is_error=True)

        try:
            matches = sorted(
                base.glob(pattern),
                key=lambda p: p.stat().st_mtime if p.exists() else 0,
                reverse=True,
            )
        except Exception as e:
            return ToolResult(output=f"Glob error: {e}", is_error=True)

        # Filter to files only
        files = [m for m in matches if m.is_file()]

        if not files:
            return ToolResult(output=f"No files matching '{pattern}' in {base}")

        total = len(files)
        files = files[:max_results]

        lines = [str(f) for f in files]
        output = "\n".join(lines)

        if total > max_results:
            output += f"\n\n... ({total} total matches, showing {max_results})"

        return ToolResult(output=output)
