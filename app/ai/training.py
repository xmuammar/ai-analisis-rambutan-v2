"""Safe, local-first training primitives for corrected visual observations."""

from __future__ import annotations

import hashlib
import json
import pickle
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

FEATURE_KEYS = (
    "brightness_mean",
    "green_mean",
    "green_dominance",
    "sharpness_proxy",
)


@dataclass(frozen=True)
class TrainingResult:
    status: str
    reason: str
    model_id: str
    version: str | None = None
    samples: int = 0
    validation_samples: int = 0
    accuracy: float | None = None
    artifact_path: str | None = None
    checksum: str | None = None


def _features(value: dict) -> list[float] | None:
    try:
        return [float(value[key]) for key in FEATURE_KEYS]
    except (KeyError, TypeError, ValueError):
        return None


def build_training_samples(predictions, corrections) -> list[dict]:
    """Use only user corrections as labels; raw AI predictions are never labels."""
    corrections_by_prediction = {
        correction.prediction_id: correction.user_final_value
        for correction in corrections
        if correction.user_final_value
    }
    samples = []
    for prediction in predictions:
        if prediction.id not in corrections_by_prediction:
            continue
        try:
            payload = json.loads(prediction.prediction)
        except (TypeError, json.JSONDecodeError):
            continue
        features = _features(payload)
        if features is None:
            continue
        samples.append(
            {
                "features": features,
                "label": corrections_by_prediction[prediction.id],
                "group": prediction.observation.tree_id,
                "timestamp": prediction.created_at,
            }
        )
    return samples


def train_visual_model(
    samples: list[dict],
    model_folder: str | Path,
    model_id: str = "rambutan-visual-color",
) -> TrainingResult:
    """Train and persist a candidate only when data and validation are adequate."""
    labels = {sample["label"] for sample in samples}
    groups = {sample["group"] for sample in samples}
    if len(samples) < 12:
        return TrainingResult(
            "INSUFFICIENT_DATA",
            "Minimal 12 label koreksi diperlukan sebelum training.",
            model_id,
            samples=len(samples),
        )
    if len(labels) < 2:
        return TrainingResult(
            "INSUFFICIENT_DATA",
            "Minimal dua kelas label diperlukan.",
            model_id,
            samples=len(samples),
        )
    if len(groups) < 2:
        return TrainingResult(
            "INSUFFICIENT_DATA",
            "Data harus berasal dari minimal dua pohon untuk mencegah leakage.",
            model_id,
            samples=len(samples),
        )
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score
    except ImportError:
        return TrainingResult(
            "FAILED", "scikit-learn belum terpasang.", model_id, samples=len(samples)
        )

    minimum_time = datetime.min.replace(tzinfo=timezone.utc)
    ordered = sorted(samples, key=lambda item: item["timestamp"] or minimum_time)
    validation_group = max(groups)
    train = [item for item in ordered if item["group"] != validation_group]
    validation = [item for item in ordered if item["group"] == validation_group]
    if not train or not validation or len({item["label"] for item in train}) < 2:
        return TrainingResult(
            "INSUFFICIENT_DATA",
            "Group validation split belum memiliki kelas yang cukup.",
            model_id,
            samples=len(samples),
            validation_samples=len(validation),
        )
    classifier = LogisticRegression(max_iter=500, random_state=42)
    classifier.fit(
        [item["features"] for item in train], [item["label"] for item in train]
    )
    accuracy = float(
        accuracy_score(
            [item["label"] for item in validation],
            classifier.predict([item["features"] for item in validation]),
        )
    )
    version = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    artifact_folder = Path(model_folder) / "trained"
    artifact_folder.mkdir(parents=True, exist_ok=True)
    artifact = artifact_folder / f"{model_id}-{version}.pkl"
    payload = {
        "model": classifier,
        "feature_keys": FEATURE_KEYS,
        "model_id": model_id,
        "version": version,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "validation_group": validation_group,
        "accuracy": accuracy,
    }
    artifact.write_bytes(pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL))
    checksum = hashlib.sha256(artifact.read_bytes()).hexdigest()
    return TrainingResult(
        "CANDIDATE_READY",
        "Kandidat tersimpan; aktivasi harus melewati perbandingan dengan model aktif.",
        model_id,
        version,
        len(samples),
        len(validation),
        accuracy,
        str(artifact),
        checksum,
    )
