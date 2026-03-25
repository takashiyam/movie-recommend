"""Smoke tests to verify all components work together."""

import asyncio
import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_config():
    """Test configuration loading."""
    from codecli.config import Config

    config = Config(backend="mock")
    assert config.backend == "mock"
    assert config.model == "mock"
    assert config.temperature == 0.0
    assert "Working directory" in config.system_prompt
    print("  [OK] Config loading")


def test_conversation():
    """Test conversation management."""
    from codecli.conversation import Conversation

    conv = Conversation(system_prompt="You are a test assistant.")
    conv.add_user("Hello")
    conv.add_assistant("Hi there!")
    conv.add_user("Read a file")
    conv.add_assistant("", tool_calls=[{
        "id": "tc1",
        "type": "function",
        "function": {"name": "file_read", "arguments": '{"file_path": "test.py"}'},
    }])
    conv.add_tool_result("tc1", "file_read", "file contents here")

    msgs = conv.get_messages_for_api()
    assert msgs[0]["role"] == "system"
    assert len(msgs) == 6  # system + 5 messages
    print("  [OK] Conversation management")


def test_tool_registry():
    """Test tool registry and schemas."""
    from codecli.tools import get_default_registry

    registry = get_default_registry()
    schemas = registry.get_schemas()

    assert len(schemas) == 6
    names = [s["name"] for s in schemas]
    assert "file_read" in names
    assert "file_write" in names
    assert "file_edit" in names
    assert "bash" in names
    assert "grep_search" in names
    assert "glob_search" in names
    print(f"  [OK] Tool registry ({len(schemas)} tools registered)")


def test_tool_execution():
    """Test actual tool execution."""
    from codecli.tools import get_default_registry

    registry = get_default_registry()

    # Test file_read on this test file
    result = asyncio.run(registry.execute("file_read", {
        "file_path": os.path.abspath(__file__),
        "limit": 5,
    }))
    assert not result.is_error
    assert "test_smoke.py" in result.output or "Smoke tests" in result.output
    print("  [OK] file_read execution")

    # Test bash
    result = asyncio.run(registry.execute("bash", {"command": "echo hello_world"}))
    assert not result.is_error
    assert "hello_world" in result.output
    print("  [OK] bash execution")

    # Test glob_search
    result = asyncio.run(registry.execute("glob_search", {
        "pattern": "*.py",
        "path": os.path.dirname(os.path.abspath(__file__)),
    }))
    assert not result.is_error
    assert "test_smoke" in result.output
    print("  [OK] glob_search execution")

    # Test grep_search
    result = asyncio.run(registry.execute("grep_search", {
        "pattern": "def test_",
        "path": os.path.abspath(__file__),
    }))
    assert not result.is_error
    assert "test_config" in result.output or "test_" in result.output
    print("  [OK] grep_search execution")

    # Test file_write and file_edit
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        tmppath = f.name

    result = asyncio.run(registry.execute("file_write", {
        "file_path": tmppath,
        "content": "hello world\nfoo bar\n",
    }))
    assert not result.is_error
    print("  [OK] file_write execution")

    result = asyncio.run(registry.execute("file_edit", {
        "file_path": tmppath,
        "old_string": "foo bar",
        "new_string": "baz qux",
    }))
    assert not result.is_error
    assert "Replaced 1" in result.output
    print("  [OK] file_edit execution")

    # Verify edit
    result = asyncio.run(registry.execute("file_read", {"file_path": tmppath}))
    assert "baz qux" in result.output
    os.unlink(tmppath)
    print("  [OK] file_edit verification")

    # Test unknown tool
    result = asyncio.run(registry.execute("nonexistent", {}))
    assert result.is_error
    print("  [OK] Unknown tool handling")


def test_mock_backend():
    """Test mock backend streaming."""
    from codecli.llm.mock import MockBackend
    from codecli.llm.base import TextDelta, ToolCallStart, Done

    backend = MockBackend()

    # Test greeting
    async def run_greeting():
        chunks = []
        async for chunk in backend.stream_chat(
            [{"role": "user", "content": "こんにちは"}],
            tools=[{"name": "bash", "description": "run bash", "parameters": {}}],
        ):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(run_greeting())
    text = "".join(c.text for c in chunks if isinstance(c, TextDelta))
    assert "こんにちは" in text
    assert any(isinstance(c, Done) for c in chunks)
    print("  [OK] Mock backend greeting")

    # Test tool call
    async def run_tool():
        chunks = []
        async for chunk in backend.stream_chat(
            [{"role": "user", "content": "プロジェクトの構造を見せて"}],
            tools=[
                {"name": "bash", "description": "run bash", "parameters": {}},
                {"name": "file_read", "description": "read file", "parameters": {}},
            ],
        ):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(run_tool())
    has_tool_call = any(isinstance(c, ToolCallStart) for c in chunks)
    assert has_tool_call, "Mock should trigger a tool call for structure request"
    print("  [OK] Mock backend tool calling")


def test_prompt_based_tool_calling():
    """Test prompt-based tool call parsing."""
    from codecli.tool_calling.prompt_based import (
        build_tool_prompt,
        parse_tool_calls,
        has_tool_calls,
        strip_tool_calls,
    )

    tools = [
        {
            "name": "file_read",
            "description": "Read a file",
            "parameters": {
                "type": "object",
                "properties": {"file_path": {"type": "string"}},
                "required": ["file_path"],
            },
        }
    ]

    # Test prompt building
    prompt = build_tool_prompt(tools)
    assert "file_read" in prompt
    assert "tool_call" in prompt
    print("  [OK] Tool prompt building")

    # Test parsing
    text = 'Let me read that file.\n<tool_call>\n{"name": "file_read", "arguments": {"file_path": "/tmp/test.py"}}\n</tool_call>\n'
    assert has_tool_calls(text)
    calls = parse_tool_calls(text)
    assert len(calls) == 1
    assert calls[0]["name"] == "file_read"
    assert calls[0]["arguments"]["file_path"] == "/tmp/test.py"
    print("  [OK] Tool call parsing")

    # Test stripping
    stripped = strip_tool_calls(text)
    assert "<tool_call>" not in stripped
    assert "read that file" in stripped
    print("  [OK] Tool call stripping")


def test_backend_registry():
    """Test backend creation from config."""
    from codecli.config import Config
    from codecli.llm.registry import create_backend
    from codecli.llm.mock import MockBackend
    from codecli.llm.ollama import OllamaBackend
    from codecli.llm.openai_compat import OpenAICompatBackend
    from codecli.llm.anthropic import AnthropicBackend

    # Mock
    config = Config(backend="mock")
    backend = create_backend(config)
    assert isinstance(backend, MockBackend)

    # Ollama
    config = Config(backend="ollama")
    backend = create_backend(config)
    assert isinstance(backend, OllamaBackend)

    # OpenAI
    config = Config(backend="openai")
    backend = create_backend(config)
    assert isinstance(backend, OpenAICompatBackend)

    # vLLM
    config = Config(backend="vllm", base_url="http://localhost:8000/v1")
    backend = create_backend(config)
    assert isinstance(backend, OpenAICompatBackend)

    # Anthropic
    config = Config(backend="anthropic")
    backend = create_backend(config)
    assert isinstance(backend, AnthropicBackend)

    print("  [OK] Backend registry")


def test_orchestrator_with_mock():
    """Test full orchestrator loop with mock backend."""
    from codecli.config import Config
    from codecli.llm.registry import create_backend
    from codecli.tools import get_default_registry
    from codecli.ui.terminal import TerminalUI
    from codecli.cli import Orchestrator

    config = Config(backend="mock")
    backend = create_backend(config)
    tools = get_default_registry()
    ui = TerminalUI()

    orchestrator = Orchestrator(config, backend, tools, ui)

    # Test a greeting
    asyncio.run(orchestrator.process_message("こんにちは"))
    assert len(orchestrator.conversation.messages) >= 2
    print("  [OK] Orchestrator greeting flow")

    # Clear and test tool calling flow
    orchestrator.conversation.clear()
    asyncio.run(orchestrator.process_message("プロジェクトの構造を見せて"))
    # Should have: user msg, assistant with tool call, tool result, assistant response
    assert len(orchestrator.conversation.messages) >= 3
    print("  [OK] Orchestrator tool-calling flow")


def main():
    print("\n=== Local Code Agent - Smoke Tests ===\n")

    tests = [
        ("Configuration", test_config),
        ("Conversation", test_conversation),
        ("Tool Registry", test_tool_registry),
        ("Tool Execution", test_tool_execution),
        ("Mock Backend", test_mock_backend),
        ("Prompt-based Tool Calling", test_prompt_based_tool_calling),
        ("Backend Registry", test_backend_registry),
        ("Orchestrator (full loop)", test_orchestrator_with_mock),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        print(f"[TEST] {name}")
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        print()

    print(f"{'=' * 40}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")

    if failed:
        print("\nSome tests failed!")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
