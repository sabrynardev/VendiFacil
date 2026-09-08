import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


def log_audit(
    db: Session,
    user: User,
    *,
    action: str,
    entity_type: str,
    entity_id: int | str | None,
    description: str,
    changes: dict[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(
        account_id=user.account_id,
        user_id=user.id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        description=description,
        changes=json.dumps(changes, ensure_ascii=False, default=str) if changes else None,
    )
    db.add(entry)
    return entry
