import json
import time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models.resilience import SyncOperationLog
from app.models.sale import Sale
from app.models.user import User
from app.schemas.sale import OfflineSaleCreate, SyncResult
from app.services.resilience import SyncValidationError, record_sync_failure, sync_offline_sale
from app.services.profiles import permission_codes_for_user
from app.api.routes.sales import serialize_sale

router = APIRouter()


@router.post("/sales", response_model=SyncResult)
def sync_sale(payload: OfflineSaleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    started = time.perf_counter()
    try:
        sale, duplicate, conflicts = sync_offline_sale(db, payload, user)
        db.commit()
        db.refresh(sale)
        return SyncResult(operation_id=payload.operation_id, status=sale.sync_status, duplicate=duplicate, conflict=bool(conflicts), conflicts=conflicts, sale=serialize_sale(sale))
    except SyncValidationError as exc:
        db.rollback()
        record_sync_failure(db, payload, user, exc, int((time.perf_counter() - started) * 1000))
        db.commit()
        raise HTTPException(status_code=409, detail={"message": str(exc), "category": exc.category, "operation_id": payload.operation_id}) from exc
    except IntegrityError:
        db.rollback()
        existing = db.query(Sale).filter(Sale.account_id == user.account_id, Sale.idempotency_key == payload.idempotency_key).first()
        if existing:
            conflicts = json.loads(existing.sync_conflict) if existing.sync_conflict else []
            return SyncResult(operation_id=payload.operation_id, status=existing.sync_status, duplicate=True, conflict=bool(conflicts), conflicts=conflicts, sale=serialize_sale(existing))
        raise HTTPException(status_code=409, detail="A operação entrou em conflito e requer revisão.")


@router.get("/logs")
def sync_logs(limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(SyncOperationLog).filter(SyncOperationLog.account_id == user.account_id)
    if PermissionCode.SALES_VIEW.value not in permission_codes_for_user(user):
        query = query.filter(SyncOperationLog.user_id == user.id)
    rows = query.order_by(SyncOperationLog.updated_at.desc()).limit(limit).all()
    return [{"operation_id": row.operation_id, "operation_type": row.operation_type, "device_id": row.device_id, "status": row.status, "attempts": row.attempts, "conflict": row.conflict, "error_category": row.error_category, "error_message": row.error_message, "duration_ms": row.duration_ms, "created_at": row.created_at.isoformat(), "updated_at": row.updated_at.isoformat()} for row in rows]
