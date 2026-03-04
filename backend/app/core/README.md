# Core Services Documentation

The `core` directory contains foundational utilities and cross-cutting concerns used throughout the application. These modules provide essential functionality for authentication, error handling, logging, file management, and request context.

## 📋 Overview

Core services are designed to be:
- **Reusable**: Used across multiple API endpoints and services
- **Stateless**: No application state dependencies
- **Well-tested**: High test coverage for critical paths
- **Type-safe**: Comprehensive type annotations

## 📁 Directory Structure

```
core/
├── events/                  # Event publishing system
│   ├── redis.py            # Redis pub/sub implementation
│   └── types.py            # Event type definitions
│
├── middleware/              # HTTP middleware
│   └── request_id.py       # Request ID injection
│
├── auth.py                 # JWT authentication logic
├── context.py              # Request context management
├── deps.py                 # FastAPI dependency injection
├── enums.py                # Application-wide enums
├── error_registry.py       # Error code registry
├── errors.py               # Custom exception classes
├── files.py                # File handling utilities
├── logger.py               # Structured logging setup
├── security.py             # Security utilities (hashing, tokens)
└── README.md               # This file
```

## 🔐 Authentication (`auth.py`)

Handles JWT-based authentication with access and refresh tokens.

### Key Functions

#### `create_access_token`
```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str
```
Creates a JWT access token with user claims.

**Parameters**:
- `data`: Payload to encode (typically `{"sub": user_id}`)
- `expires_delta`: Optional custom expiration time

**Returns**: Encoded JWT string

**Usage**:
```python
from app.core.auth import create_access_token

token = create_access_token(
    data={"sub": str(user.id)},
    expires_delta=timedelta(minutes=15)
)
```

#### `create_refresh_token`
```python
def create_refresh_token(data: dict) -> str
```
Creates a long-lived refresh token for obtaining new access tokens.

**Default Expiration**: 7 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)

#### `decode_token`
```python
def decode_token(token: str) -> dict
```
Validates and decodes a JWT token.

**Raises**:
- `InvalidCredentialsError`: If token is invalid or expired

**Example**:
```python
try:
    payload = decode_token(token)
    user_id = payload.get("sub")
except InvalidCredentialsError:
    # Handle invalid token
```

#### `get_current_user`
```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User
```
FastAPI dependency for extracting authenticated user from token.

**Usage in endpoints**:
```python
@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

### Token Management

**Access Tokens**:
- Short-lived (15 minutes default)
- Used for API authentication
- Stored in HTTP-only cookie

**Refresh Tokens**:
- Long-lived (7 days default)
- Used to obtain new access tokens
- Stored in HTTP-only cookie with strict security settings

### Security Best Practices

1. **Use HTTP-only cookies** in production (`COOKIE_SECURE=True`)
2. **Rotate refresh tokens** on each use
3. **Implement token blacklisting** for logout
4. **Use strong secret keys** (min 32 characters)
5. **Enable HTTPS** in production

## 🔒 Security (`security.py`)

Cryptographic utilities for password hashing and token generation.

### Key Functions

#### `get_password_hash`
```python
def get_password_hash(password: str) -> str
```
Hashes a password using bcrypt.

**Example**:
```python
from app.core.security import get_password_hash

hashed = get_password_hash("user_password")
# Store hashed password in database
```

#### `verify_password`
```python
def verify_password(plain_password: str, hashed_password: str) -> bool
```
Verifies a password against its hash.

**Example**:
```python
from app.core.security import verify_password

if verify_password(input_password, user.hashed_password):
    # Password correct
else:
    # Password incorrect
```

#### `generate_secure_token`
```python
def generate_secure_token(length: int = 32) -> str
```
Generates a cryptographically secure random token.

**Use Cases**:
- Email verification tokens
- Password reset tokens
- API keys

**Example**:
```python
from app.core.security import generate_secure_token

verification_token = generate_secure_token(64)
```

## 🌐 Context Management (`context.py`)

Provides request-scoped context variables using `contextvars`.

### Context Variables

```python
current_request_id: ContextVar[Optional[str]]
current_user_id: ContextVar[Optional[UUID]]
```

### Usage

**Setting Context** (in middleware):
```python
from app.core.context import current_request_id

request_id = str(uuid.uuid4())
current_request_id.set(request_id)
```

**Accessing Context** (anywhere in request):
```python
from app.core.context import current_request_id, current_user_id

request_id = current_request_id.get()
user_id = current_user_id.get()
```

### Benefits

- **No global state**: Thread-safe and async-safe
- **Automatic cleanup**: Context cleared after request
- **Deep access**: Available in nested function calls without explicit passing

## 📦 Dependencies (`deps.py`)

FastAPI dependency injection utilities.

### Database Dependencies

#### `get_db`
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]
```
Provides an async database session.

**Usage**:
```python
@router.get("/items")
async def get_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()
```

#### `get_db_sync`
```python
def get_db_sync() -> Generator[Session, None, None]
```
Provides a synchronous database session (for Celery tasks).

### Storage Dependencies

#### `get_storage`
```python
def get_storage() -> StorageProvider
```
Provides the configured storage provider (S3).

**Usage**:
```python
@router.post("/upload")
async def upload(
    file: UploadFile,
    storage: StorageProvider = Depends(get_storage)
):
    url = await storage.upload(file.file, key="files/myfile.pdf")
    return {"url": url}
```

### Vector Store Dependencies

#### `get_vector_store`
```python
def get_vector_store() -> QdrantStore
```
Provides the vector store instance.

## 🔢 Enums (`enums.py`)

Application-wide enumeration types.

### FileStatus
```python
class FileStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
```

Tracks file processing lifecycle.

### FileType
```python
class FileType(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    WORD = "word"
    TEXT = "text"
```

Supported file formats.

### MessageRole
```python
class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
```

Chat message roles.

### QuotaType
```python
class QuotaType(str, Enum):
    FILE_UPLOADS = "file_uploads"
    API_CALLS = "api_calls"
    STORAGE_BYTES = "storage_bytes"
```

User quota categories.

## 🚨 Error Handling

### Custom Exceptions (`errors.py`)

```python
class AppError(Exception):
    """Base exception for all application errors."""
    def __init__(self, message: str, code: str, status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code

class NotFoundError(AppError):
    """Resource not found."""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} with id {identifier} not found",
            code="NOT_FOUND",
            status_code=404
        )

class InvalidCredentialsError(AppError):
    """Authentication failed."""
    # ...

class QuotaExceededError(AppError):
    """User quota exceeded."""
    # ...
```

### Error Registry (`error_registry.py`)

Centralized error code definitions for consistent error responses.

```python
ERROR_CODES = {
    "AUTH_001": "Invalid credentials",
    "AUTH_002": "Token expired",
    "FILE_001": "File not found",
    "FILE_002": "Unsupported file type",
    "FILE_003": "File too large",
    "QUOTA_001": "Upload quota exceeded",
    # ...
}
```

### Usage in Endpoints

```python
from app.core.errors import NotFoundError, QuotaExceededError

@router.get("/files/{file_id}")
async def get_file(file_id: UUID, db: AsyncSession = Depends(get_db)):
    file = await db.get(File, file_id)
    if not file:
        raise NotFoundError("File", str(file_id))
    return file

@router.post("/upload")
async def upload_file(user: User = Depends(get_current_user)):
    if user.uploads_count >= user.upload_limit:
        raise QuotaExceededError("file_uploads")
    # Process upload
```

### Global Exception Handler

The main app includes a global exception handler for `AppError`:

```python
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "code": exc.code
            }
        }
    )
```

## 📄 File Utilities (`files.py`)

File handling and validation utilities.

### Key Functions

#### `validate_file_type`
```python
def validate_file_type(filename: str, allowed_types: List[str]) -> bool
```
Validates file extension against allowed types.

**Example**:
```python
from app.core.files import validate_file_type

if not validate_file_type(filename, ["pdf", "docx"]):
    raise ValueError("Unsupported file type")
```

#### `get_file_extension`
```python
def get_file_extension(filename: str) -> str
```
Extracts file extension (lowercase, without dot).

#### `generate_file_key`
```python
def generate_file_key(user_id: UUID, filename: str) -> str
```
Generates a unique S3 key for file storage.

**Format**: `users/{user_id}/files/{uuid}-{filename}`

**Example**:
```python
key = generate_file_key(user.id, "report.pdf")
# Result: "users/123e4567-e89b-12d3-a456-426614174000/files/abc123-report.pdf"
```

#### `get_file_size`
```python
async def get_file_size(file: UploadFile) -> int
```
Calculates file size in bytes.

#### `validate_file_size`
```python
def validate_file_size(size: int, max_size: int) -> bool
```
Validates file size against maximum limit.

**Example**:
```python
from app.core.files import validate_file_size
from app.config import settings

if not validate_file_size(file_size, settings.MAX_FILE_SIZE_BYTES):
    raise ValueError("File too large")
```

## 📝 Logging (`logger.py`)

Structured JSON logging with request correlation.

### Configuration

```python
import logging
from app.core.logger import get_logger

logger = get_logger(__name__)
```

### Log Levels

- `DEBUG`: Detailed debugging information
- `INFO`: General informational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

### Usage

```python
from app.core.logger import get_logger

logger = get_logger(__name__)

# Basic logging
logger.info("Processing file upload")

# With context
logger.info("File processed", extra={
    "file_id": str(file_id),
    "size": file_size,
    "type": file_type
})

# Error logging
try:
    process_file()
except Exception as e:
    logger.error("File processing failed", exc_info=True, extra={
        "file_id": str(file_id),
        "error": str(e)
    })
```

### Log Format

```json
{
    "timestamp": "2024-03-04T12:00:00Z",
    "level": "INFO",
    "logger": "app.api.v0.files",
    "message": "File processed",
    "request_id": "abc-123-def-456",
    "user_id": "user-uuid",
    "file_id": "file-uuid",
    "size": 1024000
}
```

### Request ID Correlation

The `request_id` middleware automatically adds a unique ID to each request, which is included in all logs for that request.

## 📡 Event System

### Redis Events (`events/redis.py`)

Real-time event publishing for SSE streaming.

#### `publish_event`
```python
async def publish_event(channel: str, event: dict) -> None
```
Publishes an event to a Redis channel.

**Parameters**:
- `channel`: Channel name (typically `f"chat:{chat_id}"`)
- `event`: Event data dictionary

**Example**:
```python
from app.core.events.redis import publish_event

await publish_event(
    channel=f"chat:{chat_id}",
    event={
        "type": "message",
        "data": {
            "role": "assistant",
            "content": "Hello!"
        }
    }
)
```

#### `subscribe_to_channel`
```python
async def subscribe_to_channel(channel: str) -> AsyncGenerator[dict, None]
```
Subscribes to a Redis channel and yields events.

**Usage in SSE endpoint**:
```python
from app.core.events.redis import subscribe_to_channel

@router.get("/stream/{chat_id}")
async def stream_chat(chat_id: UUID):
    async def event_generator():
        async for event in subscribe_to_channel(f"chat:{chat_id}"):
            yield f"data: {json.dumps(event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

### Event Types (`events/types.py`)

Defines standard event structures.

```python
class EventType(str, Enum):
    MESSAGE_TOKEN = "message_token"
    MESSAGE_COMPLETE = "message_complete"
    TOOL_CALL = "tool_call"
    ERROR = "error"

class Event(BaseModel):
    type: EventType
    data: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

## 🔧 Middleware

### Request ID Middleware (`middleware/request_id.py`)

Injects a unique request ID into each HTTP request.

**Features**:
- Generates UUID for each request
- Adds `X-Request-ID` header to response
- Sets context variable for logging
- Supports client-provided request IDs

**Configuration**:
```python
from app.core.middleware.request_id import RequestIDMiddleware

app.add_middleware(RequestIDMiddleware)
```

**Access in code**:
```python
from app.core.context import current_request_id

request_id = current_request_id.get()
```

## 🧪 Testing Core Services

```python
import pytest
from app.core.auth import create_access_token, decode_token
from app.core.security import get_password_hash, verify_password

def test_token_creation_and_validation():
    # Create token
    token = create_access_token({"sub": "user-123"})
    
    # Decode and validate
    payload = decode_token(token)
    assert payload["sub"] == "user-123"

def test_password_hashing():
    password = "secure_password_123"
    hashed = get_password_hash(password)
    
    # Verify correct password
    assert verify_password(password, hashed)
    
    # Verify incorrect password
    assert not verify_password("wrong_password", hashed)
```

## 🔍 Best Practices

### Error Handling
1. **Always use custom exceptions** for known error cases
2. **Include error codes** for client error handling
3. **Log errors** with full context before raising
4. **Sanitize error messages** before sending to client

### Logging
1. **Use structured logging** with extra fields
2. **Include request IDs** for correlation
3. **Log at appropriate levels** (don't overuse ERROR)
4. **Avoid logging sensitive data** (passwords, tokens)

### Authentication
1. **Validate tokens** on every protected endpoint
2. **Refresh tokens** proactively before expiration
3. **Implement token revocation** for logout
4. **Use dependency injection** for auth checks

### Context Management
1. **Set context** early in request lifecycle
2. **Don't mutate context** after setting
3. **Use context** instead of passing data through layers

## 🛡️ Security Checklist

- [ ] JWT secret key is strong and not committed to version control
- [ ] Cookies are HTTP-only and Secure in production
- [ ] Password hashing uses bcrypt with sufficient work factor
- [ ] File uploads are validated (type, size)
- [ ] Error messages don't leak sensitive information
- [ ] Rate limiting is implemented on auth endpoints
- [ ] CORS is configured properly for production
- [ ] All database queries use parameterized queries (SQLAlchemy)

## 📚 Related Documentation

- [Authentication Flow](../docs/auth-flow.md)
- [Error Handling Guide](../docs/error-handling.md)
- [Logging Best Practices](../docs/logging.md)

---

For questions about core services, please refer to the main project documentation or open an issue.