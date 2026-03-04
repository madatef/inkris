## Backend overview

This directory contains the Inkris backend, built with **FastAPI**, **Celery**, **PostgreSQL**, **Redis**, **Qdrant**, and **AWS S3**.

At a high level, the backend is responsible for:

- **HTTP API** for authentication, usage tracking, file upload, events, and chat.
- **Document & Excel ingestion** into object storage and the vector store.
- **Retrieval‑augmented generation (RAG)** over stored documents.
- **Agent orchestration** combining RAG, tools (Excel, web search, etc.) and LLMs.
- **Background processing** for long‑running ingestion and analysis tasks.

### Key entry points

- **`server.py`**: Uvicorn entrypoint; configures the event loop (Windows‑friendly) and starts `app.main:app`.
- **`app/main.py`**:
  - Creates the FastAPI app and configures CORS and exception handling.
  - Initializes Celery, Qdrant collections and indexes, LangGraph persistence, and DuckDB on startup.
  - Includes all versioned API routers under `/api/v0`.
  - Serves the built frontend from `dist/` in production and exposes `/health`.

### Configuration

- **`app/config.py`** defines a `Settings` class (Pydantic settings) and reads environment variables from `.env` by default.
- **`.env.example`** documents all required configuration values:
  - App metadata and limits.
  - Database connection strings (async/sync, including agent state DB).
  - JWT/auth settings and cookie behavior.
  - Redis URLs for Celery and events.
  - AWS credentials and bucket names for file and media storage.
  - Qdrant URL/API key/collection name.
  - LLM model names and provider keys.
  - Web search and crawling keys.
  - LangSmith / LangChain tracing configuration.

Copy `.env.example` to `.env` and fill in the values appropriate to your environment.

### Architecture by area

- **API layer (`app/api/v0`)**
  - `auth.py`: authentication and user‑related endpoints.
  - `files.py`: file upload, metadata, and processing triggers.
  - `events.py`: event streaming and progress updates.
  - `chats.py`: chat and RAG endpoints.
  - `usage.py`: usage, quota, and billing‑related endpoints.

- **Core utilities (`app/core`)**
  - `auth.py`, `security.py`: auth helpers, password hashing, JWT handling.
  - `deps.py`: FastAPI dependencies (DB sessions, current user, etc.).
  - `errors.py`, `error_registry.py`: centralized error types and codes.
  - `logger.py`: structured logging configuration.
  - `files.py`: common file and path utilities.
  - `context.py`: request/agent context helpers.
  - `middleware/request_id.py`: request ID middleware.
  - `events/*`: Redis‑based event definitions and publisher.
  - `enums.py`: shared enums (file extensions, splitters, etc.).

- **Persistence (`app/db`, `app/models`, `alembic`)**
  - `db/session.py`: sync/async SQLAlchemy sessions.
  - `db/duckdb.py`: DuckDB initialization for analytics‑style workloads.
  - `db/model_registry.py`: model registration helpers.
  - `models/*.py`: SQLAlchemy models for users, files, Excel metadata, conversations, quotas, refresh tokens, etc.
  - `alembic/versions/*`: migration history for the relational database.

- **Storage (`app/storage`)**
  - `base.py`: base storage abstractions.
  - `s3_provider.py`: S3 client and bucket configuration used to store file bytes and derived assets.

- **Vector store (`app/vector_store`)**
  - `base.py`: common vector store interfaces.
  - `qdrant.py`: async Qdrant client wrapper for collection creation, payload indexing, and point upserts/queries.

- **Services (`app/services`)**
  - `files.py`: high‑level file management (e.g., linking uploads to users).
  - `file_processor.py`: document and Excel ingestion pipeline:
    - Reads bytes from S3.
    - Converts documents to pages.
    - Splits pages into semantic chunks via LlamaIndex splitters.
    - Embeds with `openai_text_small`.
    - Uploads points to Qdrant and publishes progress events.
  - `chats.py`: business logic for chats and RAG over stored content.
  - `users.py`: user‑related domain logic.
  - `transformers/*`: bytes‑to‑pages conversion, chunkers, and embedders.

- **Tasks (`app/tasks`)**
  - `celery.py`: Celery app configuration (broker, backend, queues).
  - `file_tasks.py`: Celery tasks for processing documents and Excel files.
  - `queue.py`: task queue definitions and helpers.

- **Agents (`app/agents`)**
  - `orchestrator.py`: LangGraph‑based orchestration of tools, RAG, and LLM calls.
  - `llms.py`: LLM client setup and model selection.
  - `tools/*`: tool implementations (e.g., RAG tools, Excel tools, orchestrator tools).
  - `subagents/*`: focused agents such as RAG and Excel agents.
  - `middleware/*`: agent‑specific middleware (summarization, PII handling, etc.).
  - `persistence/*`: agent state pool, checkpointing, and store implementation.
  - `runtime_context.py`, `streaming.py`, `formatters/*`: runtime scaffolding for agent runs and formatting of responses.

### Running the backend

1. Follow the root `README.md` to set up Python, dependencies, and `.env`.
2. Run database migrations with Alembic.
3. Start the API server via `python server.py`.
4. Start Celery workers for background processing.

See the per‑directory READMEs inside `app/` for more detailed documentation of specific areas.

