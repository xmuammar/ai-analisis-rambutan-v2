"""Problem-oriented ML/DL orchestration for field inspection.

General-purpose vision models provide observations and features. Domain
outputs remain estimates or confirmation requests until an agriculture-labeled
model or calibrated measurement is available.
"""

from statistics import mean
from typing import Any


def _component(
    algorithm: str,
    status: str,
    value: Any,
    confidence: float,
    evidence: list[str],
    *,
    source: str = "HYBRID_AI",
) -> dict[str, Any]:
    return {
        "algorithm": algorithm,
        "status": status,
        "value": value,
        "confidence": round(max(0.0, min(1.0, confidence)), 4),
        "evidence": evidence,
        "source": source,
    }


def solve_visual_problems(
    model_results: dict[str, dict[str, Any]],
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Map available model evidence to every problem domain in the specification."""
    history = history or []
    visual = model_results.get("visual_features", {})
    detection = model_results.get("object_detection", {})
    visual_ready = visual.get("status") == "READY"
    detections = detection.get("detections", [])
    labels = [str(item.get("label", "")).lower() for item in detections]
    green = float(visual.get("green_dominance", 0.0) or 0.0)
    brightness = float(visual.get("brightness_mean", 0.0) or 0.0)
    dark = brightness < 100
    leaf_wilt = green < 12 or (green < 20 and brightness < 75)
    moisture_class = "MOIST" if dark else "SLIGHTLY_DRY" if brightness < 145 else "DRY"
    ready_models = sum(
        result.get("status") == "READY" for result in model_results.values()
    )
    evidence_base = [
        f"{ready_models} keluaran model tersedia.",
        "Nilai pertanian khusus tetap memerlukan model berlabel atau konfirmasi.",
    ]
    tree = _component(
        "Scene + Tree Structure Screening",
        "READY" if ready_models else "INSUFFICIENT_DATA",
        {
            "canopy_detected": any(label in {"tree", "plant"} for label in labels),
            "visual_vigor": "NORMAL" if green >= 8 else "UNCERTAIN",
        },
        min(0.65, ready_models / 5),
        evidence_base
        + ["Bentuk tajuk dan tinggi tidak diukur tanpa depth/reference marker."],
    )
    leaf = _component(
        "Leaf Feature + Visual Health Screening",
        "READY" if visual_ready else "INSUFFICIENT_DATA",
        {
            "leaf_color": visual.get("color_class"),
            "leaf_wilt": leaf_wilt if visual_ready else None,
            "leaf_damage_percent": None,
            "visible_pest": None,
            "visible_disease_symptom": None,
        },
        float(visual.get("confidence", 0.0) or 0.0),
        evidence_base
        + ["Layu adalah estimasi ensemble warna/brightness; bukan diagnosis penyakit."],
    )
    shoot = _component(
        "Shoot Detection + Growth Trend",
        "READY" if visual_ready else "INSUFFICIENT_DATA",
        {"new_shoot_present": None, "new_shoot_count_estimate": None},
        float(visual.get("confidence", 0.0) or 0.0),
        evidence_base + ["Tren tunas membutuhkan foto historis atau label tunas."],
    )
    stem = _component(
        "Stem/Branch Detection + Depth Estimation",
        "READY" if visual_ready else "INSUFFICIENT_DATA",
        {
            "stem_visible": any(label in {"trunk", "tree"} for label in labels),
            "physical_damage": None,
            "stem_diameter_estimate": None,
        },
        min(0.5, float(visual.get("confidence", 0.0) or 0.0)),
        evidence_base
        + ["Diameter dan luka memerlukan depth model atau referensi ukuran."],
    )
    flower_fruit = _component(
        "Flower/Fruit Object Detection + Segmentation",
        "READY" if detection.get("status") == "READY" else "INSUFFICIENT_DATA",
        {
            "flower_present": any(label in {"flower", "flowers"} for label in labels),
            "fruit_present": any(
                label in {"fruit", "apple", "orange", "banana"} for label in labels
            ),
            "flower_stage": None,
            "fruit_stage": None,
            "fruit_damage_percent": None,
        },
        max(
            (
                float(item.get("confidence", 0.0))
                for item in detections
                if str(item.get("label", "")).lower()
                in {"flower", "flowers", "fruit", "apple", "orange", "banana"}
            ),
            default=0.0,
        ),
        evidence_base + ["Tahap dan kerusakan memerlukan dataset bunga/buah berlabel."],
    )
    agricultural = _component(
        "Agricultural Pest/Disease/Weed Screening",
        "READY" if ready_models else "INSUFFICIENT_DATA",
        {
            "pest_category": "UNKNOWN",
            "disease_category": "UNKNOWN",
            "weed_level": None,
            "affected_percent": None,
        },
        min(0.2, ready_models / 20),
        evidence_base
        + ["Screening umum aktif; tidak menggantikan diagnosis pertanian khusus."],
    )
    soil = _component(
        "Virtual Soil Sensor Ensemble",
        "READY" if visual_ready else "INSUFFICIENT_DATA",
        {
            "root_zone_moisture_class": moisture_class if visual_ready else None,
            "dryness_risk": "LOW" if dark else "MEDIUM",
            "waterlogging_risk": "LOW",
            "irrigation_need_probability": None,
        },
        min(0.4, float(visual.get("confidence", 0.0) or 0.0)),
        evidence_base
        + [
            (
                "Kelas kelembapan adalah inferensi visual dari brightness/warna; "
                "bukan pembacaan sensor tanah."
            ),
        ],
    )
    historical = _component(
        "Historical Baseline + Anomaly Detection",
        "READY" if len(history) >= 5 else "INSUFFICIENT_DATA",
        {"history_count": len(history), "anomaly": None},
        min(1.0, len(history) / 10),
        [f"{len(history)} data historis tersedia; minimal 5 diperlukan."],
    )
    components = {
        "tree_structure": tree,
        "leaf_health": leaf,
        "shoot_growth": shoot,
        "stem_branch": stem,
        "flower_fruit": flower_fruit,
        "pest_disease_weed": agricultural,
        "virtual_soil": soil,
        "historical_anomaly": historical,
    }
    usable = [
        item["confidence"] for item in components.values() if item["status"] == "READY"
    ]
    return {
        "status": "READY" if usable else "INSUFFICIENT_DATA",
        "algorithm_count": len(components),
        "ready_algorithm_count": sum(
            item["status"] == "READY" for item in components.values()
        ),
        "confidence": round(mean(usable), 4) if usable else 0.0,
        "components": components,
        "policy": "No false precision; unsupported agricultural values require confirmation.",
    }
