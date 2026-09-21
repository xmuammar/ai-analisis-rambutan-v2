from app.ai.problem_solver import solve_visual_problems


def test_problem_solver_covers_specification_domains():
    result = solve_visual_problems(
        {
            "visual_features": {
                "status": "READY",
                "color_class": "DOMINAN_HIJAU",
                "green_dominance": 20,
                "confidence": 0.65,
            },
            "object_detection": {"status": "READY", "detections": []},
            "segmentation": {"status": "READY"},
        }
    )
    assert result["status"] == "READY"
    assert result["algorithm_count"] >= 8
    assert result["components"]["leaf_health"]["value"]["leaf_wilt"] is False
    assert (
        result["components"]["virtual_soil"]["value"]["root_zone_moisture_class"]
        == "MOIST"
    )
    assert (
        result["components"]["pest_disease_weed"]["value"]["pest_category"] == "UNKNOWN"
    )


def test_problem_solver_does_not_fake_historical_anomalies():
    result = solve_visual_problems({"visual_features": {"status": "READY"}}, [])
    assert result["components"]["historical_anomaly"]["status"] == "INSUFFICIENT_DATA"
