# Services Documentation

The `services` directory contains the business logic layer of the application. Services orchestrate operations across multiple models, handle complex workflows, and encapsulate domain-specific logic.

## 📋 Overview

Services follow these principles:

- **Separation of Concerns**: Each service handles a specific domain
- **Database Agnostic**: Services receive database sessions as parameters
- **Testable**: Pure functions with minimal side effects
- **Reusable**: Used by API endpoints and background tasks
- **Type-Safe**: Comprehensive type annotations

## 📁 Directory Structure

```
services/
├── transformers/            # Document processing pipeline
│   ├── base.py             # Base transformer interface
│   ├── chunkers.py         # Text chunking strategies
│   └── embedders.py        # Embedding generation
│
├── chats.py                # Chat/conversation management
├── file_processor.py       # File processing orchestration
├── files.py                # File management service
├── users.py                # User management service
└── README.md               # This file
```

## 👤 User Service (`users.py`)

Handles user account management, authentication, and profile operations.

### Key Functions

#### `create_user`
```python
async def create_user(
    db: AsyncSession,
    email: str,
    password: str,
    name: str
) -> User
```
Creates a new user account.

**Features**:
- Email validation
- Password hashing
- Duplicate email check
- Initial quota setup

**Example**:
```python
from app.services.users import create_user

user = await create_user(
    db=db,
    email="user@example.com",
    password="secure_password",
    name="John Doe"
)
```

**Raises**:
- `ValueError`: If email already exists
- `ValidationError`: If email format is invalid

#### `authenticate_user`
```python
async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str
) -> Optional[User]
```
Authenticates user credentials.

**Returns**: User object if credentials valid, None otherwise

**Example**:
```python
from app.services.users import authenticate_user

user = await authenticate_user(db, email, password)
if user:
    # Generate tokens
else:
    # Invalid credentials
```

#### `get_user_by_email`
```python
async def get_user_by_email(
    db: AsyncSession,
    email: str
) -> Optional[User]
```
Retrieves user by email address.

#### `get_user_by_id`
```python
async def get_user_by_id(
    db: AsyncSession,
    user_id: UUID
) -> Optional[User]
```
Retrieves user by ID.

#### `update_user`
```python
async def update_user(
    db: AsyncSession,
    user_id: UUID,
    **updates
) -> User
```
Updates user profile fields.

**Allowed Fields**:
- `name`
- `email` (with validation)
- `password` (automatically hashed)

**Example**:
```python
updated_user = await update_user(
    db,
    user_id=user.id,
    name="Jane Doe"
)
```

#### `delete_user`
```python
async def delete_user(
    db: AsyncSession,
    user_id: UUID
) -> bool
```
Soft-deletes a user account.

**Cascading Effects**:
- Marks user as deleted
- Removes files from storage
- Deletes vector embeddings
- Cancels refresh tokens

## 📄 File Service (`files.py`)

Manages file metadata, uploads, and lifecycle.

### Key Functions

#### `create_file`
```python
async def create_file(
    db: AsyncSession,
    user_id: UUID,
    filename: str,
    content_type: str,
    size: int,
    storage_key: str,
    file_type: FileType
) -> File
```
Creates a file record in the database.

**Example**:
```python
from app.services.files import create_file

file = await create_file(
    db=db,
    user_id=current_user.id,
    filename="report.pdf",
    content_type="application/pdf",
    size=1024000,
    storage_key="users/123/files/abc-report.pdf",
    file_type=FileType.PDF
)
```

#### `get_user_files`
```python
async def get_user_files(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    file_type: Optional[FileType] = None
) -> List[File]
```
Retrieves files for a user with pagination.

**Parameters**:
- `skip`: Offset for pagination
- `limit`: Max number of results
- `file_type`: Optional filter by type

**Example**:
```python
# Get all PDFs
pdf_files = await get_user_files(
    db, user_id, file_type=FileType.PDF
)

# Paginated results
files = await get_user_files(db, user_id, skip=0, limit=20)
```

#### `get_file_by_id`
```python
async def get_file_by_id(
    db: AsyncSession,
    file_id: UUID,
    user_id: UUID
) -> Optional[File]
```
Retrieves a specific file with ownership verification.

**Security**: Returns None if file doesn't belong to user

#### `delete_file`
```python
async def delete_file(
    db: AsyncSession,
    file_id: UUID,
    user_id: UUID,
    storage: StorageProvider
) -> bool
```
Deletes a file and its associated data.

**Cleanup Operations**:
1. Delete from object storage
2. Remove vector embeddings
3. Delete Excel metadata (if applicable)
4. Remove database record

**Example**:
```python
from app.services.files import delete_file

success = await delete_file(
    db=db,
    file_id=file_id,
    user_id=current_user.id,
    storage=storage_provider
)
```

#### `update_file_status`
```python
async def update_file_status(
    db: AsyncSession,
    file_id: UUID,
    status: FileStatus,
    error: Optional[str] = None
) -> File
```
Updates file processing status.

**Statuses**:
- `PENDING`: Upload complete, awaiting processing
- `PROCESSING`: Currently being processed
- `COMPLETED`: Successfully processed
- `FAILED`: Processing failed (error message in `error` field)

## 💬 Chat Service (`chats.py`)

Manages conversations and messages between users and the AI agent.

### Key Functions

#### `create_conversation`
```python
async def create_conversation(
    db: AsyncSession,
    user_id: UUID,
    title: Optional[str] = None
) -> Conversation
```
Creates a new conversation thread.

**Auto-generated Title**: If not provided, title is generated from first message

**Example**:
```python
from app.services.chats import create_conversation

conversation = await create_conversation(
    db=db,
    user_id=current_user.id,
    title="Budget Analysis"
)
```

#### `get_user_conversations`
```python
async def get_user_conversations(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 50
) -> List[Conversation]
```
Retrieves user's conversations, ordered by most recent.

#### `get_conversation`
```python
async def get_conversation(
    db: AsyncSession,
    conversation_id: UUID,
    user_id: UUID
) -> Optional[Conversation]
```
Retrieves a specific conversation with ownership verification.

#### `add_message`
```python
async def add_message(
    db: AsyncSession,
    conversation_id: UUID,
    role: MessageRole,
    content: str,
    metadata: Optional[dict] = None
) -> Message
```
Adds a message to a conversation.

**Parameters**:
- `role`: USER, ASSISTANT, or SYSTEM
- `content`: Message text
- `metadata`: Optional JSON metadata (tool calls, citations, etc.)

**Example**:
```python
from app.services.chats import add_message
from app.core.enums import MessageRole

# User message
user_msg = await add_message(
    db=db,
    conversation_id=conv_id,
    role=MessageRole.USER,
    content="What's in the budget report?"
)

# Assistant message with metadata
assistant_msg = await add_message(
    db=db,
    conversation_id=conv_id,
    role=MessageRole.ASSISTANT,
    content="Here's what I found...",
    metadata={
        "sources": [{"file_id": "...", "page": "3"}]
    }
)
```

#### `get_conversation_messages`
```python
async def get_conversation_messages(
    db: AsyncSession,
    conversation_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[Message]
```
Retrieves messages for a conversation, ordered chronologically.

#### `delete_conversation`
```python
async def delete_conversation(
    db: AsyncSession,
    conversation_id: UUID,
    user_id: UUID
) -> bool
```
Deletes a conversation and all its messages.

**Note**: Agent checkpoints are NOT automatically deleted (they're in a separate DB)

#### `update_conversation_title`
```python
async def update_conversation_title(
    db: AsyncSession,
    conversation_id: UUID,
    title: str
) -> Conversation
```
Updates conversation title.

## 🔄 File Processor (`file_processor.py`)

Orchestrates the complete file processing pipeline from upload to vectorization.

### Processing Pipeline

```
1. File Upload → S3
2. Content Extraction (PDF text, Excel schema)
3. Text Chunking
4. Embedding Generation
5. Vector Store Upload
6. Metadata Storage
7. Status Update
```

### Key Functions

#### `process_file`
```python
async def process_file(
    file_id: UUID,
    user_id: UUID
) -> None
```
Main entry point for file processing (called by Celery task).

**Steps**:
1. Retrieve file metadata from DB
2. Download file from S3
3. Extract text/data based on file type
4. Chunk text using appropriate strategy
5. Generate embeddings
6. Upload to vector store
7. Update file status

**Error Handling**:
- Updates status to FAILED on errors
- Logs error message to database
- Preserves file record for debugging

**Example** (in Celery task):
```python
from app.services.file_processor import process_file

@celery.task
def process_file_task(file_id: str, user_id: str):
    asyncio.run(process_file(
        file_id=UUID(file_id),
        user_id=UUID(user_id)
    ))
```

#### `extract_text_from_pdf`
```python
async def extract_text_from_pdf(
    file_path: str
) -> List[Dict[str, Any]]
```
Extracts text from PDF with page-level granularity.

**Returns**:
```python
[
    {
        "page": 1,
        "page_label": "1",
        "text": "Page content..."
    },
    ...
]
```

**Features**:
- Preserves page numbers
- Handles multi-column layouts
- Extracts tables as text

#### `process_excel_file`
```python
async def process_excel_file(
    file_id: UUID,
    file_path: str,
    storage_key: str
) -> None
```
Processes Excel files for SQL querying.

**Operations**:
1. Extract all sheets and schemas
2. Store metadata in `excel_metadata` table
3. Create DuckDB-accessible reference

**Stored Metadata**:
- Sheet names
- Column names and types
- Row count per sheet
- Storage key for data access

## 🔧 Transformers

Document processing pipeline components.

### Base Transformer (`transformers/base.py`)

Abstract interface for document transformers.

```python
class BaseTransformer(ABC):
    @abstractmethod
    async def transform(self, document: Any) -> Any:
        """Transform a document."""
        pass
```

### Chunkers (`transformers/chunkers.py`)

Text chunking strategies for optimal retrieval.

#### `SentenceChunker`
Splits text by sentences with overlap.

**Configuration**:
- `chunk_size`: Target tokens per chunk (default: 512)
- `overlap`: Overlapping tokens (default: 50)

**Use Case**: General documents, articles, reports

**Example**:
```python
from app.services.transformers.chunkers import SentenceChunker

chunker = SentenceChunker(chunk_size=512, overlap=50)
chunks = chunker.chunk(text)
```

#### `RecursiveChunker`
Hierarchical splitting (paragraphs → sentences → tokens).

**Configuration**:
- `chunk_size`: Target chunk size
- `overlap`: Overlap size
- `separators`: Custom split patterns

**Use Case**: Structured documents with clear hierarchies

#### `SemanticChunker`
Groups semantically similar sentences (uses embeddings).

**Configuration**:
- `buffer_size`: Sentences to consider
- `breakpoint_threshold`: Similarity threshold for splits

**Use Case**: Maximum semantic coherence, research papers

**Example**:
```python
from app.services.transformers.chunkers import SemanticChunker

chunker = SemanticChunker(buffer_size=3)
chunks = await chunker.chunk(text)
```

### Embedders (`transformers/embedders.py`)

Generate vector embeddings for text.

#### `OpenAIEmbedder`
Uses OpenAI's embedding models.

**Model**: `text-embedding-3-small` (1536 dimensions)

**Features**:
- Batch processing (up to 100 texts)
- Rate limiting aware
- Retry logic

**Example**:
```python
from app.services.transformers.embedders import OpenAIEmbedder

embedder = OpenAIEmbedder()
embeddings = await embedder.embed([
    "First text to embed",
    "Second text to embed"
])
# Returns: List[List[float]]
```

**Configuration**:
```python
class OpenAIEmbedder:
    def __init__(
        self,
        model: str = "text-embedding-3-small",
        batch_size: int = 100
    ):
        ...
```

## 🔄 Service Patterns

### Database Session Management

All services accept database sessions as parameters:

```python
async def some_service_function(
    db: AsyncSession,
    ...
) -> Result:
    # Use db for queries
    result = await db.execute(query)
    await db.commit()
    return result
```

**Benefits**:
- Testable (mock DB easily)
- Transaction control in caller
- No global state

### Error Handling

Services raise domain-specific exceptions:

```python
from app.core.errors import NotFoundError, QuotaExceededError

async def get_file(db: AsyncSession, file_id: UUID) -> File:
    file = await db.get(File, file_id)
    if not file:
        raise NotFoundError("File", str(file_id))
    return file
```

### Validation

Use Pydantic schemas for input validation:

```python
from app.schemas.user import UserCreate

async def create_user(
    db: AsyncSession,
    user_data: UserCreate
) -> User:
    # user_data is already validated
    ...
```

## 🧪 Testing Services

### Unit Testing

```python
import pytest
from app.services.users import create_user

@pytest.mark.asyncio
async def test_create_user(db_session):
    user = await create_user(
        db=db_session,
        email="test@example.com",
        password="password123",
        name="Test User"
    )
    
    assert user.email == "test@example.com"
    assert user.hashed_password != "password123"  # Should be hashed
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_file_processing_pipeline(
    db_session,
    storage_provider,
    vector_store
):
    # Upload file
    file = await create_file(...)
    
    # Process
    await process_file(file.id, user_id)
    
    # Verify
    processed_file = await get_file_by_id(db_session, file.id, user_id)
    assert processed_file.status == FileStatus.COMPLETED
    
    # Check vector store
    count = await vector_store.count(
        collection=settings.QDRANT_COLLECTION,
        filters=[VectorFilter(key="file_id", values=[str(file.id)])]
    )
    assert count > 0
```

### Mocking External Services

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_process_file_with_mock_storage():
    with patch('app.services.file_processor.storage') as mock_storage:
        mock_storage.download.return_value = b"PDF content"
        
        await process_file(file_id, user_id)
        
        mock_storage.download.assert_called_once()
```

## 📊 Performance Considerations

### Database Queries

**Use selective loading**:
```python
# Good: Only load needed fields
result = await db.execute(
    select(File.id, File.filename, File.status)
    .where(File.user_id == user_id)
)

# Bad: Load entire object when only ID needed
files = await db.execute(select(File).where(...))
```

**Use batch operations**:
```python
# Good: Batch insert
db.add_all([Message(...) for msg in messages])

# Bad: Individual inserts
for msg in messages:
    db.add(Message(...))
    await db.flush()
```

### Embedding Generation

**Batch embeddings**:
```python
# Process in batches of 100
for i in range(0, len(chunks), 100):
    batch = chunks[i:i+100]
    embeddings = await embedder.embed(batch)
```

### Caching

Consider caching for:
- User quota checks
- File metadata lookups
- Frequently accessed conversations

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_quota(user_id: str) -> int:
    # Cache quota for 5 minutes
    ...
```

## 🔐 Security Best Practices

1. **Always verify ownership** before operations:
   ```python
   file = await get_file_by_id(db, file_id, user_id)
   if not file:
       raise NotFoundError("File", str(file_id))
   ```

2. **Sanitize user inputs**:
   ```python
   # Use Pydantic for validation
   user_data = UserCreate(**request_data)
   ```

3. **Don't expose internal errors** to API:
   ```python
   try:
       process_file(...)
   except Exception as e:
       logger.error(f"Processing failed: {e}")
       raise ProcessingError("File processing failed")
   ```

4. **Hash passwords** before storage:
   ```python
   user.hashed_password = get_password_hash(password)
   ```

## 🛣️ Roadmap

- [ ] Caching layer for frequently accessed data
- [ ] Batch file processing
- [ ] Advanced quota management (per-feature quotas)
- [ ] File versioning support
- [ ] Collaborative conversations
- [ ] Export conversation history
- [ ] Advanced search across all user files

## 🤝 Contributing

When adding new services:

1. **Follow existing patterns** (async, type hints, error handling)
2. **Add docstrings** to all public functions
3. **Write tests** for new functionality
4. **Update this README** with new services
5. **Consider performance** implications

## 📚 Related Documentation

- [API Endpoints](../api/README.md)
- [Database Models](../models/README.md)
- [Task Queue](../tasks/README.md)

---

For questions about services, please open an issue or contact the maintainers.