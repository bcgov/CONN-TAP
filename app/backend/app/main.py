"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.config import settings
from app.db.session import engine
from app.models import auth, dataset, user  # noqa: F401
from app.models.dataset import Dataset


@asynccontextmanager
async def lifespan(_: FastAPI):
    # App auth tables are managed by Alembic (schema `app`). Datasets registry stays in public for now.
    Dataset.__table__.create(bind=engine, checkfirst=True)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
