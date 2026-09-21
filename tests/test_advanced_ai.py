from app.ai.advanced import (
    analyze_field_state,
    classical_model_analysis,
    engineer_features,
)


def test_hybrid_analysis_is_explainable_and_data_safe():
    result = analyze_field_state(
        {"standing_water": True, "leaf_wilt": True, "height_cm": 120},
        [{"height_cm": 100}, {"height_cm": 110}],
    )
    assert result.health_score < 100
    assert result.risk_score > 0
    assert result.recommendation
    assert result.xai["rule_based_health"] == result.health_score
    assert any(item.status == "INSUFFICIENT_DATA" for item in result.components)


def test_feature_engineering_does_not_fake_missing_values():
    features = engineer_features({"height_cm": 120}, [{"height_cm": 100}])
    assert features["height_cm"] == 120
    assert "leaf_damage_percent" not in features


def test_classical_models_require_labels():
    result = classical_model_analysis({"height_cm": 100}, ["SEHAT"])
    assert result.status == "INSUFFICIENT_DATA"
