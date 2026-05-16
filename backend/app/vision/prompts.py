"""Crop- and region-specific vision prompts for Sri Lankan smallholder underwriting."""

from __future__ import annotations

from app.vision.image_signals import ImageSignals

# Sri Lanka–relevant pathology and field cues (DA/RRDI extension priorities).
_CROP_RUBRICS: dict[str, str] = {
    "Paddy": (
        "Paddy: bunded plots or level fields, tillers, panicles when mature. "
        "Check blast (neck/node lesions), bacterial leaf blight (water-soaked stripes), "
        "brown planthopper stress (hopper burn, sooty mold), nutrient chlorosis (N/K), lodging."
    ),
    "Maize": (
        "Maize/Corn: row spacing, broad leaves, tassels when mature. "
        "Check fall armyworm feeding, rust, leaf blight, drought curling, poor stand establishment."
    ),
    "Corn": (
        "Maize/Corn: row spacing, broad leaves, tassels when mature. "
        "Check fall armyworm feeding, rust, leaf blight, drought curling, poor stand establishment."
    ),
    "Tea": (
        "Tea: contour hedgerows on slopes, plucking table, dark green flush. "
        "Check blister blight, red spider mite bronzing, dieback, uneven pruning, erosion exposure."
    ),
    "Coconut": (
        "Coconut: palm crowns, fronds, spacing. "
        "Check yellowing fronds (nutrient/wilt), beetle/borer damage, drought browning, young palm gaps."
    ),
    "Vegetables": (
        "Vegetables: beds, mulch, drip lines, mixed cultivars. "
        "Check leaf spots, caterpillar defoliation, downy mildew, wilting, poor stand, soil exposure."
    ),
    "Fruits": (
        "Fruit crops: trees/vines (mango, banana, papaya, citrus, passion fruit). "
        "Check anthracnose, fruit fly damage, leaf curl, nutrient chlorosis, canopy gaps, weed competition."
    ),
}


def build_vision_system_prompt() -> str:
    return """You are VisionAgronomistAgent — an expert agronomic computer-vision underwriter for
smallholder farms in Sri Lanka. You MUST follow this evaluation order:

1) IMAGE VALIDITY: Is this a readable outdoor agricultural field/plantation photo (not selfie,
   receipt, indoor, or unrelated)? If not, set image_quality_score below 30 and health_score to 0.

2) CROP MATCH: Does visible vegetation match the declared crop_type? Score crop_match_confidence 0–1.

3) CANOPY & VIGOR: Estimate canopy_cover_percent (0–100). chlorophyll_index and vegetation vigor 0–1.

4) STRESS & DISEASE: List specific issues in detected_issues (e.g. "leaf_blight", "chlorosis",
   "pest_defoliation", "drought_stress", "lodging"). Set disease_detected true if actionable pathology.

5) ACREAGE: Estimate cultivated acreage from visible boundaries vs farmer declaration.
   acreage_confidence 0–1 (low if partial field, oblique angle, or no boundary cues).

6) health_score 0–100: holistic underwriting score (typical healthy field: 55–92).

Return ONLY valid JSON with exactly these keys (no extra keys):
- estimated_acreage (positive number)
- chlorophyll_index (0.0 to 1.0)
- disease_detected (boolean)
- health_score (0 to 100)
- image_quality_score (0 to 100)
- crop_match_confidence (0.0 to 1.0)
- canopy_cover_percent (0 to 100)
- detected_issues (array of short snake_case strings, empty if none)
- growth_stage (one of: seedling, vegetative, flowering, maturity, harvest, mixed, unknown)
- acreage_confidence (0.0 to 1.0)
- vegetation_index (0.0 to 1.0, estimated green biomass from imagery)"""


def build_vision_user_prompt(
    *,
    crop_type: str,
    district: str | None,
    declared_acreage: float,
    signals: ImageSignals,
) -> str:
    rubric = _CROP_RUBRICS.get(crop_type, _CROP_RUBRICS["Vegetables"])
    region = district or "Sri Lanka"
    return (
        f"Declared crop: {crop_type}. Farmer district: {region}. "
        f"Declared acreage: {declared_acreage:.2f} acres.\n\n"
        f"Crop-specific checklist:\n{rubric}\n\n"
        "Automated RGB pre-analysis (use as a prior, reconcile with what you see):\n"
        f"- computed_vegetation_index: {signals.vegetation_index:.3f}\n"
        f"- computed_green_ratio: {signals.green_ratio:.3f}\n"
        f"- computed_image_quality_score: {signals.image_quality_score:.1f}\n"
        f"- computed_sharpness: {signals.sharpness:.3f}\n"
        f"- likely_agricultural_field: {signals.is_likely_field}\n"
        f"- image_dimensions: {signals.width}x{signals.height}\n\n"
        "If computed signals conflict with visible evidence, trust the photograph. "
        "Return JSON only."
    )
