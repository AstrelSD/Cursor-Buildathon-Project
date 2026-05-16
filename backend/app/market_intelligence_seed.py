"""Build market_intelligence seed rows for every crop × district pair."""

from __future__ import annotations

from app.constants.crops import SUPPORTED_CROP_TYPES
from app.constants.districts import SRI_LANKA_DISTRICTS

# Tuned reference rows (used when present; otherwise heuristics apply).
_MANUAL_OVERRIDES: dict[tuple[str, str], dict[str, float | str]] = {
    ("Paddy", "Anuradhapura"): {
        "base_yield_index": 82.50,
        "market_volatility_coefficient": 0.35,
        "weather_risk_score": 12.50,
    },
    ("Paddy", "Polonnaruwa"): {
        "base_yield_index": 80.10,
        "market_volatility_coefficient": 0.42,
        "weather_risk_score": 15.20,
    },
    ("Paddy", "Ampara"): {
        "base_yield_index": 78.40,
        "market_volatility_coefficient": 0.38,
        "weather_risk_score": 18.00,
    },
    ("Paddy", "Kurunegala"): {
        "base_yield_index": 81.20,
        "market_volatility_coefficient": 0.31,
        "weather_risk_score": 11.80,
    },
    ("Paddy", "Nuwaraliya"): {
        "base_yield_index": 76.90,
        "market_volatility_coefficient": 0.48,
        "weather_risk_score": 22.40,
    },
    ("Tea", "Nuwaraliya"): {
        "base_yield_index": 88.00,
        "market_volatility_coefficient": 0.29,
        "weather_risk_score": 9.50,
    },
    ("Tea", "Nuwara Eliya"): {
        "base_yield_index": 88.00,
        "market_volatility_coefficient": 0.29,
        "weather_risk_score": 9.50,
    },
    ("Tea", "Kurunegala"): {
        "base_yield_index": 74.50,
        "market_volatility_coefficient": 0.33,
        "weather_risk_score": 14.10,
    },
    ("Maize", "Ampara"): {
        "base_yield_index": 79.30,
        "market_volatility_coefficient": 0.40,
        "weather_risk_score": 16.70,
    },
}

_CROP_BASE: dict[str, dict[str, float]] = {
    "Paddy": {"yield": 79.5, "volatility": 0.38, "weather": 15.0},
    "Maize": {"yield": 78.0, "volatility": 0.40, "weather": 16.0},
    "Corn": {"yield": 78.5, "volatility": 0.39, "weather": 15.5},
    "Tea": {"yield": 82.0, "volatility": 0.32, "weather": 11.0},
    "Coconut": {"yield": 77.0, "volatility": 0.34, "weather": 13.0},
    "Vegetables": {"yield": 76.0, "volatility": 0.44, "weather": 14.0},
    "Fruits": {"yield": 75.5, "volatility": 0.46, "weather": 13.5},
}

_HILL_DISTRICTS = frozenset(
    {"Nuwara Eliya", "Nuwaraliya", "Badulla", "Kandy", "Matale", "Kegalle", "Ratnapura"}
)
_DRY_ZONE_DISTRICTS = frozenset(
    {
        "Anuradhapura",
        "Polonnaruwa",
        "Ampara",
        "Kurunegala",
        "Puttalam",
        "Mannar",
        "Vavuniya",
        "Kilinochchi",
        "Mullaitivu",
        "Trincomalee",
    }
)
_COASTAL_DISTRICTS = frozenset(
    {"Galle", "Matara", "Hambantota", "Colombo", "Gampaha", "Kalutara", "Jaffna", "Batticaloa"}
)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _jitter(key: str, span: float) -> float:
    return ((hash(key) % 1000) / 1000.0 - 0.5) * span


def _metrics_for(crop_type: str, district: str) -> dict[str, float | str]:
    manual = _MANUAL_OVERRIDES.get((crop_type, district))
    if manual is not None:
        return {"crop_type": crop_type, "district": district, **manual}

    base = _CROP_BASE[crop_type]
    key = f"{crop_type}:{district}"
    yield_index = base["yield"] + _jitter(key, 7.0)
    volatility = base["volatility"] + _jitter(f"{key}:v", 0.10)
    weather = base["weather"] + _jitter(f"{key}:w", 5.0)

    if crop_type == "Tea" and district in _HILL_DISTRICTS:
        yield_index += 4.0
        weather -= 2.5
        volatility -= 0.04
    elif crop_type == "Paddy" and district in _DRY_ZONE_DISTRICTS:
        weather += 2.0
    elif crop_type in ("Maize", "Corn") and district in _DRY_ZONE_DISTRICTS:
        weather += 1.5
    elif crop_type == "Coconut" and district in _COASTAL_DISTRICTS:
        yield_index += 2.5
        weather -= 1.0
    elif crop_type == "Fruits" and district in _HILL_DISTRICTS:
        yield_index += 2.5
        volatility -= 0.03
    elif crop_type in ("Vegetables", "Fruits") and district in _COASTAL_DISTRICTS:
        yield_index += 1.5

    return {
        "crop_type": crop_type,
        "district": district,
        "base_yield_index": round(_clamp(yield_index, 70.0, 92.0), 2),
        "market_volatility_coefficient": round(_clamp(volatility, 0.22, 0.52), 2),
        "weather_risk_score": round(_clamp(weather, 8.0, 28.0), 2),
    }


def build_seed_rows() -> list[dict[str, float | str]]:
    districts = sorted(SRI_LANKA_DISTRICTS)
    rows: list[dict[str, float | str]] = []
    for crop in SUPPORTED_CROP_TYPES:
        for district in districts:
            rows.append(_metrics_for(crop, district))
    return rows
