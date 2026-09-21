from app.ai.assessment import build_assessment


def test_v2_contains_all_granular_visual_parameters():
    assessment = build_assessment(photo_count=1)
    parameters = assessment["extracted_parameters"]

    assert len(parameters) == 40
    assert parameters[0] == {
        "key": "object",
        "parameter": "Objek",
        "value": "Pohon rambutan muda",
        "evidence_status": "CONTEXT_VISUAL",
        "confidence": 0.9,
    }
    assert any(
        item["parameter"] == "Diameter batang"
        and item["evidence_status"] == "REQUIRES_SCALE"
        and item["confidence"] is None
        for item in parameters
    )
    assert assessment["quality_control"]["diagnosis_from_single_image"] is False
