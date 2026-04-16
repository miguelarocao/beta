"""Interactive REPL for BETA."""

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text

from beta.agent import BetaAgent

HISTORY_FILE = Path.home() / ".beta_history"
console = Console()

LOGO = """\
  ██████╗ ███████╗████████╗ █████╗
  ██╔══██╗██╔════╝╚══██╔══╝██╔══██╗
  ██████╔╝█████╗     ██║   ███████║
  ██╔══██╗██╔══╝     ██║   ██╔══██║
  ██████╔╝███████╗   ██║   ██║  ██║
  ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝"""


def _print_logo() -> None:
    # Blue gradient: deep blue at top, cyan at bottom
    colors = ["#1565C0", "#1976D2", "#1E88E5", "#42A5F5", "#64B5F6", "#90CAF9"]
    lines = LOGO.split("\n")
    logo = Text()
    for i, line in enumerate(lines):
        color = colors[min(i, len(colors) - 1)]
        logo.append(line + ("\n" if i < len(lines) - 1 else ""), style=f"bold {color}")
    console.print()
    console.print(logo)
    console.print("\n[dim]Better Exploration of Training Analytics[/dim]")
    console.print("[dim]Commands: exit, quit, clear, Ctrl+C/Ctrl+D[/dim]\n")


def run_repl() -> None:
    """Run the interactive REPL loop."""
    _print_logo()

    agent = BetaAgent()

    # Conversation history persists across turns
    messages: list[dict] = []

    # Command history persists across sessions
    history = FileHistory(str(HISTORY_FILE))

    while True:
        try:
            user_input = prompt("β> ", history=history).strip()
        except (KeyboardInterrupt, EOFError):
            # Ctrl+C or Ctrl+D
            console.print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            console.print("Goodbye!")
            break

        if user_input.lower() == "clear":
            # TODO: make it "visually" clear history, too
            messages.clear()
            console.print("[dim]Cleared message history[/dim]")
            continue

        # Add user message to history
        messages.append({"role": "user", "content": user_input})

        # TODO: Add history limit and clear

        try:
            response = agent.send_message(messages)
            console.print(Markdown(response))

        except Exception as e:
            console.print(f"\n[red]Error:[/red] {e}\n")
            # Remove the failed user message to keep history clean
            # messages.pop()
            # TODO: Review this
