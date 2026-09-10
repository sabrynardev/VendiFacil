from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.core.datetime import local_today
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models.user import User
from app.services.analytics import AnalyticsValidationError, analytics_overview, export_csv
from app.services.audit import log_audit

router = APIRouter()


def resolved_period(start: date | None, end: date | None) -> tuple[date, date]:
    final = end or local_today()
    initial = start or (final - timedelta(days=29))
    return initial, final


@router.get("/overview")
def overview(start: date | None = None, end: date | None = None, stopped_days: int = Query(default=30, ge=1, le=730), db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.ANALYTICS_VIEW))):
    initial, final = resolved_period(start, end)
    try:
        return analytics_overview(db, user.account_id, initial, final, stopped_days)
    except AnalyticsValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/export")
def export(report: str, start: date | None = None, end: date | None = None, stopped_days: int = Query(default=30, ge=1, le=730), db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.REPORT_EXPORT))):
    initial, final = resolved_period(start, end)
    try:
        data = analytics_overview(db, user.account_id, initial, final, stopped_days)
        filename, content = export_csv(data, report)
        log_audit(db, user, action="EXPORT", entity_type="ANALYTICS", entity_id=None, description=f"Exportou o relatório {report} de {initial} a {final}.")
        db.commit()
        return {"filename": filename, "content": content}
    except AnalyticsValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
