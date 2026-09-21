from datetime import datetime, timezone

from app.ai.training import train_visual_model


def _sample(group, label, offset):
    return {
        "features": [100 + offset, 120 + offset, 20 + offset, 10 + offset],
        "label": label,
        "group": group,
        "timestamp": datetime.now(timezone.utc),
    }


def test_training_refuses_insufficient_labels(tmp_path):
    result = train_visual_model([_sample(1, "HIJAU", 0)], tmp_path)
    assert result.status == "INSUFFICIENT_DATA"
    assert "12" in result.reason


def test_training_uses_group_validation_and_persists_candidate(tmp_path):
    samples = [
        _sample(group, "HIJAU" if index % 2 else "COKELAT", index)
        for group in (1, 2)
        for index in range(12)
    ]
    result = train_visual_model(samples, tmp_path)
    assert result.status == "CANDIDATE_READY"
    assert result.validation_samples == 12
    assert result.accuracy is not None
    assert result.checksum
