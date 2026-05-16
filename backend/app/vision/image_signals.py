"""Lightweight RGB vegetation and image-quality signals (no ML model weights).

Uses Excess Green Index (ExG) — standard for ground/drone RGB crop monitoring:
  ExG = 2·G' − R' − B'  where R',G',B' are normalized per-pixel reflectance.
References: Woebbecke et al. (1995); common in digital ag RGB pipelines (UCD, AgPipeline).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageFilter, ImageStat

logger = logging.getLogger(__name__)

MAX_VISION_EDGE = 1536
_SAMPLE_STRIDE = 4


@dataclass(frozen=True)
class ImageSignals:
    vegetation_index: float  # 0–1, from mean ExG
    green_ratio: float  # 0–1
    brightness: float  # 0–1 mean luminance
    sharpness: float  # 0–1 edge-energy proxy
    image_quality_score: float  # 0–100 composite
    width: int
    height: int
    is_likely_field: bool


def prepare_image_for_vision(image_bytes: bytes, mime_type: str) -> tuple[bytes, str]:
    """Downscale large photos for consistent Gemini input and faster EXG sampling."""
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            img = img.convert("RGB")
            w, h = img.size
            longest = max(w, h)
            if longest > MAX_VISION_EDGE:
                scale = MAX_VISION_EDGE / longest
                img = img.resize(
                    (int(w * scale), int(h * scale)),
                    Image.Resampling.LANCZOS,
                )
            out = BytesIO()
            fmt = "JPEG" if mime_type == "image/jpeg" else "PNG"
            save_mime = "image/jpeg" if fmt == "JPEG" else "image/png"
            img.save(out, format=fmt, quality=88 if fmt == "JPEG" else None)
            return out.getvalue(), save_mime
    except Exception:
        logger.warning("Image prepare failed; using original bytes")
        return image_bytes, mime_type


def analyze_image_bytes(image_bytes: bytes) -> ImageSignals:
    with Image.open(BytesIO(image_bytes)) as img:
        rgb = img.convert("RGB")
        w, h = rgb.size

        exg_sum = 0.0
        green_sum = 0.0
        count = 0
        pixels = rgb.load()
        for y in range(0, h, _SAMPLE_STRIDE):
            for x in range(0, w, _SAMPLE_STRIDE):
                r, g, b = pixels[x, y]
                total = r + g + b + 1e-6
                rn, gn, bn = r / total, g / total, b / total
                exg_sum += 2.0 * gn - rn - bn
                green_sum += gn
                count += 1

        mean_exg = exg_sum / max(count, 1)
        vegetation_index = _clamp01((mean_exg + 1.0) / 2.0)
        green_ratio = green_sum / max(count, 1)

        gray = rgb.convert("L")
        brightness = ImageStat.Stat(gray).mean[0] / 255.0
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_std = ImageStat.Stat(edges).stddev[0]
        sharpness = _clamp01(edge_std / 40.0)

        res_score = _clamp01(min(w, h) / 480.0)
        bright_score = 1.0 - min(abs(brightness - 0.45) / 0.45, 1.0)
        image_quality_score = round(
            100.0 * (0.35 * sharpness + 0.30 * res_score + 0.35 * bright_score),
            1,
        )

        is_likely_field = (
            vegetation_index >= 0.32
            and image_quality_score >= 35.0
            and w >= 200
            and h >= 200
        )

        return ImageSignals(
            vegetation_index=round(vegetation_index, 3),
            green_ratio=round(green_ratio, 3),
            brightness=round(brightness, 3),
            sharpness=round(sharpness, 3),
            image_quality_score=image_quality_score,
            width=w,
            height=h,
            is_likely_field=is_likely_field,
        )


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
