import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogResponse

router = APIRouter()


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=200),
    entity_type: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.AUDIT_VIEW)),
):
    query = db.query(AuditLog).filter(AuditLog.account_id == current_user.account_id)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type.upper())
    entries = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        AuditLogResponse(
            id=entry.id,
            user_name=entry.user.name if entry.user else None,
            action=entry.action,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            description=entry.description,
            changes=json.loads(entry.changes) if entry.changes else None,
            created_at=entry.created_at,
        )
        for entry in entries
    ]
