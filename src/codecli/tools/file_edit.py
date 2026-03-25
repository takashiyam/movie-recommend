"""File edit tool using exact string replacement."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from codecli.tools.base import Tool, ToolResult


class FileEditTool(Tool):
    name = "file_edit"
    description = (
        "Edit a file by replacing an exact string with a new string. "
        "The old_string must appear exactly once in the file (unless replace_all is true)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to edit.",
            },
            "old_string": {
                "type": "string",
                "description": "The exact string to find and replace.",
            },
            "new_string": {
                "type": "string",
                "description": "The string to replace it with.",
            },
            "replace_all": {
                "type": "boolean",
                "description": "Replace all occurrences. Default: false",
            },
        },
        "required": ["file_path", "old_string", "new_string"],
    }

    async def execute(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
        **_: Any,
    ) -> ToolResult:
        path = Path(file_path).expanduser().resolve()

        if not path.exists():
            return ToolResult(output=f"File not found: {path}", is_error=True)

        try:
            content = path.read_text(encoding="utf-8")
        except PermissionError:
            return ToolResult(output=f"Permission denied: {path}", is_error=True)

        count = content.count(old_string)

        if count == 0:
            return ToolResult(
                output=f"old_string not found in {path}. Make sure the string matches exactly.",
                is_error=True,
            )

        if count > 1 and not replace_all:
            return ToolResult(
                output=(
                    f"old_string found {count} times in {path}. "
                    "Provide more context to make it unique, or set replace_all=true."
                ),
                is_error=True,
            )

        if replace_all:
            new_content = content.replace(old_string, new_string)
        else:
            new_content = content.replace(old_string, new_string, 1)

        path.write_text(new_content, encoding="utf-8")

        replaced = count if replace_all else 1
        return ToolResult(output=f"Replaced {replaced} occurrence(s) in {path}")
