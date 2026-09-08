from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    user_name: str | None
    action: str
    entity_type: str
    entity_id: str | None
    description: str
    changes: dict | None
    created_at: datetime
