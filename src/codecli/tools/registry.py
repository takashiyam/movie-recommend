"""Tool registry: collects and manages available tools."""

from __future__ import annotations

from typing import Any

from codecli.tools.base import Tool, ToolResult


class ToolRegistry:
    """Registry of available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def get_schemas(self) -> list[dict[str, Any]]:
        return [tool.to_schema() for tool in self._tools.values()]

    async def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(output=f"Unknown tool: {name}", is_error=True)
        try:
            return await tool.execute(**arguments)
        except Exception as e:
            return ToolResult(output=f"Tool error: {type(e).__name__}: {e}", is_error=True)

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())


def get_default_registry() -> ToolRegistry:
    """Create a registry with all built-in tools."""
    from codecli.tools.file_read import FileReadTool
    from codecli.tools.file_write import FileWriteTool
    from codecli.tools.file_edit import FileEditTool
    from codecli.tools.bash import BashTool
    from codecli.tools.grep_search import GrepSearchTool
    from codecli.tools.glob_search import GlobSearchTool

    registry = ToolRegistry()
    registry.register(FileReadTool())
    registry.register(FileWriteTool())
    registry.register(FileEditTool())
    registry.register(BashTool())
    registry.register(GrepSearchTool())
    registry.register(GlobSearchTool())
    return registry
