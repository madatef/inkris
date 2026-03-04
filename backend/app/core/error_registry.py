from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ErrorContract:
    code: str
    status_code: int
    message: str
    field: Optional[str] = None


# ------------------
# Auth domain errors
# ------------------

INVALID_CREDENTIALS = ErrorContract(
    code="invalid_credentials",
    message="Invalid email or password.",
    status_code=401,
)

EMAIL_EXISTS = ErrorContract(
    code="email_exists",
    message="A user with this email already exists.",
    status_code=409,
)

INVALID_TOKEN = ErrorContract(
    code="invalid_token",
    message="Token is invalid or has expired.",
    status_code=401,
)

USER_NOT_FOUND = ErrorContract(
    code="user_not_found",
    message="User doesn't exist.",
    status_code=404,
)

# -------------------
# Quota domain errors
# -------------------

QUOTA_NOT_FOUND = ErrorContract(
    code="quota_not_found",
    message="Quota record not found for curren user.",
    status_code=404,
)

QUOTA_EXCEEDED_FILES = ErrorContract(
    code="quota_exceeded_files",
    message="You have reached your file upload limit.",
    status_code=403,
)

QUOTA_EXCEEDED_FILE_PROCESSING = ErrorContract(
    code="quota_exceeded_file_processing",
    message="You have exceeded file processing limit. You can only upload files if they can be processed.",
    status_code=403,
)

QUOTA_EXCEEDED_STORAGE = ErrorContract(
    code="quota_exceeded_storage",
    message="You have reached your cloud storage limit.",
    status_code=403,
)

QUOTA_EXCEEDED_CONVERSATIONS = ErrorContract(
    code="quota_exceeded_conversations",
    message="You have reached your conversations limit.",
    status_code=403,
)

QUOTA_EXCEEDED_IMAGES = ErrorContract(
    code="quota_exceeded_images",
    message="You have reached your image generation limit.",
    status_code=403,
)

QUOTA_EXCEEDED_VIDEOS = ErrorContract(
    code="quota_exceeded_videos",
    message="You have reached your video generation limit.",
    status_code=403,
)

QUOTA_EXCEEDED_LLM_TOKENS = ErrorContract(
    code="quota_exceeded_llm_tokens",
    message="You have exceeded your LLM tokens limit.",
    status_code=403,
)

QUOTA_EXCEEDED_EMBEDDING_TOKENS = ErrorContract(
    code="quota_exceeded_embedding_tokens",
    message="You have exceeded your embedding tokens limit.",
    status_code=403,
)

QUOTA_EXCEEDED_WEB_SEARCH = ErrorContract(
    code="quota_exceeded_web_search",
    message="You have exceeded your web search limit.",
    status_code=403,
)

# ------------------
# File domain errors
# ------------------

FILE_NAME_EXISTS = ErrorContract(
    code="file_name_exists",
    message="A file with this name and extension already exists.",
    status_code=409,
    field="name",
)

FILE_NOT_FOUND = ErrorContract(
    code="file_not_found",
    message="File not found.",
    status_code=404,
)

FILE_DELETED = ErrorContract(
    code="file_deleted",
    status_code=410,
    message="This file has been deleted.",
)

FILE_FORBIDDEN = ErrorContract(
    code="file_forbidden",
    message="You do not have access to this file.",
    status_code=403,
)

FILE_UPLOADED = ErrorContract(
    code="file_already_uploaded",
    message="This file has already been uploaded.",
    status_code=400,
)

FILE_UPLOAD_INVALID = ErrorContract(
    code="invalid_file_metadata",
    message="File size and/or format is invalid.",
    status_code=422,
)

FILE_NOT_RECEIVED = ErrorContract(
    code="file_not_received",
    message="Cloud did not receive the file. Delete file and try again.",
    status_code=424,
)

FILE_NOT_READY = ErrorContract(
    code="file_not_ready",
    message="File is not processed yet.",
    status_code=418, # Humor is part of my job
)

# ------------------
# Chat domain errors
# ------------------

CONVERSATION_NOT_FOUND = ErrorContract(
    code="conversation_not_found",
    message="This conversation doesn't exist or has been deleted.",
    status_code=404,
)

CONVERSATION_FORBIDDEN = ErrorContract(
    code="conversation_forbidden",
    message="You don't have access to this conversation",
    status_code=403,
)

CONVERSATION_DELETED = ErrorContract(
    code="conversation_deleted",
    message="This conversation has been deleted.",
    status_code=410,
)