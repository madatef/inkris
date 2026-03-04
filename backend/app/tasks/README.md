# Tasks Documentation

The `tasks` directory contains the background task processing system built on Celery. This enables asynchronous file processing, scheduled jobs, and long-running operations without blocking API requests.

## 📋 Overview

The task system is designed for:

- **Async Processing**: Long-running operations (file processing, embeddings)
- **Reliability**: Automatic retries and error handling
- **Scalability**: Horizontal scaling with multiple workers
- **Monitoring**: Task status tracking and result storage

## 📁 Directory Structure

```
tasks/
├── celery.py          # Celery app configuration
├── file_tasks.py      # File processing tasks
├── queue.py           # Task queue management
└── README.md          # This file
```

## 🏗️ Architecture

```
API Endpoint
    ↓
Queue Task (non-blocking)
    ↓
Redis Broker
    ↓
Celery Worker(s)
    ↓
Task Execution
    ↓
Result Storage (Redis)
```

## ⚙️ Celery Configuration (`celery.py`)

### Celery App Setup

```python
from celery import Celery
from app.config import settings

celery_app = Celery(
    'inkris',
    broker=settings.CELERY_BROKER_URL,      # Redis for task queue
    backend=settings.CELERY_RESULT_BACKEND  # Redis for results
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,        # 1 hour max
    task_soft_time_limit=3300,   # 55 minutes soft limit
    worker_prefetch_multiplier=1, # One task at a time
    worker_max_tasks_per_child=50 # Restart worker after 50 tasks
)
```

### Configuration Options

#### Task Execution
- **`task_time_limit`**: Hard limit (kills task)
- **`task_soft_time_limit`**: Soft limit (raises exception)
- **`task_acks_late`**: Acknowledge after completion (for reliability)
- **`task_reject_on_worker_lost`**: Requeue if worker dies

#### Worker Configuration
- **`worker_prefetch_multiplier`**: Tasks to prefetch (1 = sequential)
- **`worker_max_tasks_per_child`**: Restart worker after N tasks (prevent memory leaks)
- **`worker_concurrency`**: Number of concurrent task executions

#### Result Backend
- **`result_expires`**: How long to keep results (default: 1 day)
- **`result_persistent`**: Persist results to disk

### Celery Beat (Scheduled Tasks)

For periodic tasks:

```python
celery_app.conf.beat_schedule = {
    'cleanup-old-files': {
        'task': 'app.tasks.file_tasks.cleanup_old_files',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
```

## 📄 File Tasks (`file_tasks.py`)

### `process_file_task`

Main task for processing uploaded files.

```python
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def process_file_task(self, file_id: str, user_id: str) -> dict:
    """
    Process uploaded file: extract text, chunk, embed, and store.
    
    Args:
        file_id: UUID of the file to process
        user_id: UUID of the file owner
        
    Returns:
        dict: Processing result with status and metadata
    """
    try:
        # Run async processing
        result = asyncio.run(process_file(
            file_id=UUID(file_id),
            user_id=UUID(user_id)
        ))
        return {
            'status': 'completed',
            'file_id': file_id,
            'chunks_created': result.get('chunks_count', 0)
        }
    except Exception as exc:
        # Update file status to FAILED
        asyncio.run(update_file_status(
            file_id=UUID(file_id),
            status=FileStatus.FAILED,
            error=str(exc)
        ))
        
        # Retry with exponential backoff
        raise self.retry(exc=exc)
```

**Features**:
- **Automatic Retries**: Up to 3 attempts with 60s delay
- **Error Handling**: Updates file status on failure
- **Progress Tracking**: Returns processing statistics
- **Idempotency**: Safe to retry

**Usage from API**:
```python
from app.tasks.file_tasks import process_file_task

@router.post("/upload")
async def upload_file(file: UploadFile):
    # Save file metadata
    db_file = await create_file(...)
    
    # Queue processing task
    task = process_file_task.delay(
        file_id=str(db_file.id),
        user_id=str(current_user.id)
    )
    
    return {
        'file_id': db_file.id,
        'task_id': task.id,
        'status': 'processing'
    }
```

### `delete_file_data_task`

Background cleanup when files are deleted.

```python
@celery_app.task(bind=True)
def delete_file_data_task(self, file_id: str, user_id: str) -> dict:
    """
    Delete file data from all storage systems.
    
    Operations:
    1. Delete from S3
    2. Delete from vector store
    3. Delete Excel metadata (if applicable)
    4. Delete database record
    """
    try:
        asyncio.run(cleanup_file_data(
            file_id=UUID(file_id),
            user_id=UUID(user_id)
        ))
        return {'status': 'deleted', 'file_id': file_id}
    except Exception as exc:
        logger.error(f"File deletion failed: {exc}")
        raise self.retry(exc=exc)
```

### `batch_embed_task`

Batch embedding generation for multiple files.

```python
@celery_app.task
def batch_embed_task(file_ids: List[str], user_id: str) -> dict:
    """
    Process multiple files in batch for efficiency.
    
    Useful for:
    - Bulk file imports
    - Reprocessing after embedding model changes
    - Initial setup for new users
    """
    results = []
    for file_id in file_ids:
        try:
            result = asyncio.run(process_file(
                file_id=UUID(file_id),
                user_id=UUID(user_id)
            ))
            results.append({
                'file_id': file_id,
                'status': 'completed'
            })
        except Exception as e:
            results.append({
                'file_id': file_id,
                'status': 'failed',
                'error': str(e)
            })
    
    return {
        'total': len(file_ids),
        'successful': sum(1 for r in results if r['status'] == 'completed'),
        'failed': sum(1 for r in results if r['status'] == 'failed'),
        'results': results
    }
```

### Scheduled Tasks

#### `cleanup_old_files`

Remove orphaned files and expired data.

```python
@celery_app.task
def cleanup_old_files() -> dict:
    """
    Daily cleanup of:
    - Failed uploads older than 7 days
    - Orphaned vector embeddings
    - Expired temporary files
    """
    asyncio.run(cleanup_old_data())
    return {'status': 'completed'}
```

#### `update_usage_stats`

Calculate and update user usage statistics.

```python
@celery_app.task
def update_usage_stats() -> dict:
    """
    Update usage statistics for all users:
    - File count
    - Storage used
    - API calls this month
    """
    asyncio.run(calculate_usage_stats())
    return {'status': 'completed'}
```

## 🔄 Queue Management (`queue.py`)

Utilities for managing task queues.

### Queue Priorities

```python
class QueuePriority(str, Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

QUEUE_ROUTING = {
    'app.tasks.file_tasks.process_file_task': {
        'queue': 'normal'
    },
    'app.tasks.file_tasks.batch_embed_task': {
        'queue': 'low'
    },
    'app.tasks.file_tasks.delete_file_data_task': {
        'queue': 'high'
    }
}
```

### Task Routing

Configure Celery to route tasks to specific queues:

```python
celery_app.conf.task_routes = QUEUE_ROUTING
```

Start workers for specific queues:
```bash
# High priority worker
celery -A app.tasks.celery worker -Q high --concurrency=4

# Normal priority worker
celery -A app.tasks.celery worker -Q normal --concurrency=2

# Low priority worker
celery -A app.tasks.celery worker -Q low --concurrency=1
```

### Task Status Checking

```python
from celery.result import AsyncResult

def get_task_status(task_id: str) -> dict:
    """Get the status of a task."""
    result = AsyncResult(task_id, app=celery_app)
    
    return {
        'task_id': task_id,
        'status': result.state,
        'result': result.result if result.ready() else None,
        'traceback': result.traceback if result.failed() else None
    }
```

**Task States**:
- `PENDING`: Task waiting to start
- `STARTED`: Task has begun execution
- `SUCCESS`: Task completed successfully
- `FAILURE`: Task failed
- `RETRY`: Task is being retried
- `REVOKED`: Task was cancelled

### Cancelling Tasks

```python
from celery.task.control import revoke

def cancel_task(task_id: str, terminate: bool = False):
    """
    Cancel a running task.
    
    Args:
        task_id: ID of task to cancel
        terminate: If True, forcefully kill the task
    """
    revoke(task_id, terminate=terminate)
```

## 🚀 Running Workers

### Development

```bash
# Single worker
celery -A app.tasks.celery worker --loglevel=info

# With auto-reload
watchmedo auto-restart -d app/ -p '*.py' -- \
    celery -A app.tasks.celery worker --loglevel=info
```

### Production

```bash
# Multiple workers with supervisor
celery multi start worker1 worker2 \
    -A app.tasks.celery \
    --pidfile=/var/run/celery/%n.pid \
    --logfile=/var/log/celery/%n.log \
    --loglevel=INFO \
    --concurrency=4

# With systemd service
sudo systemctl start celery
```

### Monitoring

```bash
# Flower (web-based monitoring)
celery -A app.tasks.celery flower --port=5555

# Access at http://localhost:5555
```

**Flower Features**:
- Real-time task monitoring
- Worker status and statistics
- Task history and results
- Task retry/revoke controls
- Rate limiting configuration

## 📊 Task Patterns

### Task Chaining

Execute tasks sequentially:

```python
from celery import chain

# Process file, then generate summary, then notify user
workflow = chain(
    process_file_task.s(file_id, user_id),
    generate_summary_task.s(),
    notify_user_task.s()
)
workflow.apply_async()
```

### Task Groups

Execute tasks in parallel:

```python
from celery import group

# Process multiple files simultaneously
job = group(
    process_file_task.s(file_id, user_id)
    for file_id in file_ids
)
result = job.apply_async()
```

### Callbacks

Execute task on success/failure:

```python
process_file_task.apply_async(
    args=[file_id, user_id],
    link=on_success_task.s(),      # Called on success
    link_error=on_error_task.s()   # Called on failure
)
```

### Periodic Tasks with Crontab

```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'daily-cleanup': {
        'task': 'app.tasks.file_tasks.cleanup_old_files',
        'schedule': crontab(hour=2, minute=0),
    },
    'hourly-stats': {
        'task': 'app.tasks.file_tasks.update_usage_stats',
        'schedule': crontab(minute=0),  # Every hour
    },
    'weekly-report': {
        'task': 'app.tasks.reporting.generate_weekly_report',
        'schedule': crontab(day_of_week=1, hour=9),  # Monday 9 AM
    }
}
```

## 🧪 Testing Tasks

### Unit Testing

```python
import pytest
from app.tasks.file_tasks import process_file_task

def test_process_file_task(monkeypatch):
    # Mock the file processing
    async def mock_process(*args, **kwargs):
        return {'chunks_count': 10}
    
    monkeypatch.setattr(
        'app.tasks.file_tasks.process_file',
        mock_process
    )
    
    # Test task
    result = process_file_task(
        file_id='test-id',
        user_id='user-id'
    )
    
    assert result['status'] == 'completed'
    assert result['chunks_created'] == 10
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_file_processing_end_to_end(celery_worker):
    # Upload file
    file = await create_file(...)
    
    # Queue task
    task = process_file_task.delay(str(file.id), str(user_id))
    
    # Wait for completion (in test only!)
    result = task.get(timeout=10)
    
    # Verify
    assert result['status'] == 'completed'
    
    # Check database
    processed_file = await get_file_by_id(file.id)
    assert processed_file.status == FileStatus.COMPLETED
```

### Eager Mode (Synchronous)

For testing without Redis:

```python
# In test configuration
celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True

# Tasks run synchronously in tests
result = process_file_task(file_id, user_id)  # Blocks until complete
```

## 🔍 Monitoring and Debugging

### Task Logging

```python
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@celery_app.task
def my_task(arg):
    logger.info(f"Processing {arg}")
    try:
        # Task logic
        logger.debug("Step 1 complete")
    except Exception as e:
        logger.error(f"Task failed: {e}", exc_info=True)
        raise
```

### Task Events

Enable events for monitoring:

```bash
celery -A app.tasks.celery worker --events
```

### Inspecting Workers

```python
from celery import Celery

app = Celery('inkris')

# Get active tasks
i = app.control.inspect()
active = i.active()
scheduled = i.scheduled()
reserved = i.reserved()

# Get worker stats
stats = i.stats()
```

### Debugging Failed Tasks

```python
from celery.result import AsyncResult

task_result = AsyncResult(task_id)

if task_result.failed():
    print(f"Error: {task_result.result}")
    print(f"Traceback: {task_result.traceback}")
```

## ⚡ Performance Optimization

### Prefetch Settings

```python
# Conservative: One task at a time (prevents blocking)
celery_app.conf.worker_prefetch_multiplier = 1

# Aggressive: Multiple tasks (better throughput)
celery_app.conf.worker_prefetch_multiplier = 4
```

### Connection Pool

```python
celery_app.conf.broker_pool_limit = 10  # Max broker connections
```

### Task Compression

```python
celery_app.conf.task_compression = 'gzip'  # Compress large payloads
```

### Result Backend Optimization

```python
# Don't store results if not needed
@celery_app.task(ignore_result=True)
def fire_and_forget_task():
    ...

# Short result expiration
celery_app.conf.result_expires = 3600  # 1 hour
```

## 🔒 Security Considerations

### Input Validation

```python
@celery_app.task
def process_file_task(file_id: str, user_id: str):
    # Validate UUIDs
    try:
        file_uuid = UUID(file_id)
        user_uuid = UUID(user_id)
    except ValueError:
        raise ValueError("Invalid UUID format")
    
    # Verify ownership
    if not is_owner(user_uuid, file_uuid):
        raise PermissionError("Unauthorized")
```

### Rate Limiting

```python
@celery_app.task(rate_limit='10/m')  # 10 tasks per minute
def rate_limited_task():
    ...
```

### Secure Task Serialization

```python
# Use JSON (not pickle) for security
celery_app.conf.task_serializer = 'json'
celery_app.conf.accept_content = ['json']
```

## 🛠️ Troubleshooting

### Common Issues

**Workers not consuming tasks**
```bash
# Check worker status
celery -A app.tasks.celery inspect active

# Check queue length
celery -A app.tasks.celery inspect reserved
```

**Task timeouts**
```python
# Increase time limits
celery_app.conf.task_time_limit = 7200  # 2 hours
```

**Memory leaks**
```python
# Restart workers periodically
celery_app.conf.worker_max_tasks_per_child = 100
```

**Redis connection issues**
```python
# Increase retry on connection failure
celery_app.conf.broker_connection_retry_on_startup = True
```

## 📚 Best Practices

1. **Idempotent Tasks**: Tasks should be safe to retry
   ```python
   # Good: Check if already processed
   if file.status == FileStatus.COMPLETED:
       return {'status': 'already_completed'}
   ```

2. **Short-Running Tasks**: Break long operations into smaller tasks
   ```python
   # Good: Chain of small tasks
   chain(extract_task.s(), chunk_task.s(), embed_task.s())
   
   # Bad: One huge task
   process_everything_task.s()
   ```

3. **Error Handling**: Always handle and log errors
   ```python
   try:
       risky_operation()
   except Exception as e:
       logger.error(f"Failed: {e}", exc_info=True)
       raise
   ```

4. **Task Naming**: Use descriptive names with module prefix
   ```python
   # Good
   @celery_app.task(name='files.process')
   
   # Bad
   @celery_app.task(name='process')
   ```

5. **Avoid Database in Tasks**: Pass IDs, not objects
   ```python
   # Good
   task.delay(file_id=file.id)
   
   # Bad
   task.delay(file=file)  # Can't serialize
   ```

## 🛣️ Roadmap

- [ ] Task result webhooks
- [ ] Dynamic task priority
- [ ] Task dependency graphs
- [ ] Advanced retry strategies
- [ ] Task result caching
- [ ] Multi-tenant task isolation

## 🤝 Contributing

When adding new tasks:

1. **Add to appropriate file** (`file_tasks.py`, etc.)
2. **Include docstring** with args, returns, raises
3. **Add error handling** and logging
4. **Make idempotent** (safe to retry)
5. **Add tests** for task logic
6. **Update this README** with new tasks
7. **Configure routing** in `queue.py`

---

For questions about task processing, please open an issue or contact the maintainers.