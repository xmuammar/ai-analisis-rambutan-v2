from dataclasses import asdict
from importlib.metadata import PackageNotFoundError, version

from app.ai.models import ModelManager, ModelManifest
from app.ai.vision import (
    TorchvisionClassificationProvider,
    TorchvisionEmbeddingProvider,
    TorchvisionSegmentationProvider,
    VisionProvider,
    YOLOVisionProvider,
)


def system_snapshot(model_directory: str) -> dict:
    try:
        flask_version = version("Flask")
    except PackageNotFoundError:
        flask_version = "unknown"
    manager = ModelManager(model_directory)
    model_path = manager.model_directory / "yolo11n.pt"
    manifest = ModelManifest(
        model_id="yolo11n",
        name="YOLO11 Nano",
        task="OBJECT_DETECTION",
        version="11n",
        runtime="ultralytics-pytorch-cpu",
        checksum=None,
        size_bytes=model_path.stat().st_size if model_path.exists() else None,
    )
    vision = YOLOVisionProvider(model_path) if model_path.exists() else VisionProvider()
    packs = {
        "object_detection": (model_path, YOLOVisionProvider),
        "classification": (
            manager.model_directory / "mobilenet_v3_large.pth",
            TorchvisionClassificationProvider,
        ),
        "segmentation": (
            manager.model_directory / "deeplabv3_mobilenet_v3_large.pth",
            TorchvisionSegmentationProvider,
        ),
        "embedding": (
            manager.model_directory / "mobilenet_v3_large.pth",
            TorchvisionEmbeddingProvider,
        ),
    }
    return {
        "runtime": {"flask": flask_version},
        "vision": {
            "name": vision.name,
            "status": vision.status,
            "model_path": str(model_path),
            "model_size_bytes": (
                model_path.stat().st_size if model_path.exists() else None
            ),
        },
        "model": {"manifest": asdict(manifest), "status": manager.status(manifest)},
        "model_packs": {
            task: {
                "name": provider.name if path.exists() else "unavailable",
                "status": "AVAILABLE" if path.exists() else "NOT_INSTALLED",
                "path": str(path),
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
            for task, (path, provider) in packs.items()
        },
        "safety": {
            "fake_inference": False,
            "insufficient_data_fallback": True,
            "raw_data_preserved": True,
        },
    }
