"""Interactive REPL for BETA."""

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from pathlib import Path

from beta.agent import BetaAgent

HISTORY_FILE = Path.home() / ".beta_history"

WELCOME = """
BETA - Better Exploration of Training Analytics
Type your questions about climbing data. Commands: exit, quit, or Ctrl+C/Ctrl+D to leave.
"""


def run_repl() -> None:
    """Run the interactive REPL loop."""
    print(WELCOME)

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
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        if user_input.lower() == "clear":
            # TODO: make it "visually" clear history, too
            messages.clear()
            print("Cleared message history")
            continue

        # Add user message to history
        messages.append({"role": "user", "content": user_input})

        # TODO: Add history limit and clear

        try:
            response = agent.send_message(messages)
            print(f"\n{response}\n")

        except Exception as e:
            print(f"\nError: {e}\n")
            # Remove the failed user message to keep history clean
            # messages.pop()
            # TODO: Review this
