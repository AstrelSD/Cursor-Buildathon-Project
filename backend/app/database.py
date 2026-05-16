from __future__ import annotations

import asyncio
from threading import Lock
from typing import Optional

from supabase import AsyncClient, acreate_client

from app.config import settings

_client: Optional[AsyncClient] = None
_async_init_lock = asyncio.Lock()
_thread_guard = Lock()


async def init_supabase() -> AsyncClient:
    """Initialize the long-lived Supabase async client (idempotent)."""
    global _client

    if not settings.supabase_configured:
        raise RuntimeError(
            "Supabase is not configured. Set SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY in backend/.env"
        )

    async with _async_init_lock:
        if _client is not None:
            return _client

        client = await acreate_client(
            str(settings.SUPABASE_URL),
            settings.SUPABASE_SERVICE_ROLE_KEY.get_secret_value(),  # type: ignore[union-attr]
        )

        with _thread_guard:
            _client = client

        return client


async def close_supabase() -> None:
    """Tear down the Supabase client and release underlying HTTP resources."""
    global _client

    async with _async_init_lock:
        with _thread_guard:
            client = _client
            _client = None

        if client is None:
            return

        postgrest = getattr(client, "postgrest", None)
        session = getattr(postgrest, "session", None) if postgrest else None
        if session is not None and hasattr(session, "aclose"):
            await session.aclose()


def get_supabase() -> AsyncClient:
    """Return the initialized Supabase client (thread-safe read)."""
    with _thread_guard:
        if _client is None:
            raise RuntimeError(
                "Supabase client is not initialized. "
                "Ensure application lifespan startup has completed."
            )
        return _client