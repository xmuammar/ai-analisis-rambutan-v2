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
    architecture = assessment["architecture_parameters"]
    assert len(architecture) == 16
    assert architecture[0]["parameter"] == "Batang utama"
    assert architecture[0]["value"] == "Masih dominan dan mudah dikenali"
    soil = assessment["soil_parameters"]
    assert len(soil) == 23
    assert soil[0]["parameter"] == "Permukaan tanah"
    assert soil[0]["interpretation"] == "Terlihat jelas di permukaan"
    assert any(
        item["parameter"] == "pH"
        and item["evidence_status"] == "REQUIRES_MEASUREMENT"
        and item["confidence"] is None
        for item in soil
    )
    weeds = assessment["weed_parameters"]
    assert len(weeds) == 8
    assert weeds[0]["parameter"] == "Gulma radius dekat pangkal"
    assert weeds[-1]["value"] == "Pemeliharaan rutin"
    microclimate = assessment["microclimate_parameters"]
    assert len(microclimate) == 11
    assert microclimate[0]["parameter"] == "Intensitas cahaya saat foto"
    assert microclimate[0]["value"] == "Tinggi"
    assert any(
        item["parameter"] == "Suhu udara"
        and item["evidence_status"] == "REQUIRES_MEASUREMENT"
        and item["confidence"] is None
        for item in microclimate
    )
    screening = assessment["pest_disease_screening"]
    assert len(screening["symptoms"]) == 14
    assert screening["pest_screening"] == "Tidak ditemukan indikasi kuat"
    assert screening["disease_screening"] == "Tidak ditemukan gejala berat"
    assert screening["diagnosis"] is None
    assert screening["confirmation_required"] is True
