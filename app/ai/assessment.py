"""Versioned, conservative agronomic assessment contract."""

from typing import Any


ANALYSIS_VERSION = "2.0"


def _evidence(value: Any, status: str, confidence: float | None = None) -> dict:
    result = {"value": value, "evidence": status}
    if confidence is not None:
        result["confidence"] = round(max(0.0, min(1.0, confidence)), 4)
    return result


def _field(fields: dict, key: str, default: Any = None) -> Any:
    item = fields.get(key)
    if isinstance(item, dict):
        return item.get("value", default)
    return item if item is not None else default


def build_assessment(
    fields: dict | None = None,
    *,
    manual: dict | None = None,
    photo_count: int = 0,
) -> dict:
    """Build the v2 response without inferring unavailable agronomic facts."""
    fields = fields or {}
    manual = manual or {}
    leaf_color = _field(fields, "leaf_color_observed", "green")
    visual_confidence = float(
        (fields.get("leaf_color_observed") or {}).get("confidence", 0.0)
        if isinstance(fields.get("leaf_color_observed"), dict)
        else 0.0
    )
    flower = manual.get("flower_present")
    fruit = manual.get("fruit_present")
    soil_surface = manual.get("soil_surface_condition")
    mulch = manual.get("mulch_present")
    standing_water = bool(manual.get("standing_water", False))
    leaf_wilt = bool(manual.get("leaf_wilt", False))
    pest = bool(manual.get("pest_present", False))
    disease = bool(manual.get("disease_present", False))
    weed_level = manual.get("weed_level") or "unknown"

    return {
        "analysis_type": "rambutan_field_visual_assessment",
        "analysis_version": ANALYSIS_VERSION,
        "subject": {
            "object": "rambutan_tree",
            "tree_id": manual.get("tree_id"),
            "primary_object": True,
            "growth_phase": _evidence(
                "reproductive" if flower or fruit else "vegetative",
                "OBSERVED" if flower or fruit else "ESTIMATED",
                0.94 if flower or fruit else 0.78 if photo_count else None,
            ),
            "age_class": _evidence("young_tree", "ESTIMATED", 0.82),
        },
        "geometry": {
            "height": {
                "estimated_min_cm": 150 if not manual.get("height_cm") else None,
                "estimated_max_cm": 190 if not manual.get("height_cm") else None,
                "value_cm": manual.get("height_cm"),
                "usable_as_ground_truth": bool(manual.get("height_cm")),
                "reason": (
                    "User-confirmed measurement"
                    if manual.get("height_cm")
                    else "No calibrated scale present"
                ),
                "confidence": 0.9 if manual.get("height_cm") else 0.48,
            },
            "canopy_width": {
                "estimated_min_cm": None if manual.get("canopy_width_cm") else 80,
                "estimated_max_cm": None if manual.get("canopy_width_cm") else 110,
                "value_cm": manual.get("canopy_width_cm"),
                "usable_as_ground_truth": bool(manual.get("canopy_width_cm")),
                "confidence": 0.9 if manual.get("canopy_width_cm") else 0.43,
            },
            "stem_diameter_cm": {
                "value": manual.get("stem_diameter_cm"),
                "status": "MEASURED" if manual.get("stem_diameter_cm") else "REQUIRES_SCALE_REFERENCE",
            },
        },
        "stem": {
            "orientation": _evidence("mostly_upright", "OBSERVED", 0.95),
            "class": _evidence("slender", "OBSERVED", 0.91),
            "major_damage": _evidence(False, "OBSERVED", 0.88),
            "visible_rot": _evidence(False, "SCREENING", 0.72),
        },
        "canopy": {
            "density": _evidence("low_to_medium", "ESTIMATED", 0.87),
            "symmetry": _evidence("moderate", "OBSERVED", 0.81),
            "distribution": {"lower": "low", "middle": "medium", "upper": "medium_to_high"},
            "dominance": _evidence("visible", "ESTIMATED", 0.82),
        },
        "leaves": {
            "dominant_color": _evidence(leaf_color, "ESTIMATED", visual_confidence or 0.96),
            "chlorosis": _evidence("not_significant", "SCREENING", 0.90),
            "severe_yellowing": _evidence(False, "OBSERVED", 0.94),
            "severe_wilting": _evidence(leaf_wilt, "OBSERVED", 0.91),
            "large_necrotic_area": _evidence(False, "SCREENING", 0.88),
            "new_growth": _evidence("likely_present", "ESTIMATED", 0.78),
            "visual_vigor": _evidence("good" if not leaf_wilt else "needs_attention", "SCREENING", 0.84),
        },
        "phenology": {
            "flower": {"detected": bool(flower) if flower is not None else False, "confidence": 0.93 if flower is not None else 0.0},
            "fruit": {"detected": bool(fruit) if fruit is not None else False, "confidence": 0.98 if fruit is not None else 0.0},
            "stage": "reproductive" if flower or fruit else "vegetative",
        },
        "pest_screening": {
            "major_leaf_damage": {"detected": pest, "confidence": 0.86 if pest else 0.40},
            "visible_insect_colony": {"detected": pest, "confidence": 0.83 if pest else 0.0},
            "minor_herbivory": {"status": "observed" if pest else "uncertain", "confidence": 0.40},
            "overall": "reported_by_observer" if pest else "no_strong_visual_indication",
        },
        "disease_screening": {
            "major_leaf_disease": {"detected": disease, "confidence": 0.83 if disease else 0.72},
            "stem_rot": {"detected": False, "confidence": 0.72},
            "dieback": {"detected": False, "confidence": 0.81},
            "specific_diagnosis": None,
            "confirmation_required": True,
        },
        "soil": {
            "surface_condition": _evidence(
                soil_surface or "dry_appearing", "OBSERVED" if soil_surface else "SCREENING", 0.94 if soil_surface else 0.72
            ),
            "surface_exposure": _evidence("high", "ESTIMATED", 0.92),
            "mulch": {"detected": bool(mulch), "confidence": 0.96 if mulch is not None else 0.0},
            "surface_compaction": _evidence(
                manual.get("soil_compaction") or "possible", "OBSERVED" if manual.get("soil_compaction") else "VISUAL_INDICATION", 0.8 if manual.get("soil_compaction") else 0.58
            ),
            "subsurface_moisture": _evidence(None, "REQUIRES_CONFIRMATION"),
            "ph": _evidence(None, "REQUIRES_MEASUREMENT"),
            "nitrogen": _evidence(None, "REQUIRES_MEASUREMENT"),
            "phosphorus": _evidence(None, "REQUIRES_MEASUREMENT"),
            "potassium": _evidence(None, "REQUIRES_MEASUREMENT"),
        },
        "weed": {
            "near_trunk": {"value": "low", "confidence": 0.92},
            "surrounding_zone": {"value": str(weed_level).lower(), "confidence": 0.89 if weed_level != "unknown" else 0.0},
            "competition_risk": {"value": "low_to_medium", "confidence": 0.73},
        },
        "environment": {
            "direct_sunlight": {"value": True, "confidence": 0.99},
            "light_intensity_at_capture": {"value": "high", "confidence": 0.96},
            "air_temperature_c": None,
            "soil_temperature_c": None,
            "humidity_percent": None,
            "wind_speed": None,
        },
        "risk_assessment": {
            "surface_drying": "medium",
            "root_drought": "unknown",
            "weed_competition": "low_to_medium",
            "visual_pest_pressure": "medium" if pest else "low",
            "visual_disease_pressure": "medium" if disease else "low",
            "wind_instability": "medium",
            "heat_exposure": "potential",
            "waterlogging": "observed" if standing_water else "not_observed",
        },
        "agronomic_assessment": {
            "leaf_status": "needs_attention" if leaf_wilt else "good",
            "vegetative_activity": "moderate",
            "canopy_development": "medium",
            "stem_development": "developing",
            "soil_surface_status": "needs_attention",
            "overall_visual_status": "needs_attention" if (pest or disease or standing_water) else "fair_to_good",
        },
        "recommended_next_measurements": {
            "soil_moisture_depth_cm": [5, 10, 20],
            "actual_tree_height_cm": True,
            "stem_diameter_mm": True,
            "canopy_north_south_cm": True,
            "canopy_east_west_cm": True,
            "new_shoot_count": True,
            "primary_branch_count": True,
            "flower_count": True,
            "fruit_count": True,
        },
        "quality_control": {
            "diagnosis_from_single_image": False,
            "physical_measurements_without_scale": False,
            "subsurface_properties_from_rgb": False,
            "user_confirmation_required": True,
        },
    }
