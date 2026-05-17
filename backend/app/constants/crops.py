"""Crop types supported on apply form and market intelligence seeding."""

from __future__ import annotations

import re

SUPPORTED_CROP_TYPES: tuple[str, ...] = (
    "Paddy",
    "Maize",
    "Corn",
    "Tea",
    "Coconut",
    "Vegetables",
    "Fruits",
)

_CROP_SIGNALS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Vegetables", (r"vegetables?", r"காய்கறி", r"එළවළු")),
    ("Fruits", (r"fruits?", r"பழம்", r"පළතුරු")),
    ("Coconut", (r"coconuts?", r"தேங்காய்", r"පොල්")),
    ("Maize", (r"maize", r"மக்காச்சோளம்", r"මයිස්", r"ඉරිඟු")),
    ("Corn", (r"\bcorn\b", r"சோளம்")),
    ("Tea", (r"\btea\b", r"தேயிலை", r"තේ")),
    ("Paddy", (r"\bpaddy\b", r"\brice\b", r"நெல்", r"වී", r"කුඹුරු")),
)


def normalize_crop_type(raw: str) -> str:
    """Map free-text / dialect crop names to a supported apply-form value."""
    trimmed = raw.strip()
    if not trimmed:
        return SUPPORTED_CROP_TYPES[0]

    for supported in SUPPORTED_CROP_TYPES:
        if supported.lower() == trimmed.lower():
            return supported

    for label, patterns in _CROP_SIGNALS:
        if any(re.search(pattern, trimmed, re.IGNORECASE) for pattern in patterns):
            return label

    return SUPPORTED_CROP_TYPES[0]
