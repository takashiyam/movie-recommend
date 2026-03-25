"""Conversation context management."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    """A single message in the conversation."""

    role: str  # "system" | "user" | "assistant" | "tool"
    content: str | list[dict[str, Any]] = ""
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        if self.name:
            d["name"] = self.name
        return d


@dataclass
class Conversation:
    """Manages the conversation history."""

    system_prompt: str = ""
    messages: list[Message] = field(default_factory=list)
    max_context_chars: int = 100_000  # Rough limit (~25k tokens)

    def add_system(self, content: str) -> None:
        self.system_prompt = content

    def add_user(self, content: str) -> None:
        self.messages.append(Message(role="user", content=content))

    def add_assistant(self, content: str, tool_calls: list[dict[str, Any]] | None = None) -> None:
        self.messages.append(Message(role="assistant", content=content, tool_calls=tool_calls))

    def add_tool_result(self, tool_call_id: str, name: str, content: str) -> None:
        self.messages.append(
            Message(role="tool", content=content, tool_call_id=tool_call_id, name=name)
        )

    def get_messages_for_api(self) -> list[dict[str, Any]]:
        """Return messages formatted for API consumption."""
        result = []
        if self.system_prompt:
            result.append({"role": "system", "content": self.system_prompt})
        for msg in self.messages:
            result.append(msg.to_dict())
        return result

    def truncate_if_needed(self) -> None:
        """Drop oldest non-system messages if context is too large."""
        total = len(self.system_prompt)
        for msg in self.messages:
            total += len(str(msg.content))

        while total > self.max_context_chars and len(self.messages) > 2:
            removed = self.messages.pop(0)
            total -= len(str(removed.content))

    def clear(self) -> None:
        self.messages.clear()
