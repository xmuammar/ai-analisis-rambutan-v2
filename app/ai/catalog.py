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
    ("K-Means / DBSCAN", "Pengelompokan pola", "sklearn", "Data fitur"),
    ("PCA", "Reduksi dimensi", "sklearn", "Data fitur"),
    ("ARIMA-style / EWMA", "Deret waktu", "python", "Histori temporal"),
    ("LSTM / GRU", "Deret waktu mendalam", "torch", "Histori panjang"),
    ("YOLO / RT-DETR", "Deteksi objek", "ultralytics", "Model visual"),
    (
        "MobileNet / EfficientNet / ConvNeXt",
        "Klasifikasi gambar",
        "torchvision",
        "Model vision",
    ),
    ("DINO / DINOv2", "Embedding gambar", "torch", "Model embedding"),
    ("SAM / MobileSAM / U-Net", "Segmentasi", "torchvision", "Model segmentasi"),
    ("Depth estimation", "Pengukuran", "torch", "Model kedalaman + kalibrasi"),
    ("SHAP / LIME", "Penjelasan model", "shap", "Prediksi model"),
    ("Grad-CAM / Heatmap", "Penjelasan visual", "torch", "Model visual"),
    ("Weighted Ensemble", "Penggabungan model", "python", ">=2 keluaran"),
    ("Rule-Based Expert System", "Penalaran agronomi", "python", "Bukti lapangan"),
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
            "runtime": {"python": "Python", "sklearn": "scikit-learn", "torch": "PyTorch",
                        "torchvision": "TorchVision", "ultralytics": "Ultralytics",
                        "shap": "SHAP"}.get(runtime, runtime),
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
