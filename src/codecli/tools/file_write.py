"""File write tool."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from codecli.tools.base import Tool, ToolResult


class FileWriteTool(Tool):
    name = "file_write"
    description = (
        "Write content to a file. Creates the file if it doesn't exist. "
        "Creates parent directories as needed. Overwrites existing content."
    )
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to write.",
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file.",
            },
        },
        "required": ["file_path", "content"],
    }

    async def execute(self, file_path: str, content: str, **_: Any) -> ToolResult:
        path = Path(file_path).expanduser().resolve()

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        except PermissionError:
            return ToolResult(output=f"Permission denied: {path}", is_error=True)
        except OSError as e:
            return ToolResult(output=f"Write error: {e}", is_error=True)

        lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
        return ToolResult(output=f"Written {lines} lines to {path}")
