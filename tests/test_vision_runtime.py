from pathlib import Path

from PIL import Image

from app.ai.vision import (
    TorchvisionEmbeddingProvider,
    TorchvisionSegmentationProvider,
    YOLOVisionProvider,
)


def test_yolo_provider_runs_cpu_smoke_inference(tmp_path: Path):
    image_path = tmp_path / "blank.png"
    Image.new("RGB", (640, 480), (120, 120, 120)).save(image_path)
    model_path = Path(__file__).parents[1] / "instance" / "models" / "yolo11n.pt"
    result = YOLOVisionProvider(model_path).analyze(image_path)
    assert result["status"] == "READY"
    assert result["model"] == "yolo11n"
    assert isinstance(result["detections"], list)


def test_segmentation_and_embedding_packs_run(tmp_path: Path):
    image_path = tmp_path / "blank.png"
    Image.new("RGB", (640, 480), (120, 120, 120)).save(image_path)
    segmentation = TorchvisionSegmentationProvider(
        Path(__file__).parents[1] / "instance/models/deeplabv3_mobilenet_v3_large.pth"
    ).analyze(image_path)
    embedding = TorchvisionEmbeddingProvider(
        Path(__file__).parents[1] / "instance/models/mobilenet_v3_large.pth"
    ).analyze(image_path)
    assert segmentation["status"] == "READY"
    assert embedding["status"] == "READY"
    assert embedding["dimensions"] > 0
