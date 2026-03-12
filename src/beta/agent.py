"""Agent loop for BETA."""

from beta.tools import TOOLS, execute_tool


SYSTEM_PROMPT = """
TODO: Fill in system prompt
""".strip()


def run_agent_turn(messages: list[dict]) -> str:
    """Run a single turn of the agent loop.

    Args:
        messages: Conversation history as list of {"role": ..., "content": ...}

    Returns:
        The agent's final text response for this turn.
    """
    # TODO: Implement the agent loop
    raise NotImplementedError("Implement the agent loop here")
