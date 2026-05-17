"""Vercel entrypoint: re-export the FastAPI app from the application package."""

from app.main import app

__all__ = ["app"]
