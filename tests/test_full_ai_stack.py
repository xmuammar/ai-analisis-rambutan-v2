from pathlib import Path

from PIL import Image

from app.ai.backup import build_backup, validate_backup
from app.ai.ml import detect_deviation, moving_average, weighted_ensemble
from app.ai.models import ModelManifest
from app.ai.vision import assess_image


def test_backup_checksum_and_tamper_detection():
    payload = build_backup({"trees": [{"code": "RBT-001"}]})
    assert validate_backup(payload) == (True, "Backup valid.")
    payload["data"]["trees"][0]["code"] = "RBT-999"
    assert validate_backup(payload)[0] is False


def test_ml_engines_refuse_insufficient_data():
    assert moving_average([1, 2], window=3).status == "INSUFFICIENT_DATA"
    assert detect_deviation(1, []).status == "INSUFFICIENT_DATA"
    assert weighted_ensemble([]).status == "INSUFFICIENT_DATA"


def test_image_quality_engine(tmp_path: Path):
    image_path = tmp_path / "tree.png"
    Image.new("RGB", (800, 600), (120, 120, 120)).save(image_path)
    result = assess_image(image_path)
    assert result.status == "GOOD"
    assert result.width == 800


def test_model_manifest_verification(tmp_path: Path):
    model_path = tmp_path / "model.bin"
    model_path.write_bytes(b"model")
    manifest = ModelManifest(
        "model",
        "Test model",
        "TREE_ANALYSIS",
        "1",
        "test",
        checksum="",
    )
    assert manifest.verify(model_path) is False
