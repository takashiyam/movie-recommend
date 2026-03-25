"""User input prompt with history support."""

from __future__ import annotations

import sys
from pathlib import Path

# Try prompt_toolkit, fall back to basic input
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.key_binding import KeyBindings

    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False


def create_prompt_session() -> object:
    """Create a prompt session with history and multi-line support."""
    if not HAS_PROMPT_TOOLKIT or not sys.stdin.isatty():
        return None  # Use basic input fallback

    history_path = Path.home() / ".config" / "codecli" / "history"
    history_path.parent.mkdir(parents=True, exist_ok=True)

    bindings = KeyBindings()

    @bindings.add("escape", "enter")
    def _(event):
        """Alt+Enter to insert newline."""
        event.current_buffer.insert_text("\n")

    return PromptSession(
        history=FileHistory(str(history_path)),
        key_bindings=bindings,
        multiline=False,
        enable_history_search=True,
    )


def get_user_input(session: object) -> str | None:
    """Get input from user. Returns None on EOF/Ctrl+D."""
    try:
        if session is not None and HAS_PROMPT_TOOLKIT:
            text = session.prompt("❯ ")  # type: ignore[union-attr]
        else:
            # Basic fallback for non-TTY or missing prompt_toolkit
            try:
                text = input("❯ ")
            except EOFError:
                return None
        return text.strip() if text else None
    except EOFError:
        return None
    except KeyboardInterrupt:
        return None
