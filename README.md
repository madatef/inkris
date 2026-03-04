# Inkris Backend

> A powerful, AI-driven backend for document processing, RAG (Retrieval-Augmented Generation), and intelligent file management with multi-agent orchestration.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.124.4-009688.svg)](https://fastapi.tiangolo.com)

## 📖 Overview

Inkris is an intelligent document management and conversational AI system that enables users to upload files, interact with them through natural language, perform semantic search, leverage web search for context enrichment, and generate multimedia content based on document analysis.

The backend implements a sophisticated multi-agent architecture powered by LangGraph and LangChain, featuring specialized agents for document retrieval, Excel processing, and intelligent orchestration.

## ✨ Key Features

- 🤖 **Multi-Agent System**: Orchestrator-based architecture with specialized sub-agents
- 📄 **Document Processing**: Support for PDFs, Excel files, and various document formats
- 🔍 **Semantic Search**: Vector-based retrieval using Qdrant for intelligent document search
- 💬 **Conversational AI**: Natural language interaction with your documents
- 🌐 **Web Search Integration**: Enriched responses with real-time web data
- 🔒 **Enterprise Security**: JWT authentication, PII detection, and secure file storage
- 📊 **Excel Intelligence**: Specialized agent for spreadsheet analysis and manipulation
- ⚡ **Async Processing**: Background task processing with Celery
- 🎯 **Context-Aware**: Maintains conversation state with LangGraph checkpointing
- 📈 **Observability**: Built-in tracing with LangSmith

## 🏗️ Tech Stack

### Core Framework
- **FastAPI**: Modern, fast web framework for building APIs
- **Python 3.13**: Latest Python with enhanced performance and typing
- **Pydantic**: Data validation and settings management
- **SQLAlchemy**: Async ORM with PostgreSQL support

### AI & ML
- **LangChain**: LLM application framework
- **LangGraph**: Multi-agent workflow orchestration with state management
- **OpenAI**: GPT models for language understanding and generation
- **LlamaIndex**: Document indexing and retrieval

### Vector Store & Embeddings
- **Qdrant**: High-performance vector database for semantic search
- **OpenAI Embeddings**: Text embeddings for vector similarity

### Databases
- **PostgreSQL**: Primary database for application data and agent state
- **DuckDB**: In-process analytics for Excel data processing
- **Redis**: Message broker and caching layer

### Storage & Processing
- **AWS S3**: Object storage for files and media
- **Celery**: Distributed task queue for async processing
- **PyMuPDF**: PDF processing and text extraction
- **openpyxl**: Excel file manipulation

### Observability & Tracing
- **LangSmith**: Agent execution tracing and monitoring
- **Custom Logger**: Structured logging with request tracing

## 📁 Project Structure

```
backend/
├── alembic/                    # Database migrations
│   ├── versions/               # Migration version files
│   ├── env.py                  # Alembic environment configuration
│   └── script.py.mako          # Migration template
│
├── app/
│   ├── agents/                 # Multi-agent system
│   │   ├── formatters/         # Output formatting (RAG responses)
│   │   ├── middleware/         # Agent middleware (PII, summarization)
│   │   ├── persistence/        # State management (checkpointer, connection pool)
│   │   ├── subagents/          # Specialized agents (Excel, RAG)
│   │   ├── tools/              # Agent tool definitions
│   │   ├── llms.py             # LLM configurations
│   │   ├── orchestrator.py     # Main orchestrator agent
│   │   ├── prompts.py          # System prompts
│   │   ├── runtime_context.py  # Agent runtime context
│   │   └── streaming.py        # SSE streaming utilities
│   │
│   ├── api/v0/                 # API endpoints (versioned)
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── chats.py            # Chat/conversation endpoints
│   │   ├── events.py           # SSE event streaming
│   │   ├── files.py            # File upload/management
│   │   └── usage.py            # Usage statistics
│   │
│   ├── core/                   # Core utilities and services
│   │   ├── events/             # Event system (Redis pub/sub)
│   │   ├── middleware/         # HTTP middleware (request ID)
│   │   ├── auth.py             # JWT authentication logic
│   │   ├── context.py          # Request context management
│   │   ├── deps.py             # FastAPI dependencies
│   │   ├── enums.py            # Application enums
│   │   ├── error_registry.py   # Error code registry
│   │   ├── errors.py           # Custom exceptions
│   │   ├── files.py            # File handling utilities
│   │   ├── logger.py           # Logging configuration
│   │   └── security.py         # Password hashing, token generation
│   │
│   ├── db/                     # Database configurations
│   │   ├── duckdb.py           # DuckDB connection management
│   │   ├── model_registry.py   # SQLAlchemy model registry
│   │   └── session.py          # PostgreSQL session management
│   │
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── base.py             # Base model with common fields
│   │   ├── conversation.py     # Conversation/message models
│   │   ├── excel_metadata.py   # Excel file metadata
│   │   ├── file.py             # File models
│   │   ├── quota.py            # User quota tracking
│   │   ├── refresh_token.py    # JWT refresh tokens
│   │   └── user.py             # User model
│   │
│   ├── schemas/                # Pydantic schemas (request/response)
│   │   ├── chat.py             # Chat-related schemas
│   │   ├── file.py             # File schemas
│   │   ├── usage.py            # Usage statistics schemas
│   │   └── user.py             # User schemas
│   │
│   ├── services/               # Business logic layer
│   │   ├── transformers/       # Document processing
│   │   │   ├── base.py         # Base transformer interface
│   │   │   ├── chunkers.py     # Text chunking strategies
│   │   │   └── embedders.py    # Embedding generation
│   │   ├── chats.py            # Chat service logic
│   │   ├── file_processor.py   # File processing orchestration
│   │   ├── files.py            # File management service
│   │   └── users.py            # User management service
│   │
│   ├── storage/                # Object storage abstraction
│   │   ├── base.py             # Storage provider interface
│   │   └── s3_provider.py      # AWS S3 implementation
│   │
│   ├── tasks/                  # Background task processing
│   │   ├── celery.py           # Celery app configuration
│   │   ├── file_tasks.py       # File processing tasks
│   │   └── queue.py            # Task queue management
│   │
│   ├── vector_store/           # Vector database integration
│   │   ├── base.py             # Vector store interface
│   │   └── qdrant.py           # Qdrant implementation
│   │
│   ├── config.py               # Application settings
│   └── main.py                 # FastAPI application entry point
|
├── dis/
│   └── assets/                 # CSS/JS bundles
│
├── .env.example                # Environment variables template
├── .python-version             # Python version specification
├── alembic.ini                 # Alembic configuration
├── pyproject.toml              # Project metadata and dependencies
├── server.py                   # Development server entry point
├── uv.lock                     # Dependency lock file
└── LICENSE                     # MIT License
```

## 🚀 Getting Started

### Prerequisites

- Python 3.13+
- PostgreSQL 14+
- Redis 6+
- AWS Account (for S3 storage)
- Qdrant Cloud account or self-hosted instance
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/inkris.git
   cd frontend
   # Install dependencies
   npm run install
   # Build frontend
   npm run build
   # Or run for production
   npm run build:prod
   # or run dev derver
   npm run dev
   ```
   Copy the frontend build (/dist) to the backend

2. **Set up Python environment**
   ```bash
   cd ../backend
   # Or if you're still in root
   cd backend

   # Using uv (recommended)
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate  # On Windows with Git bash: source .venv\Scripts\activate
   uv sync
   
   # Or using pip
   pip install -e .
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up databases**
   ```bash
   # Run PostgreSQL migrations
   alembic upgrade head
   
   # Ensure Redis is running
   redis-server
   ```

5. **Create Qdrant collection**
   ```python
   # Create and run a setup script or use the API or website
   python -m app.scripts.setup_qdrant
   ```

### Running the Application

#### Development Server
```bash
# from /backend
python server.py
```

The API will be available at `http://127.0.0.1:8000`, or the port you set if changed

#### Celery Workers (separate terminal)
```bash
celery -A app.tasks.celery worker --loglevel=info
# On Windows, you might eant to use the arg --pool=solo
```

#### API Documentation
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## 🔧 Configuration

### Environment Variables

See `.env.example` for all required configuration. Key variables:

#### Application
- `APP_NAME`: Application name
- `PORT`: Server port (default: 8000)
- `DEBUG`: Enable debug mode
- `APP_ENVIRONMENT`: Environment (development/production)

#### Databases
- `DATABASE_URL`: PostgreSQL connection (async)
- `AGENT_STATE_DATABASE_URL`: Agent state DB (sync)
- `AGENT_STATE_DATABASE_URL_ASYNC`: Agent state DB (async)

#### Authentication
- `SECRET_KEY`: JWT signing key
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration
- `REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token expiration

#### External Services
- `OPENAI_API_KEY`: OpenAI API key
- `QDRANT_URL` / `QDRANT_API_KEY`: Vector store
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`: AWS credentials
- `JINA_API_KEY` / `SERPER_API_KEY`: Web search services

#### Observability

LangSmith reads env vars, not .env files. Make sure you use `load_dotenv()` very early in `server.py` or export the vars from the terminal.
- `LANGCHAIN_API_KEY`: LangSmith API key
- `LANGCHAIN_TRACING_V2`: Enable tracing
- `LANGCHAIN_PROJECT`: Project name in LangSmith

## 📚 Architecture

### Multi-Agent System

The system uses a **hierarchical multi-agent architecture**:

1. **Orchestrator Agent**: Main controller that routes requests to specialized agents
2. **RAG Agent**: Handles document retrieval and question answering
3. **Excel Agent**: Specialized in spreadsheet analysis and data manipulation

### Agent Middleware Stack

- **Dynamic Prompts**: Context-aware system prompts with user/file information
- **PII Detection**: Automatic detection and masking of sensitive information
- **Summarization**: Automatic conversation summarization at token thresholds
- **Checkpointing**: Persistent state management across conversations

### Data Flow

```
User Request → API Endpoint → Service Layer → Orchestrator Agent
                                                    ↓
                                    ┌───────────────┴───────────────┐
                                    ↓                               ↓
                              RAG Agent                      Excel Agent
                                    ↓                               ↓
                            Vector Store                     DuckDB Query
                                    ↓                               ↓
                              Retrieved Chunks              Structured Data
                                    ↓                               ↓
                                    └───────────────┬───────────────┘
                                                    ↓
                                            Orchestrator Response
                                                    ↓
                                            Stream to Client
```

### File Processing Pipeline

```
Upload → S3 Storage → Background Task → Document Parsing
                                              ↓
                                        Chunking Strategy
                                              ↓
                                      Embedding Generation
                                              ↓
                                      Vector Store Upload
                                              ↓
                                        Metadata Storage
```

## 🔌 API Overview

### Authentication
- `POST /api/v0/auth/register` - User registration
- `POST /api/v0/auth/login` - User login
- `POST /api/v0/auth/refresh` - Refresh access token
- `POST /api/v0/auth/logout` - User logout

### Files
- `POST /api/v0/files/upload` - Upload file
- `GET /api/v0/files` - List user files
- `GET /api/v0/files/{file_id}` - Get file details
- `DELETE /api/v0/files/{file_id}` - Delete file

### Chats
- `POST /api/v0/chats` - Create new conversation
- `GET /api/v0/chats` - List conversations
- `POST /api/v0/chats/{chat_id}/messages` - Send message
- `GET /api/v0/chats/{chat_id}/messages` - Get message history

### Events
- `GET /api/v0/events/stream` - SSE stream for real-time updates

### Usage
- `GET /api/v0/usage` - Get usage statistics

## 🧪 Testing

If tests are made by contributors:
```bash
# Run tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_agents.py
```

## 📦 Database Migrations

```bash
# Create a new migration (overwrites the current migration if any that's not upgraded)
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## 🐳 Docker Deployment

```bash
# Build image
docker build -t inkris .

# Run with docker-compose
docker-compose up -d
```

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch (or fix)** (`git checkout -b feature/amazing-feature`)
3. **Follow code style**:
   - Use type hints for all functions
   - Follow PEP 8 conventions
   - Add docstrings for public functions
   - Write tests for new features
4. **Commit your changes** (`git commit -m 'Add amazing feature'`)
5. **Push to the branch** (`git push origin feature/amazing-feature`)
6. **Open a Pull Request**

### Code Style

This project uses:
- **Black** for code formatting
- **Ruff** for linting
- **mypy** for type checking

```bash
# Format code
black app/

# Lint
ruff check app/

# Type check
mypy app/
```

### Project-Specific Guidelines

- **Agents**: New agent tools should be added to `app/agents/tools/`
- **API Endpoints**: Use versioned routes under `app/api/v0/`
- **Models**: SQLAlchemy models go in `app/models/`
- **Schemas**: Pydantic schemas in `app/schemas/`
- **Services**: Business logic in `app/services/`

## 📖 Documentation

- [Agents Documentation](./backend/app/agents/README.md) - Multi-agent system architecture
- [Core Services](./backend/app/core/README.md) - Core utilities and services
- [Services Layer](./backend/app/services/README.md) - Business logic documentation
- [Task Queue](./backend/app/tasks/README.md) - Background task processing

## 🔍 Monitoring & Debugging

### LangSmith Tracing
Access your traces at: https://smith.langchain.com

Filter by project name specified in `LANGCHAIN_PROJECT` env variable.

### Logs
Structured JSON logs are written to stdout with request IDs for correlation. You can extend the Logger skeleton to any logging mechanism/service you please.

### Health Checks
```bash
curl http://localhost:8000/health
```

## 🛡️ Security

- JWT-based authentication with refresh tokens
- Secure password hashing with bcrypt
- PII detection and masking in agent conversations (emails and credit cards). You can extend the PII middleware before agent to cover IP addresses, phone numbers, etc.
- File type validation and size limits
- CORS configuration for production
- Secure cookie settings (HttpOnly, SameSite)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Mohammad Atef Diab** - *Initial work*

## 🙏 Acknowledgments

- LangChain team for the agent framework
- Anthropic for Claude Code (used to write this documentation and assist in building frontend)
- OpenAI for GPT models
- FastAPI team for the excellent web framework
- Meta for React
- Open source community for DuckDB, remark-math, rehype-katex, remark-gfm, and all the other beautiful services that made this app possible

## 📞 Support

- GitHub Issues: [Report bugs or request features](https://github.com/yourusername/inkris/issues)
- Email: itsmadatef@gmail.com

---

**Built with ❤️ using FastAPI, Ract, Vite, LangChain, and LangGraph**