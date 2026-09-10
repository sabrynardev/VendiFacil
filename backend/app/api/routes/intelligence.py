from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.core.config import get_settings
from app.core.datetime import local_today
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models.user import User
from app.services.intelligence import IntelligenceValidationError, ask_vendi, generate_insights, stock_forecast

router = APIRouter()
settings = get_settings()


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    start: date | None = None
    end: date | None = None


@router.get("/forecast")
def forecast(
    end: date | None = None,
    window_days: int = Query(default=settings.intelligence_default_window_days, ge=7, le=180),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PermissionCode.INTELLIGENCE_VIEW)),
):
    try:
        return stock_forecast(db, user.account_id, end or local_today(), window_days)
    except IntelligenceValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/insights")
def insights(
    start: date | None = None,
    end: date | None = None,
    category: str | None = None,
    priority: str | None = None,
    window_days: int = Query(default=settings.intelligence_default_window_days, ge=7, le=180),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PermissionCode.INTELLIGENCE_VIEW)),
):
    final = end or local_today()
    initial = start or (final - timedelta(days=window_days - 1))
    try:
        result = generate_insights(db, user.account_id, initial, final, window_days)
    except IntelligenceValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if category:
        result["insights"] = [item for item in result["insights"] if item["category"].casefold() == category.casefold()]
    if priority:
        result["insights"] = [item for item in result["insights"] if item["priority"] == priority.upper()]
    return result


@router.post("/ask")
def ask(
    payload: AskRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PermissionCode.ASSISTANT_ASK)),
):
    if not settings.intelligence_assistant_enabled:
        raise HTTPException(status_code=503, detail="O assistente conversacional está desabilitado neste ambiente.")
    try:
        return ask_vendi(db, user, payload.question, payload.start, payload.end)
    except IntelligenceValidationError as exc:
        status_code = 429 if "Muitas consultas" in str(exc) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
