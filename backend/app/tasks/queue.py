from uuid import UUID

from app.tasks.file_tasks import process_file


def enqueue_file_processing(file_id: UUID) -> None:
    process_file.delay(file_id) 