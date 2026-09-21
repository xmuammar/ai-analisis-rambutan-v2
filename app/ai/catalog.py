"""Runtime catalogue for the agricultural ML/DL capability surface."""

from importlib.util import find_spec
from typing import Any

_ALGORITHMS = (
    ("Logistic Regression", "Klasifikasi", "sklearn", "Data label >= 2 kelas"),
    ("Decision Tree", "Klasifikasi", "sklearn", "Data label"),
    ("Random Forest", "Klasifikasi/regresi", "sklearn", "Data label"),
    ("Gradient Boosting", "Klasifikasi/regresi", "sklearn", "Data label"),
    ("XGBoost-compatible", "Klasifikasi/regresi", "sklearn", "Adapter dataset"),
    ("SVM / One-Class SVM", "Klasifikasi/anomali", "sklearn", "Data fitur"),
    ("KNN", "Klasifikasi", "sklearn", "Data fitur"),
    ("Naive Bayes", "Klasifikasi", "sklearn", "Data fitur"),
    ("Linear Regression", "Regresi", "sklearn", "Target numerik"),
    ("Isolation Forest", "Anomali", "sklearn", "Baseline historis"),
    ("K-Means / DBSCAN", "Clustering", "sklearn", "Data fitur"),
    ("PCA", "Reduksi dimensi", "sklearn", "Data fitur"),
    ("ARIMA-style / EWMA", "Time-series", "python", "Histori temporal"),
    ("LSTM / GRU", "Deep time-series", "torch", "Histori panjang"),
    ("YOLO / RT-DETR", "Object detection", "ultralytics", "Model vision"),
    (
        "MobileNet / EfficientNet / ConvNeXt",
        "Image classification",
        "torchvision",
        "Model vision",
    ),
    ("DINO / DINOv2", "Image embedding", "torch", "Model embedding"),
    ("SAM / MobileSAM / U-Net", "Segmentation", "torchvision", "Model segmentation"),
    ("Depth estimation", "Measurement", "torch", "Depth model + calibration"),
    ("SHAP / LIME", "Explainability", "shap", "Model prediction"),
    ("Grad-CAM / Heatmap", "Vision explainability", "torch", "Model vision"),
    ("Weighted Ensemble", "Model fusion", "python", ">=2 outputs"),
    ("Rule-Based Expert System", "Agricultural reasoning", "python", "Field evidence"),
)


def _runtime_available(runtime: str) -> bool:
    if runtime == "python":
        return True
    if runtime == "sklearn":
        return find_spec("sklearn") is not None
    if runtime == "torch":
        return find_spec("torch") is not None
    if runtime == "torchvision":
        return find_spec("torchvision") is not None
    if runtime == "ultralytics":
        return find_spec("ultralytics") is not None
    if runtime == "shap":
        return find_spec("shap") is not None
    return False


def get_algorithm_catalog() -> list[dict[str, Any]]:
    """Return capabilities without claiming that a model is trained/active."""
    return [
        {
            "name": name,
            "task": task,
            "runtime": runtime,
            "requirement": requirement,
            "runtime_status": (
                "TERPASANG" if _runtime_available(runtime) else "BELUM TERPASANG"
            ),
            "model_status": (
                "SIAP DIPAKAI"
                if runtime in {"python", "sklearn"}
                else "MEMERLUKAN MODEL/DATASET"
            ),
        }
        for name, task, runtime, requirement in _ALGORITHMS
    ]
