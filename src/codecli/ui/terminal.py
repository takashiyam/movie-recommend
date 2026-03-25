"""Rich-based terminal renderer with streaming support."""

from __future__ import annotations

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text


class TerminalUI:
    """Handles all terminal output rendering."""

    def __init__(self) -> None:
        self.console = Console()

    def print_welcome(self, backend: str, model: str) -> None:
        self.console.print()
        self.console.print(
            Panel(
                f"[bold cyan]Local Code Agent[/bold cyan]\n"
                f"Backend: [green]{backend}[/green] | Model: [green]{model}[/green]\n"
                f"Type [bold]/help[/bold] for commands, [bold]Ctrl+C[/bold] to exit",
                border_style="cyan",
            )
        )
        self.console.print()

    def print_help(self) -> None:
        help_text = (
            "[bold]Commands:[/bold]\n"
            "  /help     - Show this help\n"
            "  /clear    - Clear conversation history\n"
            "  /config   - Show current configuration\n"
            "  /model    - Change model (e.g. /model llama3.1)\n"
            "  /backend  - Change backend (e.g. /backend openai)\n"
            "  /compact  - Summarize and compact conversation\n"
            "  /exit     - Exit the assistant\n"
            "  Ctrl+C    - Cancel current operation or exit"
        )
        self.console.print(Panel(help_text, title="Help", border_style="blue"))

    def create_streaming_display(self) -> StreamingDisplay:
        return StreamingDisplay(self.console)

    def print_tool_call(self, name: str, arguments: dict) -> None:
        args_display = "\n".join(f"  {k}: {v}" for k, v in arguments.items())
        if len(args_display) > 500:
            args_display = args_display[:500] + "\n  ..."
        self.console.print(
            Panel(
                f"[bold]{name}[/bold]\n{args_display}",
                title="[yellow]Tool Call[/yellow]",
                border_style="yellow",
                padding=(0, 1),
            )
        )

    def print_tool_result(self, name: str, result: str, is_error: bool = False) -> None:
        style = "red" if is_error else "green"
        title = f"[{style}]{'Error' if is_error else 'Result'}: {name}[/{style}]"
        # Truncate long results
        display = result if len(result) <= 2000 else result[:2000] + "\n... (truncated)"
        self.console.print(
            Panel(display, title=title, border_style=style, padding=(0, 1))
        )

    def print_error(self, message: str) -> None:
        self.console.print(f"[bold red]Error:[/bold red] {message}")

    def print_info(self, message: str) -> None:
        self.console.print(f"[dim]{message}[/dim]")


class StreamingDisplay:
    """Accumulates streaming text and renders as Markdown."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self.buffer = ""
        self._live: Live | None = None

    def start(self) -> None:
        self._live = Live(
            Text("▍", style="cyan"),
            console=self.console,
            refresh_per_second=10,
            vertical_overflow="visible",
        )
        self._live.start()

    def update(self, text_delta: str) -> None:
        self.buffer += text_delta
        if self._live:
            try:
                rendered = Markdown(self.buffer + " ▍")
            except Exception:
                rendered = Text(self.buffer + " ▍")
            self._live.update(rendered)

    def finish(self) -> str:
        if self._live:
            if self.buffer.strip():
                try:
                    self._live.update(Markdown(self.buffer))
                except Exception:
                    self._live.update(Text(self.buffer))
            else:
                self._live.update(Text(""))
            self._live.stop()
            self._live = None
        return self.buffer
