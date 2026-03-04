from dataclasses import dataclass
from uuid import UUID

@dataclass
class AgentContext:
    user_id: UUID | str
    user_name: str
    files: [str]
