from datetime import datetime, timezone

from app.ai.confidence import combine_confidences, confidence_label
from app.ai.engine import analyze_inspection
from app.ai.types import InspectionInputs
from app.ai.xai import explain_prediction


def test_virtual_soil_requires_evidence():
    analysis = analyze_inspection(
        InspectionInputs(),
        observation_datetime=datetime.now(timezone.utc),
    )
    prediction = analysis.result.predictions[0]
    assert prediction.value == "INSUFFICIENT_DATA"
    assert prediction.confidence < 0.45
    assert analysis.result.status == "READY"


def test_virtual_soil_exposes_real_evidence():
    analysis = analyze_inspection(
        InspectionInputs(surface_dark=True),
        observation_datetime=datetime.now(timezone.utc),
    )
    prediction = analysis.result.predictions[0]
    assert prediction.value == "MOIST"
    assert "Permukaan tanah terlihat gelap." in explain_prediction(prediction)
    assert prediction.feature_version == "soil-features-1"


def test_confidence_engine_bounds_and_labels():
    assert combine_confidences([0.8, 0.6]) == 0.7
    assert confidence_label(0.8) == "Tinggi"
    assert confidence_label(-1) == "Rendah"
