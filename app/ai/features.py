from datetime import date, datetime
from typing import Any

FEATURE_VERSION = "baseline-1"


def build_features(
    *,
    observation_datetime: datetime,
    planting_date: date | None = None,
    raw_inputs: dict[str, Any],
) -> dict[str, Any]:
    features = dict(raw_inputs)
    if planting_date:
        features["days_since_planting"] = max(
            0, (observation_datetime.date() - planting_date).days
        )
    features["feature_version"] = FEATURE_VERSION
    return features
