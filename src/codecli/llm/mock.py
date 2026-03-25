"""Mock backend for testing and demo purposes.

Simulates an LLM that can respond to basic requests and use tools,
without requiring any external API or model.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, AsyncIterator

from codecli.llm.base import (
    Done,
    LLMBackend,
    StreamChunk,
    TextDelta,
    ToolCallArgDelta,
    ToolCallEnd,
    ToolCallStart,
)


# Pattern-matched responses with optional tool calls
PATTERNS: list[dict[str, Any]] = [
    # More specific patterns first
    {
        "keywords": ["構造", "ファイル一覧", "構成", "ls", "tree", "structure"],
        "tool": "bash",
        "args": {"command": "find . -type f -not -path './.git/*' | head -50 | sort"},
        "response": "プロジェクトの構造を確認します。",
    },
    {
        "keywords": ["git", "status", "コミット", "差分"],
        "tool": "bash",
        "args": {"command": "git status"},
        "response": "Gitの状態を確認します。",
    },
    {
        "keywords": ["検索", "探", "search", "grep", "find"],
        "tool": "grep_search",
        "response": "コード内を検索します。",
    },
    {
        "keywords": ["テスト", "test", "実行", "run"],
        "tool": "bash",
        "response": "コマンドを実行します。",
    },
    {
        "keywords": ["読", "read", "cat", "開い"],
        "tool": "file_read",
        "response": "ファイルの内容を読み込みます。",
    },
]


class MockBackend(LLMBackend):
    """Mock backend that simulates tool-using LLM responses."""

    name = "mock"
    supports_native_tools = True

    def __init__(self, **_: Any) -> None:
        pass

    def _match_pattern(self, user_msg: str) -> dict[str, Any] | None:
        for pattern in PATTERNS:
            if any(kw in user_msg.lower() for kw in pattern["keywords"]):
                return pattern
        return None

    def _extract_path(self, text: str) -> str:
        """Try to extract a file path from user message."""
        import re
        # Look for quoted strings first
        match = re.search(r'["\']([^"\']+)["\']', text)
        if match:
            return match.group(1)
        # Look for filenames with extensions (e.g. README.md, src/main.py)
        match = re.search(r'[\w./~-]+\.\w+', text)
        if match:
            return match.group(0)
        # Look for paths like /foo/bar or ./foo or src/main
        match = re.search(r'[./~][\w/._-]+', text)
        if match:
            return match.group(0)
        return "."

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        # Find the latest user message
        user_msg = ""
        has_tool_result = False
        for msg in reversed(messages):
            if msg["role"] == "user":
                user_msg = msg["content"] if isinstance(msg["content"], str) else str(msg["content"])
                break
            if msg["role"] == "tool":
                has_tool_result = True

        # If we just got a tool result, generate a summary response
        if has_tool_result:
            for msg in reversed(messages):
                if msg["role"] == "tool":
                    content = msg["content"] if isinstance(msg["content"], str) else str(msg["content"])
                    summary = f"結果を確認しました。\n\n"
                    if len(content) > 200:
                        summary += f"取得した情報（{len(content)}文字）を基に回答します。\n"
                    yield TextDelta(text=summary)
                    yield TextDelta(text=f"以下が結果です:\n\n```\n{content[:1000]}\n```")
                    if len(content) > 1000:
                        yield TextDelta(text=f"\n\n（{len(content) - 1000}文字省略）")
                    yield Done(stop_reason="stop")
                    return

        # Match patterns for tool use
        pattern = self._match_pattern(user_msg)

        if pattern and tools:
            # Emit thinking text
            response_text = pattern["response"]
            yield TextDelta(text=response_text + "\n")

            # Build tool call
            call_id = str(uuid.uuid4())[:8]
            tool_name = pattern["tool"]

            # Build arguments
            args = pattern.get("args", {})
            if not args:
                if tool_name == "file_read":
                    args = {"file_path": self._extract_path(user_msg)}
                elif tool_name == "grep_search":
                    # Extract search term
                    args = {"pattern": user_msg.split()[-1], "path": "."}
                elif tool_name == "bash":
                    # Try to extract command
                    args = {"command": "echo 'specify a command'"}

            yield ToolCallStart(id=call_id, name=tool_name)
            yield ToolCallArgDelta(id=call_id, delta=json.dumps(args, ensure_ascii=False))
            yield ToolCallEnd(id=call_id)
            yield Done(stop_reason="tool_calls")
            return

        # Default: just echo back a helpful response
        if not user_msg:
            yield TextDelta(text="何かお手伝いできることはありますか？")
        elif any(kw in user_msg.lower() for kw in ["hello", "hi", "こんにちは", "はじめ"]):
            yield TextDelta(text="こんにちは！AIコーディングアシスタントです。\n\n")
            yield TextDelta(text="以下のことができます:\n")
            yield TextDelta(text="- ファイルの読み書き・編集\n")
            yield TextDelta(text="- コマンドの実行\n")
            yield TextDelta(text="- コード検索\n\n")
            yield TextDelta(text="何でも聞いてください！")
        elif any(kw in user_msg.lower() for kw in ["help", "ヘルプ", "使い方"]):
            yield TextDelta(text="## 使い方\n\n")
            yield TextDelta(text="自然言語でリクエストしてください。例:\n\n")
            yield TextDelta(text="- 「このプロジェクトの構造を見せて」\n")
            yield TextDelta(text="- 「src/main.pyを読んで」\n")
            yield TextDelta(text="- 「TODOを検索して」\n")
            yield TextDelta(text="- 「テストを実行して」\n")
        else:
            yield TextDelta(text=f"了解しました。「{user_msg[:50]}」について対応します。\n\n")
            yield TextDelta(text="*（これはモックモードです。実際のLLMバックエンドに接続すると、")
            yield TextDelta(text="より高度な応答とツール使用が可能になります。)*\n\n")
            yield TextDelta(text="利用可能なバックエンド:\n")
            yield TextDelta(text="- `codecli -b ollama` (ローカル)\n")
            yield TextDelta(text="- `codecli -b openai` (OpenAI API)\n")
            yield TextDelta(text="- `codecli -b anthropic` (Anthropic API)\n")

        yield Done(stop_reason="stop")
