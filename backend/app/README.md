## `app` package

The `app` package contains the main FastAPI application, HTTP API routes, domain services, data models, storage and vector store integrations, and the LangGraph/LangChain‑based agent system that powers Inkris.

### High‑level layout

- **`main.py`**: FastAPI application definition, startup/shutdown lifecycle, CORS, exception handling, and static file mounting.
- **`config.py`**: Pydantic settings loaded from `.env` (see backend `README.md`).
- **`api/v0`**: Versioned HTTP API routers.
- **`core`**: Cross‑cutting concerns such as logging, auth, errors, events, and middleware.
- **`db`**: Database connections and non‑ORM data stores (e.g., DuckDB).
- **`models`**: SQLAlchemy ORM models.
- **`schemas`**: Pydantic request/response models.
- **`services`**: Business/domain logic around users, files, chats, and document processing.
- **`storage`**: S3 and other storage backends.
- **`vector_store`**: Qdrant integration and vector store abstractions.
- **`tasks`**: Celery configuration and task definitions.
- **`agents`**: Orchestrated LLM agents, tools, and persistence.

### API layer (`api/v0`)

Each module in `api/v0` defines a FastAPI router that wires HTTP endpoints to underlying services:

- **`auth.py`**: Sign‑up, login, refresh tokens, and other auth‑related endpoints.
- **`files.py`**: File upload endpoints, metadata retrieval, triggers for processing, and file status.
- **`events.py`**: Event streaming and progress/status notifications.
- **`chats.py`**: Chat and RAG endpoints that interact with the agent orchestrator.
- **`usage.py`**: Usage and quota tracking endpoints.

Routers are included in `app/main.py` under the `/api/v0` prefix.

### Core (`core`)

Key components:

- **`auth.py`, `security.py`**: Authentication helpers and JWT handling.
- **`deps.py`**: Common FastAPI dependencies (e.g., DB sessions, current user).
- **`errors.py`, `error_registry.py`**: Application error types and shared error codes.
- **`logger.py`**: Logging configuration and logger instance.
- **`files.py`**: Helpers for validating and managing uploaded files.
- **`context.py`**: Request/agent context utilities.
- **`middleware/request_id.py`**: Middleware that attaches a unique request ID for tracing.
- **`events/redis.py`, `events/types.py`**: Event schema definitions and Redis publisher helpers.
- **`enums.py`**: Shared enums such as file extensions and splitter strategies.

### Persistence (`db`, `models`, `schemas`)

- **`db/session.py`**: Sync/async SQLAlchemy session management.
- **`db/duckdb.py`**: DuckDB initialization and connection helpers.
- **`db/model_registry.py`**: central place to register models for migrations or reflection.
- **`models/*.py`**: ORM models for users, files, Excel metadata, quotas, conversations, refresh tokens, and other entities.
- **`schemas/*.py`**: Pydantic models for API contracts (e.g., `User`, `File`, `ChatMessage`, `Usage`).

### Services

- **`services/files.py`**: High‑level file management logic.
- **`services/file_processor.py`**:
  - Fetches uploaded file bytes from S3.
  - Converts documents into pages.
  - Splits pages into semantic chunks using LlamaIndex splitters.
  - Embeds chunks using the configured OpenAI embedding model.
  - Pushes resulting vectors into Qdrant.
  - Persists Excel sheet metadata and stores per‑sheet Parquet files in S3.
  - Publishes `FileProcessingEvent` messages during processing for progress tracking.
- **`services/chats.py`**: Chat and RAG orchestration at the service layer.
- **`services/users.py`**: User‑related business logic.
- **`services/transformers/*`**: Converters, chunkers, and embedders used during ingestion.

### Storage and vector store

- **`storage/base.py`** and **`storage/s3_provider.py`**:
  - Encapsulate S3 client initialization and bucket configuration.
  - Provide simple primitives used by services and tasks to read/write objects.

- **`vector_store/base.py`** and **`vector_store/qdrant.py`**:
  - Define a basic interface for vector stores.
  - Implement a Qdrant‑backed store for creating collections, indexing payload keys, and uploading/querying points.

### Tasks (`tasks`)

- **`tasks/celery.py`**: Celery application configuration; sets broker/result backend and auto‑discovers tasks.
- **`tasks/file_tasks.py`**: Celery tasks for processing documents and Excel files by delegating to `services.file_processor`.
- **`tasks/queue.py`**: Queue and routing configuration.

Tasks are typically triggered from API endpoints or internal services when a file is uploaded or a long‑running operation is requested.

### Agents (`agents`)

The `agents` package contains higher‑level orchestrated agents built on LangGraph/LangChain:

- **`orchestrator.py`**: The main orchestrator graph for combining RAG, tools, and LLM calls.
- **`llms.py`**: LLM client setup and model selection (driven by `Settings`).
- **`prompts.py`**: Prompt templates for system and tool messages.
- **`tools/*`**: Tool implementations such as:
  - **`rag_tools.py`**: query the vector store and compose answers.
  - **`excel_tools.py`**: interact with stored Excel metadata and Parquet data.
  - **`orchestrator_tools.py`**: helpers for the orchestrator itself.
- **`subagents/*`**: Focused agents for specific modalities (e.g., `rag_agent`, `excel_agent`).
- **`middleware/*`**: Agent middleware such as summarization and PII filtering.
- **`persistence/*`**: Pool, checkpointer, and store integrations used to persist agent state in Postgres.
- **`runtime_context.py`, `streaming.py`, `formatters/rag_formatter.py`**:
  - Provide runtime context handling.
  - Stream partial outputs to clients.
  - Format final RAG answers for consumption by the UI.

### How everything fits together

1. A user uploads a file via the HTTP API.
2. The file is stored in S3 and a Celery task is enqueued.
3. The Celery worker runs `file_tasks`, which call into `services.file_processor`.
4. The file is parsed, chunked, embedded, and stored in Qdrant; progress events are published via Redis.
5. When the user starts a chat, `services.chats` and the `agents.orchestrator`:
   - Retrieve relevant chunks from Qdrant.
   - Optionally call tools (Excel, web search, etc.).
   - Ask the LLM to answer, summarize, or generate content.
6. Responses and usage data are returned via the API and surfaced in the frontend.

