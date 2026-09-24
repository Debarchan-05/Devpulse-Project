from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # No Alembic here on purpose -- create_all() builds any missing
    # tables and the badge catalog is (re)seeded idempotently. See
    # app/db/init_db.py for the reasoning and trade-offs.
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="A MySQL + FastAPI backend that turns a GitHub profile into a "
    "living 'developer pulse' score, growth history, achievements, and "
    "AI-assisted career feedback.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": settings.app_name}


app.include_router(api_router, prefix=settings.api_v1_prefix)
