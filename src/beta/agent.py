"""Agent loop for BETA."""

from anthropic.types import MessageParam, TextBlock, ToolUseBlock

from beta.tools import TOOLS, execute_tool
from anthropic import Anthropic
import os

SYSTEM_PROMPT = """
You are a helpful data analyst who helps the user answer questions about climbing data.
These questions may include queries about the data or generating images.
If you are unsure you should clarify with the user.
""".strip()

class BetaAgent:
    def __init__(self):
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def send_message(self, messages: list[MessageParam]) -> str:
        """Run a single turn of the agent loop.

    Args:
        messages: Conversation history as list of {"role": ..., "content": ...}

                User message
            │
            ▼
        ┌─► Claude API call
        │       │
        │       ├─ stop_reason == "tool_use"
        │       │       │
        │       │       ▼
        │       │   Execute tool(s)
        │       │       │
        │       │       ▼
        │       │   Send tool_result back ──────┐
        │       │                               │
        │       └─ stop_reason == "end_turn"    │
        │               │                       │
        │               ▼                       │
        │         Respond to user               │
        │                                       │
        └───────────────────────────────────────┘

        Returns:
            The agent's final text response for this turn.
        """
        # TODO: Add handling of conversation (by maintaining list)
        # TODO: Implement the agent loop
        # TODO: Retries

        response = self.client.messages.create(
            max_tokens=1024,
            temperature = 0.1, # analytical
            messages=messages,
            model="claude-haiku-4-5",
            )
        
        for block in response.content:
            if isinstance(block, TextBlock):
                return block.text
            elif isinstance(block, ToolUseBlock):
                raise ValueError('Tool Use is not yet supported!')
                #return '{block.name}, {block.input}, {block.id}'
            raise ValueError(f'Unknown message type: {block}')
