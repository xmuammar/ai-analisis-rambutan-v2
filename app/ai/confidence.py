def confidence_label(value: float) -> str:
    bounded = max(0.0, min(1.0, value))
    if bounded >= 0.75:
        return "Tinggi"
    if bounded >= 0.45:
        return "Sedang"
    return "Rendah"


def combine_confidences(values: list[float]) -> float:
    if not values:
        return 0.0
    return max(0.0, min(1.0, sum(values) / len(values)))
