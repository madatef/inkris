# Agents System Documentation

This directory contains the multi-agent orchestration system built on LangGraph and LangChain. The system implements a hierarchical agent architecture with specialized agents for different tasks.

## 📋 Overview

The agent system is designed around an **orchestrator pattern** where a main agent coordinates specialized sub-agents to handle complex user requests. The architecture supports:

- **Stateful conversations** with persistent checkpointing
- **Context-aware prompts** with user and file information
- **PII detection and masking** for privacy
- **Automatic summarization** at token thresholds (20,000 tokens trigger. Feel free to change!)
- **Structured outputs** via formatters
- **Tool-based interactions** for external integrations

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Orchestrator Agent                     │
│  (Routes requests, manages context, coordinates)        │
└────────────────────┬────────────────────────────────────┘
                     │
       ┌─────────────┼─────────────┐
       ↓             ↓             ↓
   RAG Agent    Excel Agent    Future Agents
       │             │
       ↓             ↓
  Vector Store   DuckDB Query
```

### Key Components

1. **Orchestrator** (`orchestrator.py`): Main agent that handles routing and coordination
2. **Sub-agents** (`subagents/`): Specialized agents for specific domains
3. **Tools** (`tools/`): Function definitions for agent capabilities
4. **Middleware** (`middleware/`): Cross-cutting concerns (PII, summarization)
5. **Persistence** (`persistence/`): State management and checkpointing
6. **Formatters** (`formatters/`): Structured output schemas

## 📁 Directory Structure

```
agents/
├── formatters/              # Output formatting schemas
│   └── rag_formatter.py    # RAG response structure
│
├── middleware/              # Agent middleware components
│   ├── pii.py              # PII detection and masking
│   └── summarization.py    # Automatic conversation summarization
│
├── persistence/             # State management
│   ├── checkpointer.py     # LangGraph checkpointer manager
│   ├── pool.py             # PostgreSQL connection pool
│   └── store.py            # LangGraph store for metadata
│
├── subagents/              # Specialized agents
│   ├── excel_agent.py      # Excel/spreadsheet analysis
│   └── rag_agent.py        # Document retrieval and QA
│
├── tools/                  # Agent tool definitions
│   ├── excel_tools.py      # Excel manipulation tools
│   ├── orchestrator_tools.py # Orchestrator delegation tools
│   └── rag_tools.py        # RAG search and retrieval tools
│
├── llms.py                 # LLM configurations
├── orchestrator.py         # Main orchestrator agent
├── prompts.py              # System prompts for agents
├── runtime_context.py      # Agent runtime context schema
├── streaming.py            # SSE streaming utilities
└── README.md               # This file
```

## 🤖 Agents

### Orchestrator Agent

**Location**: `orchestrator.py`

The orchestrator is the main entry point for all user interactions. It:

- Receives user messages
- Analyzes the request intent
- Routes to appropriate sub-agents
- Aggregates responses
- Maintains conversation context

**Tools Available**:

***Note***: the following tool names are descriptive, not the exact names used in code.

- `call_excel_agent`: Delegate Excel-related queries
- `call_rag_agent`: Delegate document retrieval queries
- `search_web`: Perform web searches (via Jina/Serper)
- `read_webpage`: Extract content from URLs
- `generate_image`: Generate an image from a text prompt using gpt-image-1.5
- `generate_video`: Generate a video from a text prompt using Sora 2

**Middleware Stack**:
1. **Dynamic Context Prompt**: Injects user ID, name, and file list
2. **PII Middleware**: Masks emails and redacts credit cards
3. **Summarization Middleware**: Triggers at 20k tokens, summarizing context and keeping the default message offset (set by LangChain, changeable through the `keep` param)

**Configuration**:
```python
Model: OpenAI GPT (configurable via ORCHESTRATOR_OPENAI_MODEL)
Temperature: 0.2 (balanced creativity/precision)
Checkpointer: PostgreSQL-backed state persistence
Context Schema: AgentContext (user_id, user_name, files)
```

### RAG Agent

**Location**: `subagents/rag_agent.py`

Handles document retrieval and question answering over uploaded files.

**Capabilities**:
- Semantic search across user's document collection
- Multi-document reasoning
- Page-level and chunk-level retrieval
- Source attribution with file ID and page numbers

**Tools Available**:
- `search_chunks`: Vector similarity search
- `get_page_chunks`: Retrieve all chunks from specific page
- `get_point_by_id`: Get a specific vector point (useful for when the retrieved points' text is truncated. Points reference previous and next points)

**Output Format** (via `formatters/rag_formatter.py`):
```python
{
    "chunks": [
        {
            "file_id": "uuid",
            "page": "1",
            "text": "Retrieved text content..."
        }
    ]
}
```

**Configuration**:
```python
Model: OpenAI GPT (configurable via RAG_OPENAI_MODEL)
Temperature: 0.0 (maximum precision for factual retrieval)
Vector Store: Qdrant
Embedding Model: OpenAI text-embedding-3-small
```

### Excel Agent

**Location**: `subagents/excel_agent.py`

Specialized agent for spreadsheet analysis, querying, and manipulation.

**Capabilities**:
- Natural language queries over Excel data
- SQL-based data analysis (via DuckDB)
- Statistical computations
- Data transformations and aggregations

**Tools Available**:
- `query_excel`: Execute SQL queries on Excel data
- `get_excel_schema`: Retrieve table structure
- `list_excel_files`: Get available spreadsheets

**Technical Stack**:
- **DuckDB**: In-process analytics engine
- **PyArrow**: Zero-copy data interchange
- **Apache Parquet**: Convert sheets into columnar data
- **S3FS**: Direct S3 file access

**Configuration**:
```python
Model: OpenAI GPT (same as orchestrator)
Temperature: 0.0 (precise data queries)
Storage: Ephemeral DuckDB instance per query
```

## 🛠️ Tools

### Orchestrator Tools

**File**: `tools/orchestrator_tools.py`

- **`call_excel_agent`**: Delegates Excel queries to Excel agent
- **`call_rag_agent`**: Delegates document queries to RAG agent
- **`search_web`**: Web search via Serper API
- **`read_webpage`**: Content extraction via Jina Reader API
- **`generate_image`**: Generate an image from a text prompt using gpt-image-1.5
- **`generate_video`**: Generate a video from a text prompt using Sora 2

### RAG Tools

**File**: `tools/rag_tools.py`

- **`search_chunks`**: Vector similarity search with filters
  - Parameters: `query` (str), `file_ids` (optional list)
  - Returns: Top-k relevant chunks with metadata
  
- **`get_page_chunks`**: Retrieve all chunks from a page
  - Parameters: `file_id` (UUID), `page_label` (str)
  - Returns: All chunks from specified page
  
- **`list_user_files`**: Get user's uploaded files
  - Returns: List of file metadata (name, ID, type)

### Excel Tools

**File**: `tools/excel_tools.py`

- **`query_excel`**: Execute SQL on Excel data
  - Parameters: `file_id` (UUID), `query` (SQL string)
  - Returns: Query results as formatted table
  
- **`get_excel_schema`**: Get table structure
  - Parameters: `file_id` (UUID)
  - Returns: Column names and types
  
- **`list_excel_files`**: List available Excel files
  - Returns: Excel file metadata

## 🔧 Middleware

### PII Middleware

**File**: `middleware/pii.py`

Automatically detects and handles personally identifiable information:

- **Email Detection**: Masks email addresses (`user@example.com` → `[EMAIL]`)
- **Credit Card Detection**: Redacts card numbers entirely

**Strategy Options**:
- `mask`: Replace with placeholder token
- `redact`: Remove entirely
- `hash`: One-way hash for consistency

**Example**:
```python
Input:  "My email is john@example.com and card is 4532-1234-5678-9010"
Output: "My email is [EMAIL] and card is [REDACTED]"
```

### Summarization Middleware

**File**: `middleware/summarization.py`

Automatically summarizes conversation history when token limits are reached.

**Configuration**:
- **Trigger**: 20,000 tokens
- **Model**: Configurable via `SUMMARIZATION_OPENAI_MODEL`
- **Temperature**: 0.0 (faithful summarization)

**Behavior**:
1. Monitors conversation token count
2. When threshold exceeded, generates concise summary
3. Replaces old messages with summary
4. Preserves recent context window

## 💾 Persistence

### Checkpointer

**File**: `persistence/checkpointer.py`

Manages persistent state for multi-turn conversations using LangGraph's PostgreSQL checkpointer.

**Features**:
- **Automatic state saving**: After each agent turn
- **State retrieval**: Resume conversations from any checkpoint
- **Thread-based isolation**: Each conversation has unique thread ID
- **Async operations**: Non-blocking state persistence

**Database Schema**:
```sql
checkpoints (
    thread_id TEXT,
    checkpoint_ns TEXT,
    checkpoint_id TEXT,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint JSONB,
    metadata JSONB,
    ...
)
```

**Usage**:
```python
checkpointer = get_checkpointer()
await checkpointer.setup()  # Initialize schema

# State is automatically managed by LangGraph
config = {"configurable": {"thread_id": "conversation-123"}}
response = await agent.ainvoke(input, config)
```

### Connection Pool

**File**: `persistence/pool.py`

Manages PostgreSQL connection pool for agent state database.

**Configuration**:
- **Pool Size**: Configured based on expected concurrency
- **Connection Params**: Includes keepalive for long-running writes
- **SSL Support**: Configurable for production deployments

**Special Considerations**:
- Separate from main application database
- Optimized for write-heavy workloads (checkpointing)
- Includes connection keepalive to prevent gateway timeouts

### Store

**File**: `persistence/store.py`

LangGraph store for agent metadata and auxiliary data.

**Use Cases**:
- User preferences
- Agent configurations
- Conversation metadata
- Custom agent memory

## 📝 Prompts

**File**: `prompts.py`

System prompts define agent behavior and personality.

**Structure**:
```python
orchestrator_base = """
You are Inkris, an intelligent assistant that helps users...

Your capabilities:
1. Document analysis via RAG
2. Excel data analysis
3. Web search and research
...

Guidelines:
- Be concise and helpful
- Cite sources when using RAG
- Explain your reasoning
...
"""
```

**Dynamic Prompts**:
The `@dynamic_prompt` decorator allows runtime prompt modification:

```python
@dynamic_prompt
async def context_aware_prompt(request: ModelRequest):
    base = orchestrator_base
    context = request.runtime.context
    return base + f"\nCurrent user: {context.user_name}"
```

## 🌊 Streaming

**File**: `streaming.py`

Server-Sent Events (SSE) utilities for real-time streaming of agent responses.

**Features**:
- Token-level streaming from LLM
- Event-based status updates
- Error handling and reconnection
- Progress indicators

**Event Types**:
```python
{
    "event": "token",
    "data": {"message": "Hello"}
}

{
    "event": "custom",
    "data": {"message": "<custom tool messages>"}
}

{
    "event": "done",
    "data": {"ok": true, "usage": {"...<input/output/total tokens used>"}}
}
```

## 🎯 Runtime Context

**File**: `runtime_context.py`

Defines the context schema available to agents at runtime.

**Schema**:
```python
class AgentContext(BaseModel):
    user_id: UUID
    user_name: str
    files: List[FileInfo]
    # Add custom context fields as needed
```

**Usage**:
Agents can access context via:
```python
context = request.runtime.context
user_files = context.files
```

## 🔌 LLM Configuration

**File**: `llms.py`

Factory functions for LLM instances with role-specific configurations.

**Available LLMs**:

1. **Orchestrator LLM**
   - Model: Configurable (e.g., gpt-4-turbo)
   - Temperature: 0.2 (balanced)
   - Use: General orchestration and routing

2. **RAG LLM**
   - Model: Configurable
   - Temperature: 0.0 (deterministic)
   - Use: Document retrieval and QA

3. **Summarization LLM**
   - Model: Configurable
   - Temperature: 0.0 (faithful)
   - Use: Conversation summarization

## 🚀 Usage Examples

### Creating a New Agent

```python
from langchain.agents import create_agent
from app.agents.llms import orchestrator_llm
from app.agents.persistence.checkpointer import get_checkpointer

my_agent = create_agent(
    model=orchestrator_llm(),
    tools=[tool1, tool2],
    middleware=[],
    checkpointer=get_checkpointer(),
    name='MyAgent'
)
```

### Invoking the Orchestrator

```python
from app.agents.orchestrator import get_orchestrator
from app.agents.runtime_context import AgentContext

orchestrator = await get_orchestrator()

context = AgentContext(
    user_id=user.id,
    user_name=user.name,
    files=user_files
)

config = {
    "configurable": {
        "thread_id": f"chat-{chat_id}",
        "context": context
    }
}

response = await orchestrator.ainvoke(
    {"messages": [{"role": "user", "content": "What's in my files?"}]},
    config
)
```

### Adding a New Tool

```python
from langchain.tools import tool

@tool
def my_custom_tool(param: str) -> str:
    """
    Description of what the tool does.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
    """
    # Implementation
    return result

# Add to orchestrator tools
ORCHESTRATOR_TOOLS.append(my_custom_tool)
```

## 🧪 Testing Agents

```python
import pytest
from app.agents.orchestrator import get_orchestrator

@pytest.mark.asyncio
async def test_orchestrator_routing():
    orchestrator = await get_orchestrator()
    
    config = {
        "configurable": {
            "thread_id": "test-123"
        }
    }
    
    response = await orchestrator.ainvoke(
        {"messages": [{"role": "user", "content": "Search my documents for budget data"}]},
        config
    )
    
    assert "rag_agent" in str(response)
```

## 📊 Monitoring

### LangSmith Integration

All agent executions are automatically traced in LangSmith when configured:

export these vars in dev enironments (LangSmith doesn't read from .env files by default)
```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-key
LANGCHAIN_PROJECT=inkris-agent-monitoring
```

**What's Traced**:
- Agent invocations and tool calls
- Token usage per step
- Latency metrics
- Error traces
- Full conversation history
- Realtime progress when using streaming

### Metrics to Monitor

- **Response Time**: Agent invocation latency
- **Tool Call Success Rate**: Percentage of successful tool executions
- **Token Usage**: Tokens per conversation/agent
- **Checkpoint Size**: State persistence overhead
- **Error Rate**: Failed agent runs

## 🔒 Security Considerations

1. **PII Protection**: Always enable PII middleware in production
2. **Context Isolation**: Ensure agents only access user's own files
3. **Tool Authorization**: Validate user permissions before tool execution
4. **State Encryption**: Consider encrypting checkpoints containing sensitive data
5. **Rate Limiting**: Implement rate limits on agent invocations

## 🐛 Debugging

### Enable Verbose Logging

```python
import logging
logging.getLogger("langchain").setLevel(logging.DEBUG)
```

### Inspect Agent State

```python
checkpointer = get_checkpointer()
state = await checkpointer.aget_tuple(
    {"configurable": {"thread_id": "chat-123"}}
)
print(state.checkpoint)  # Full state snapshot
```

### Test Tools Independently

```python
from app.agents.tools.rag_tools import search_chunks

result = await search_chunks.ainvoke({
    "query": "test query",
    "user_id": user_id
})
print(result)
```

## 🛣️ Roadmap

- [ ] Code execution agent
- [ ] Multi-modal document understanding
- [ ] Agent collaboration (multi-agent debate)
- [ ] Custom agent creation API
- [ ] Agent performance benchmarking
- [ ] Prompt optimization framework

## 🤝 Contributing

When adding new agents or tools:

1. **Create tool definition** in `tools/` with clear docstrings
2. **Implement agent** in `subagents/` if needed
3. **Add tests** for tool functionality
4. **Update prompts** to describe new capabilities
5. **Document** usage in this README
6. **Add monitoring** for new metrics

## 📚 Resources

- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangSmith Tracing](https://docs.smith.langchain.com/)
- [Agent Design Patterns](https://langchain-ai.github.io/langgraph/concepts/)

---

For questions or issues with the agent system, please open an issue or contact the maintainers.