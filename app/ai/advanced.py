"""Explainable hybrid analysis for small and longitudinal field datasets.

The module deliberately separates rule evidence from statistical/ML evidence.
Classical models and anomaly detection return INSUFFICIENT_DATA until their
minimum sample requirements are met.
"""

from dataclasses import asdict, dataclass
from statistics import mean, pstdev
from typing import Any


@dataclass(frozen=True)
class ComponentResult:
    name: str
    status: str
    value: float | str | None
    confidence: float
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class AdvancedAnalysis:
    status: str
    health_score: float | None
    risk_score: float | None
    trend: str
    confidence: float
    recommendation: str
    components: tuple[ComponentResult, ...]
    xai: dict[str, float]

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["components"] = [asdict(item) for item in self.components]
        return payload


def engineer_features(
    current: dict[str, Any], history: list[dict[str, Any]]
) -> dict[str, float]:
    """Create deterministic, versioned features without mutating raw data."""
    numeric_keys = (
        "height_cm",
        "stem_diameter_cm",
        "canopy_width_cm",
        "new_shoot_count",
        "fruit_count_estimate",
        "leaf_damage_percent",
        "watering_liters",
    )
    features: dict[str, float] = {}
    for key in numeric_keys:
        value = current.get(key)
        if isinstance(value, (int, float)):
            features[key] = float(value)
        values = [
            float(row[key]) for row in history if isinstance(row.get(key), (int, float))
        ]
        if values:
            features[f"{key}_mean"] = mean(values)
            features[f"{key}_change"] = features.get(key, values[-1]) - values[-1]
    features["observation_count"] = float(len(history) + 1)
    features["feature_version"] = 2.0
    return features


def rule_based_health(current: dict[str, Any]) -> ComponentResult:
    score = 100.0
    evidence: list[str] = []
    if current.get("standing_water"):
        score -= 25
        evidence.append("Genangan meningkatkan risiko stres akar.")
    if current.get("leaf_wilt"):
        score -= 20
        evidence.append("Daun layu menurunkan skor kesehatan visual.")
    if current.get("leaf_damage_percent") is not None:
        damage = max(0.0, min(100.0, float(current["leaf_damage_percent"])))
        score -= damage * 0.35
        evidence.append(f"Kerusakan daun tercatat {damage:.1f}%.")
    if not evidence:
        evidence.append("Belum ada faktor risiko rule-based yang terpicu.")
    return ComponentResult(
        "Rule-Based Health", "READY", round(max(score, 0), 2), 0.75, tuple(evidence)
    )


def trend_analysis(
    history: list[dict[str, Any]], key: str = "height_cm"
) -> ComponentResult:
    values = [row.get(key) for row in history]
    values = [float(value) for value in values if isinstance(value, (int, float))]
    if len(values) < 3:
        return ComponentResult(
            "Time-Series Trend",
            "INSUFFICIENT_DATA",
            None,
            0.0,
            ("Minimal 3 pengamatan diperlukan.",),
        )
    slope = (values[-1] - values[0]) / (len(values) - 1)
    label = "MENINGKAT" if slope > 0.01 else "MENURUN" if slope < -0.01 else "STABIL"
    return ComponentResult(
        "Time-Series Trend",
        "READY",
        label,
        min(1.0, len(values) / 10),
        (f"Perubahan rata-rata {slope:.2f} per pengamatan.",),
    )


def anomaly_analysis(
    history: list[dict[str, Any]], key: str = "height_cm"
) -> ComponentResult:
    values = [row.get(key) for row in history]
    values = [float(value) for value in values if isinstance(value, (int, float))]
    if len(values) < 5:
        return ComponentResult(
            "Anomaly Detection",
            "INSUFFICIENT_DATA",
            None,
            0.0,
            ("Minimal 5 data historis diperlukan.",),
        )
    deviation = abs(values[-1] - mean(values[:-1]))
    spread = pstdev(values[:-1])
    anomalous = spread > 0 and deviation > 2 * spread
    return ComponentResult(
        "Anomaly Detection",
        "ANOMALY" if anomalous else "NORMAL",
        round(deviation, 3),
        min(1.0, len(values) / 12),
        (f"Deviasi dari baseline historis {deviation:.2f}.",),
    )


def classical_model_analysis(
    features: dict[str, float], labels: list[str]
) -> ComponentResult:
    """Train a small Random Forest only when labelled samples are sufficient."""
    if len(labels) < 12 or len(set(labels)) < 2:
        return ComponentResult(
            "Random Forest / Gradient Boosting",
            "INSUFFICIENT_DATA",
            None,
            0.0,
            ("Minimal 12 label dan 2 kelas diperlukan.",),
        )
    try:
        from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    except ImportError:
        return ComponentResult(
            "Random Forest / Gradient Boosting",
            "NOT_INSTALLED",
            None,
            0.0,
            ("scikit-learn belum terpasang.",),
        )
    # The training endpoint owns persisted datasets. This smoke path only reports readiness.
    _ = (RandomForestClassifier, GradientBoostingClassifier, features)
    return ComponentResult(
        "Random Forest / Gradient Boosting",
        "READY",
        "ELIGIBLE",
        0.5,
        (
            "Dataset label memenuhi syarat awal; evaluasi temporal diperlukan sebelum aktivasi.",
        ),
    )


def analyze_field_state(
    current: dict[str, Any],
    history: list[dict[str, Any]] | None = None,
    labels: list[str] | None = None,
) -> AdvancedAnalysis:
    history = history or []
    features = engineer_features(current, history)
    rule = rule_based_health(current)
    trend = trend_analysis(history)
    anomaly = anomaly_analysis(history)
    classical = classical_model_analysis(features, labels or [])
    risk = 100.0 - float(rule.value or 0)
    if anomaly.status == "ANOMALY":
        risk = min(100.0, risk + 20)
    usable = [
        item.confidence
        for item in (rule, trend, anomaly, classical)
        if item.status == "READY"
    ]
    confidence = mean(usable) if usable else rule.confidence
    recommendation = (
        "Periksa penyebab perubahan dan lakukan pengamatan ulang."
        if risk >= 40 or anomaly.status == "ANOMALY"
        else "Lanjutkan pemantauan berkala; belum ada risiko tinggi terdeteksi."
    )
    xai = {
        "rule_based_health": round(float(rule.value or 0), 3),
        "risk_penalty": round(risk, 3),
        "trend_evidence": 1.0 if trend.status == "READY" else 0.0,
        "anomaly_evidence": 1.0 if anomaly.status == "ANOMALY" else 0.0,
    }
    return AdvancedAnalysis(
        "READY" if usable else "INSUFFICIENT_DATA",
        round(float(rule.value or 0), 2),
        round(risk, 2),
        str(trend.value or "BELUM CUKUP DATA"),
        round(confidence, 3),
        recommendation,
        (rule, trend, anomaly, classical),
        xai,
    )
