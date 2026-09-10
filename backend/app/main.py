import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.router import api_router
from app.core.config import get_settings
from app.database.bootstrap import ensure_multitenant_schema
from app.database.session import Base, SessionLocal, engine
from app.seed import seed_database
from app.services.profiles import backfill_account_profiles

settings = get_settings()
logger = logging.getLogger("vendi.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_multitenant_schema(engine)
    with SessionLocal() as db:
        backfill_account_profiles(db)
    if settings.auto_seed:
        with SessionLocal() as db:
            seed_database(db)
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_and_correlation_headers(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
    request.state.correlation_id = correlation_id
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled API error correlation_id=%s path=%s", correlation_id, request.url.path)
        response = JSONResponse(status_code=500, content={"detail": "Não foi possível concluir a operação.", "correlation_id": correlation_id})
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "degraded", "database": "unavailable"})


app.include_router(api_router)
