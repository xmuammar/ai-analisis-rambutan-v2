from app.ai.vision import aggregate_inspection_fields


def test_aggregation_maps_supported_fields_and_blocks_unsupported_diagnosis():
    result = aggregate_inspection_fields(
        {
            "visual_features": {
                "status": "READY",
                "model": "visual-feature-extractor",
                "color_class": "DOMINAN_HIJAU",
                "brightness_mean": 120.0,
                "sharpness_proxy": 10.0,
                "confidence": 0.65,
            },
            "object_detection": {
                "status": "READY",
                "model": "yolo11n",
                "detections": [{"label": "person", "confidence": 0.8}],
            },
            "classification": {
                "status": "READY",
                "model": "mobilenet_v3_large",
                "class_label": "greenhouse",
                "confidence": 0.7,
            },
            "embedding": {"status": "READY", "model": "embedding", "dimensions": 960},
            "segmentation": {
                "status": "READY",
                "model": "deeplab",
                "class_distribution": {"15": 0.5},
            },
        }
    )
    assert result["ready_model_count"] == 5
    assert result["fields"]["leaf_color_observed"]["value"] == "DOMINAN_HIJAU"
    assert result["fields"]["surface_dark"]["value"] is False
    assert result["fields"]["surface_dark"]["status"] == "ESTIMATED"
    assert (
        result["fields"]["soil_moisture_visual"]["source"]
        == "SOIL_LEAF_VISUAL_ENSEMBLE"
    )
    assert result["fields"]["notes"]["status"] == "DERIVED"
    assert result["fields"]["notes"]["source"] == "HYBRID_VISION_XAI"
    assert "Fitur visual mengukur" in result["fields"]["notes"]["value"]
    assert "Klasifikasi deep learning umum" in result["fields"]["notes"]["value"]
    assert result["fields"]["pest_present"]["source"] == "HYBRID_AGRICULTURE_SCREENING"
    assert (
        result["fields"]["weed_coverage_percent"]["source"]
        == "HYBRID_AGRICULTURE_SCREENING"
    )
    assert (
        result["fields"]["flower_present"]["source"] == "HYBRID_FLOWER_FRUIT_SCREENING"
    )
    assert (
        result["fields"]["fruit_count_estimate"]["source"]
        == "HYBRID_FLOWER_FRUIT_SCREENING"
    )
    assert result["fields"]["surface_dark"]["source"] == "SOIL_LEAF_VISUAL_ENSEMBLE"
    for field_name in (
        "standing_water",
        "leaf_wilt",
        "soil_moisture_visual",
        "height_cm",
        "stem_diameter_cm",
        "canopy_width_cm",
        "flower_present",
        "flower_stage",
        "fruit_present",
        "fruit_stage",
        "fruit_count_estimate",
        "fruit_damage_percent",
        "pest_present",
        "pest_type",
        "disease_present",
        "disease_type",
        "weed_level",
        "weed_coverage_percent",
    ):
        assert field_name in result["fields"]
    assert (
        result["fields"]["root_zone_moisture_class"]["status"] == "NEEDS_CONFIRMATION"
    )
    assert result["fields"]["pest_or_disease"]["status"] == "NEEDS_CONFIRMATION"
    assert result["fields"]["pest_or_disease"]["source"] == "VISUAL_ANOMALY_SCREENING"


def test_flower_fruit_ensemble_autofills_supported_fields():
    result = aggregate_inspection_fields(
        {
            "visual_features": {
                "status": "READY",
                "color_class": "DOMINAN_COKELAT_MERAH",
                "red_mean": 150,
                "green_mean": 100,
                "brightness_mean": 130,
                "sharpness_proxy": 10,
                "confidence": 0.65,
            },
            "object_detection": {
                "status": "READY",
                "model": "yolo11n",
                "detections": [
                    {"label": "flower", "confidence": 0.8},
                    {"label": "fruit", "confidence": 0.85},
                    {"label": "fruit", "confidence": 0.75},
                ],
            },
            "segmentation": {"status": "READY", "class_distribution": {}},
        }
    )
    fields = result["fields"]
    assert fields["flower_present"]["value"] is True
    assert fields["flower_stage"]["value"] == "FLOWERING"
    assert fields["fruit_present"]["value"] is True
    assert fields["fruit_stage"]["value"] == "RIPE"
    assert fields["fruit_count_estimate"]["value"] == 2
    assert fields["fruit_damage_percent"]["value"] == 0
    assert fields["fruit_stage"]["status"] == "ESTIMATED"
