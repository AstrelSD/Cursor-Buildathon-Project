from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class VisionAnalysisResult(BaseModel):
    estimated_acreage: float = Field(gt=0)
    chlorophyll_index: float = Field(ge=0, le=1)
    disease_detected: bool
    health_score: float = Field(ge=0, le=100)
    image_quality_score: float = Field(default=75.0, ge=0, le=100)
    crop_match_confidence: float = Field(default=0.75, ge=0, le=1)
    canopy_cover_percent: float = Field(default=50.0, ge=0, le=100)
    detected_issues: list[str] = Field(default_factory=list)
    growth_stage: str = Field(default="unknown")
    acreage_confidence: float = Field(default=0.65, ge=0, le=1)
    vegetation_index: float = Field(default=0.5, ge=0, le=1)


class MarketIntelligenceResult(BaseModel):
    market_volatility_coefficient: float = Field(ge=0, le=1)
    weather_risk_score: float = Field(ge=0)


class UnderwriterDecision(BaseModel):
    calculated_risk_score: float = Field(ge=0, le=100)
    approved: bool
    rejection_reason: Optional[str] = None
    transaction_reference: Optional[str] = None
    decision_logs: list[str] = Field(default_factory=list)


class LoanRecord(BaseModel):
    id: UUID
    user_id: UUID
    crop_type: str
    declared_acreage: float
    requested_amount: float
    status: str
    multimodal_evidence_url: Optional[str] = None
    district: Optional[str] = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> LoanRecord:
        profile = row.get("profiles") or {}
        district = profile.get("district") if isinstance(profile, dict) else None
        return cls(
            id=UUID(str(row["id"])),
            user_id=UUID(str(row["user_id"])),
            crop_type=row["crop_type"],
            declared_acreage=float(row["declared_acreage"]),
            requested_amount=float(row["requested_amount"]),
            status=row["status"],
            multimodal_evidence_url=row.get("multimodal_evidence_url"),
            district=district,
        )
