"""Base class and types for tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    """Result of a tool execution."""

    output: str
    is_error: bool = False


class Tool(ABC):
    """Abstract base for all tools."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with the given arguments."""
        ...

    def to_schema(self) -> dict[str, Any]:
        """Return the tool schema for LLM consumption."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
