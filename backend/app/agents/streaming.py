import json

from langchain_core.callbacks.base import BaseCallbackHandler
from langgraph.config import get_stream_writer

from app.core.enums import AgentEventTypeEnum

async def agent_sse_event(type: AgentEventTypeEnum, data: dict):
    """Creates a canonical SSE event string format for the client.
    Returns the format:
    '
        event: <event_type>
        data: <dict>
        <empty line>
    '
    """
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {type}\ndata: {payload}\n\n"

async def tool_stream_writer(message: str):
    """Streams status messages during tool execution."""
    writer = get_stream_writer()
    writer({"message": message})

class TokenCounterCallback(BaseCallbackHandler):
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
    
    def on_llm_end(self, response, **kwargs) -> None:
        # Extract token usage from LLM response
        for generation in response.generations:
            for chat_gen in generation:
                token_usage = chat_gen.message.usage_metadata or {}
                self.input_tokens += token_usage.get('input_tokens', 0)
                self.output_tokens += token_usage.get('output_tokens', 0)
                self.total_tokens += token_usage.get('total_tokens', 0)