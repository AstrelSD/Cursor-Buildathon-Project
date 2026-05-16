import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import SupabaseException

from app.config import settings
from app.database import close_supabase, get_supabase, init_supabase
from app.routers.loan import router as loan_router

logger = logging.getLogger(__name__)

CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.supabase = None
    app.state.supabase_error = None
    if settings.supabase_configured:
        try:
            await init_supabase()
            app.state.supabase = get_supabase()
        except SupabaseException as exc:
            app.state.supabase_error = str(exc)
            logger.error("Supabase startup failed: %s", exc)
    yield
    if app.state.supabase is not None:
        await close_supabase()


app = FastAPI(
    title="Agri-Lend API",
    description="Multi-agent agronomic credit underwriting engine",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(loan_router, prefix="/api")


@app.get("/health")
async def health_check() -> dict[str, object]:
    """Base performance dashboard checkpoint for load balancers and monitors."""
    supabase_ready = getattr(app.state, "supabase", None) is not None
    integrations = {
        "openai": settings.openai_configured,
        "google_genai": settings.google_genai_configured,
        "supabase": supabase_ready,
    }
    payload: dict[str, object] = {
        "status": "healthy",
        "service": "agri-lend-backend",
        "integrations": integrations,
    }
    supabase_error = getattr(app.state, "supabase_error", None)
    if supabase_error:
        payload["supabase_error"] = supabase_error
    return payload
