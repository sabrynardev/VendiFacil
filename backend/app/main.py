from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.database.bootstrap import ensure_multitenant_schema
from app.database.session import Base, SessionLocal, engine
from app.seed import seed_database

settings = get_settings()

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    ensure_multitenant_schema(engine)
    if settings.auto_seed:
        with SessionLocal() as db:
            seed_database(db)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(api_router)
