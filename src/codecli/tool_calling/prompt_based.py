"""Prompt-based tool calling for backends without native function calling.

Injects tool descriptions into the system prompt and parses XML-delimited
tool calls from the LLM's text output.
"""

from __future__ import annotations

import json
import uuid
from typing import Any


def build_tool_prompt(tools: list[dict[str, Any]]) -> str:
    """Build a system prompt section describing available tools."""
    lines = [
        "You have access to the following tools. To use a tool, output a tool call "
        "in the following XML format:\n",
        "<tool_call>",
        '{"name": "tool_name", "arguments": {"arg1": "value1"}}',
        "</tool_call>\n",
        "You can make multiple tool calls. Wait for tool results before continuing.\n",
        "Available tools:\n",
    ]

    for tool in tools:
        lines.append(f"## {tool['name']}")
        lines.append(f"Description: {tool.get('description', '')}")
        params = tool.get("parameters", {})
        props = params.get("properties", {})
        required = params.get("required", [])
        if props:
            lines.append("Parameters:")
            for pname, pschema in props.items():
                req = " (required)" if pname in required else ""
                desc = pschema.get("description", "")
                ptype = pschema.get("type", "any")
                lines.append(f"  - {pname} ({ptype}{req}): {desc}")
        lines.append("")

    return "\n".join(lines)


def parse_tool_calls(text: str) -> list[dict[str, Any]]:
    """Parse <tool_call>...</tool_call> blocks from LLM text output.

    Returns a list of dicts with 'id', 'name', and 'arguments'.
    """
    calls = []
    remaining = text
    tag_open = "<tool_call>"
    tag_close = "</tool_call>"

    while tag_open in remaining:
        start = remaining.index(tag_open) + len(tag_open)
        end_pos = remaining.find(tag_close, start)
        if end_pos == -1:
            break

        raw = remaining[start:end_pos].strip()
        remaining = remaining[end_pos + len(tag_close):]

        try:
            parsed = json.loads(raw)
            calls.append({
                "id": str(uuid.uuid4())[:8],
                "name": parsed.get("name", ""),
                "arguments": parsed.get("arguments", {}),
            })
        except json.JSONDecodeError:
            continue

    return calls


def has_tool_calls(text: str) -> bool:
    """Check if text contains tool call markers."""
    return "<tool_call>" in text and "</tool_call>" in text


def strip_tool_calls(text: str) -> str:
    """Remove tool call XML blocks from text, returning only the prose."""
    result = text
    while "<tool_call>" in result and "</tool_call>" in result:
        start = result.index("<tool_call>")
        end = result.index("</tool_call>") + len("</tool_call>")
        result = result[:start] + result[end:]
    return result.strip()
