from dataclasses import dataclass
from statistics import mean


@dataclass(frozen=True)
class MLResult:
    status: str
    value: float | None
    confidence: float
    reason: str


def moving_average(values: list[float], window: int = 3) -> MLResult:
    if window < 1:
        raise ValueError("window harus lebih besar dari nol")
    if len(values) < window:
        return MLResult("INSUFFICIENT_DATA", None, 0.0, "Data belum cukup untuk tren.")
    return MLResult(
        "READY",
        mean(values[-window:]),
        min(1.0, len(values) / 10),
        "Rata-rata bergerak.",
    )


def detect_deviation(
    value: float, baseline: list[float], tolerance: float = 0.2
) -> MLResult:
    if not baseline:
        return MLResult(
            "INSUFFICIENT_DATA", None, 0.0, "Baseline pohon belum tersedia."
        )
    reference = mean(baseline)
    deviation = abs(value - reference) / max(abs(reference), 1e-9)
    status = "ANOMALY" if deviation > tolerance else "NORMAL"
    return MLResult(
        status, deviation, min(1.0, len(baseline) / 10), f"Baseline={reference:g}."
    )


def weighted_ensemble(values: list[tuple[float, float]]) -> MLResult:
    if not values or any(weight < 0 for _, weight in values):
        return MLResult(
            "INSUFFICIENT_DATA", None, 0.0, "Prediksi ensemble belum tersedia."
        )
    total_weight = sum(weight for _, weight in values)
    if total_weight <= 0:
        return MLResult("INSUFFICIENT_DATA", None, 0.0, "Bobot model tidak valid.")
    result = sum(value * weight for value, weight in values) / total_weight
    agreement = 1 - (
        max(value for value, _ in values) - min(value for value, _ in values)
    )
    return MLResult(
        "READY", result, max(0.0, min(1.0, agreement)), "Weighted ensemble."
    )
