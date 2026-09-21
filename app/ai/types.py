from dataclasses import dataclass, field
from typing import Any, Literal

DataStatus = Literal[
    "OBSERVED",
    "MEASURED",
    "ESTIMATED",
    "INFERRED",
    "PREDICTED",
    "USER_CONFIRMED",
]


@dataclass(frozen=True)
class Evidence:
    text: str
    source: str = "VISUAL_OBSERVATION"


@dataclass(frozen=True)
class Prediction:
    field_key: str
    value: str
    confidence: float
    status: DataStatus
    source: str
    model_version: str
    feature_version: str
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AnalysisResult:
    predictions: tuple[Prediction, ...]
    status: str
    summary: str


@dataclass(frozen=True)
class InspectionInputs:
    surface_dark: bool = False
    standing_water: bool = False
    leaf_wilt: bool = False
    photo_count: int = 0

    def as_features(self) -> dict[str, Any]:
        return {
            "surface_dark": self.surface_dark,
            "standing_water": self.standing_water,
            "leaf_wilt": self.leaf_wilt,
            "photo_count": self.photo_count,
        }
