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
        # TODO: Retries
        # TODO: Handle timeouts, etc.

        while True:
            response = self.client.messages.create(
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                max_tokens=1024,
                temperature = 0.1, # analytical
                messages=messages,
                model="claude-haiku-4-5",
                )
            
            # Add assistant response to history
            # Why?if you send a tool_result referencing a tool_use_id, that tool_use block must exist in the message history 
            # Otherwise you'll get validation error.
            messages.append({"role": "assistant", "content": response.content})
            
            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if isinstance(block, TextBlock):
                        print(block.text) # Let user know what's going on
                    elif isinstance(block, ToolUseBlock):
                        result = execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                    else:
                        raise ValueError('Unexpected block type during tool use!')
                    
                messages.append({"role": "user", "content": tool_results})
            elif response.stop_reason == "end_turn":
                for block in response.content:
                    if isinstance(block, TextBlock):
                        return block.text
                    raise ValueError(f'Unexpected message type: {block}')
            else:
                # TODO: Handle more stop reasons?
                raise ValueError(f"Unexpected stop reason: {response.stop_reason}")