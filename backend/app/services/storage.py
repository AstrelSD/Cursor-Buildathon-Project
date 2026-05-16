from __future__ import annotations

import mimetypes
from urllib.parse import unquote, urlparse

from app.config import settings


def _parse_storage_path_segment(segment: str, default_bucket: str) -> tuple[str, str]:
    """Parse `bucket/object/path` from a storage URL path segment (no query string)."""
    clean = unquote(segment.split("?", 1)[0].lstrip("/"))
    bucket, _, object_path = clean.partition("/")
    if object_path:
        return bucket, object_path
    return default_bucket, bucket


def resolve_storage_location(evidence_url: str) -> tuple[str, str]:
    """Resolve bucket/object path from a storage path or Supabase Storage URL."""
    default_bucket = settings.SUPABASE_STORAGE_BUCKET
    raw = evidence_url.strip()

    for marker in (
        "/storage/v1/object/public/",
        "/storage/v1/object/sign/",
        "/storage/v1/object/authenticated/",
    ):
        if marker in raw:
            return _parse_storage_path_segment(raw.split(marker, 1)[1], default_bucket)

    if raw.startswith("http://") or raw.startswith("https://"):
        parsed = urlparse(raw)
        path = unquote(parsed.path.lstrip("/"))
        if path.startswith(f"{default_bucket}/"):
            return default_bucket, path[len(default_bucket) + 1 :]
        return default_bucket, path

    normalized = raw.lstrip("/")
    if normalized.startswith(f"{default_bucket}/"):
        return default_bucket, normalized[len(default_bucket) + 1 :]
    return default_bucket, normalized


def guess_mime_type(object_path: str) -> str:
    mime_type, _ = mimetypes.guess_type(object_path)
    return mime_type or "image/jpeg"
