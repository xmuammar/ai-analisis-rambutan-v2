from dataclasses import dataclass

from app.ai.advanced import analyze_field_state
from app.ai.confidence import combine_confidences
from app.ai.features import build_features
from app.ai.providers import AIProviderRouter
from app.ai.rules import evaluate_condition
from app.ai.types import AnalysisResult, InspectionInputs


@dataclass(frozen=True)
class InspectionAnalysis:
    result: AnalysisResult
    condition: str
    condition_reasons: tuple[str, ...]
    features: dict
    advanced: dict


def analyze_inspection(
    inputs: InspectionInputs,
    *,
    observation_datetime,
    planting_date=None,
) -> InspectionAnalysis:
    features = build_features(
        observation_datetime=observation_datetime,
        planting_date=planting_date,
        raw_inputs=inputs.as_features(),
    )
    predictions = AIProviderRouter().analyze(inputs)
    confidence = combine_confidences(
        [prediction.confidence for prediction in predictions]
    )
    result_status = "READY" if predictions else "INSUFFICIENT_DATA"
    result = AnalysisResult(
        predictions=predictions,
        status=result_status,
        summary=(
            f"{len(predictions)} prediksi berbasis bukti tersedia; "
            f"confidence gabungan {confidence:.2f}."
            if predictions
            else "Model belum siap atau data belum cukup."
        ),
    )
    condition, reasons = evaluate_condition(inputs)
    advanced = analyze_field_state(inputs.as_features())
    return InspectionAnalysis(
        result=result,
        condition=condition,
        condition_reasons=tuple(item.text for item in reasons),
        features=features,
        advanced=advanced.as_dict(),
    )
