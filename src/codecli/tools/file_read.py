"""File read tool."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from codecli.tools.base import Tool, ToolResult


class FileReadTool(Tool):
    name = "file_read"
    description = (
        "Read the contents of a file. Returns the file content with line numbers. "
        "Use offset and limit to read specific portions of large files."
    )
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute or relative path to the file to read.",
            },
            "offset": {
                "type": "integer",
                "description": "Line number to start reading from (1-based). Default: 1",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of lines to read. Default: 2000",
            },
        },
        "required": ["file_path"],
    }

    async def execute(self, file_path: str, offset: int = 1, limit: int = 2000, **_: Any) -> ToolResult:
        path = Path(file_path).expanduser().resolve()

        if not path.exists():
            return ToolResult(output=f"File not found: {path}", is_error=True)
        if not path.is_file():
            return ToolResult(output=f"Not a file: {path}", is_error=True)

        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except PermissionError:
            return ToolResult(output=f"Permission denied: {path}", is_error=True)

        lines = text.splitlines()
        total = len(lines)

        start = max(0, offset - 1)
        end = min(total, start + limit)
        selected = lines[start:end]

        numbered = []
        for i, line in enumerate(selected, start=start + 1):
            numbered.append(f"{i:>6}\t{line}")

        header = f"File: {path} ({total} lines total)"
        if start > 0 or end < total:
            header += f" [showing lines {start + 1}-{end}]"

        return ToolResult(output=header + "\n" + "\n".join(numbered))
