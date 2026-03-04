from enum import StrEnum

class FileExtensionEnum(StrEnum):
    PDF = "pdf"
    TXT = "txt"
    MD = "md"
    XLS = "xls"
    XLSX = "xlsx"

class FileStatusEnum(StrEnum):
    PENDING = "pending"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"
    DELETED = "deleted"

class ChunkTypeEnum(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    ENTITY = "entity"

class LlamaIndexSplitterEnum(StrEnum):
    SENTENCE = "sentence"
    HIERARCHICAL = "hierarchical"

class VectorPointRelationEnum(StrEnum):
    PARENT = "4"
    PREVIOUS = "2"
    NEXT = "3"
    SOURCE = "1"

class ConversationScopeEnum(StrEnum):
    FILE = "file"
    STUDIO = "studio"

class MessageRoleEnum(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"

class AgentEventTypeEnum(StrEnum):
    STATUS = "status"
    TOOL = "tool"
    TOKEN = "token"
    ERROR = "error"
    DONE = "done"