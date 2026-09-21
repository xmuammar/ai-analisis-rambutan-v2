from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImageQuality:
    status: str
    reasons: tuple[str, ...]
    width: int | None = None
    height: int | None = None
    brightness: float | None = None


def assess_image(path: str | Path) -> ImageQuality:
    """Assess basic image quality without pretending to run a vision model."""
    try:
        from PIL import Image, ImageStat
    except ImportError:
        return ImageQuality("UNAVAILABLE", ("Pillow belum terpasang.",))

    try:
        with Image.open(path) as image:
            width, height = image.size
            brightness = sum(ImageStat.Stat(image.convert("L")).mean) / 1
    except (OSError, ValueError) as error:
        return ImageQuality("INVALID", (f"Foto tidak dapat dibaca: {error}",))

    reasons: list[str] = []
    if width < 640 or height < 480:
        reasons.append("Resolusi foto rendah.")
    if brightness < 35:
        reasons.append("Foto terlalu gelap.")
    elif brightness > 225:
        reasons.append("Foto terlalu terang.")
    if reasons:
        return ImageQuality(
            "RETAKE_REQUIRED", tuple(reasons), width, height, brightness
        )
    return ImageQuality(
        "GOOD", ("Kualitas dasar foto memadai.",), width, height, brightness
    )


def extract_visual_features(path: str | Path) -> dict:
    """Extract measurable image signals without claiming species diagnosis."""
    try:
        from PIL import Image
    except ImportError:
        return {
            "status": "UNAVAILABLE",
            "message": "Pillow belum terpasang.",
            "model": "visual-feature-extractor",
        }

    try:
        with Image.open(path) as image:
            rgb = image.convert("RGB")
            sample = list(rgb.resize((64, 64)).getdata())
    except (OSError, ValueError) as error:
        return {
            "status": "FAILED",
            "message": f"Fitur visual gagal diekstrak: {error}",
            "model": "visual-feature-extractor",
        }

    red = sum(pixel[0] for pixel in sample) / len(sample)
    green = sum(pixel[1] for pixel in sample) / len(sample)
    blue = sum(pixel[2] for pixel in sample) / len(sample)
    brightness = (red + green + blue) / 3
    green_dominance = max(0.0, green - (red + blue) / 2)
    gray = [(r + g + b) / 3 for r, g, b in sample]
    sharpness_proxy = sum(
        abs(gray[index] - gray[index - 1]) for index in range(1, len(gray))
    ) / (len(gray) - 1)
    if green_dominance >= 18 and green >= red * 1.08:
        color_class = "DOMINAN_HIJAU"
    elif brightness < 60:
        color_class = "GELAP"
    elif red > green * 1.12:
        color_class = "DOMINAN_COKELAT_MERAH"
    else:
        color_class = "CAMPURAN"
    return {
        "status": "READY",
        "model": "visual-feature-extractor",
        "message": "Sinyal warna dan ketajaman terukur; bukan diagnosis penyakit.",
        "brightness_mean": round(brightness, 2),
        "red_mean": round(red, 2),
        "green_mean": round(green, 2),
        "blue_mean": round(blue, 2),
        "green_dominance": round(green_dominance, 2),
        "sharpness_proxy": round(sharpness_proxy, 2),
        "color_class": color_class,
        "confidence": 0.65,
    }


class VisionProvider:
    name = "vision-model-unavailable"
    status = "NOT_INSTALLED"

    def analyze(self, image_path: str | Path) -> dict:
        return {
            "status": "INSUFFICIENT_DATA",
            "message": "Model analisis visual belum terpasang.",
            "model": self.name,
        }


class YOLOVisionProvider(VisionProvider):
    name = "yolo11n"
    status = "AVAILABLE"

    def __init__(self, model_path: str | Path):
        self.model_path = Path(model_path)
        self._model = None

    def _load(self):
        if self._model is None:
            from ultralytics import YOLO

            self._model = YOLO(str(self.model_path))
        return self._model

    def analyze(self, image_path: str | Path) -> dict:
        quality = assess_image(image_path)
        if quality.status in {"INVALID", "RETAKE_REQUIRED", "UNAVAILABLE"}:
            return {
                "status": quality.status,
                "message": "Inference dihentikan karena kualitas foto.",
                "quality": quality,
                "model": self.name,
            }
        try:
            result = self._load()(str(image_path), device="cpu", verbose=False)[0]
        except (OSError, RuntimeError, ValueError) as error:
            return {
                "status": "FAILED",
                "message": f"Inference vision gagal: {error}",
                "model": self.name,
            }
        detections = []
        for box in result.boxes:
            class_id = int(box.cls[0])
            detections.append(
                {
                    "class_id": class_id,
                    "label": result.names[class_id],
                    "confidence": float(box.conf[0]),
                    "xyxy": [round(float(value), 2) for value in box.xyxy[0].tolist()],
                }
            )
        return {
            "status": "READY",
            "model": self.name,
            "model_version": "11n",
            "detections": detections,
            "quality": quality,
        }


class TorchvisionClassificationProvider(VisionProvider):
    name = "mobilenet_v3_large"
    status = "AVAILABLE"

    def __init__(self, model_path: str | Path):
        self.model_path = Path(model_path)
        self._model = None

    def _load(self):
        import torch
        from torchvision.models import MobileNet_V3_Large_Weights, mobilenet_v3_large

        if self._model is None:
            model = mobilenet_v3_large(weights=None)
            model.load_state_dict(torch.load(self.model_path, map_location="cpu"))
            model.eval()
            self._model = (model, MobileNet_V3_Large_Weights.DEFAULT.transforms())
        return self._model

    def analyze(self, image_path: str | Path) -> dict:
        quality = assess_image(image_path)
        if quality.status != "GOOD":
            return {"status": quality.status, "quality": quality, "model": self.name}
        import torch
        from PIL import Image
        from torchvision.models import MobileNet_V3_Large_Weights

        try:
            model, transform = self._load()
            with Image.open(image_path) as image, torch.inference_mode():
                logits = model(transform(image).unsqueeze(0))
                probabilities = logits.softmax(dim=1)[0]
            score, class_id = probabilities.max(dim=0)
            categories = MobileNet_V3_Large_Weights.DEFAULT.meta["categories"]
            return {
                "status": "READY",
                "model": self.name,
                "class_id": int(class_id),
                "class_label": categories[int(class_id)],
                "confidence": float(score),
                "message": "Klasifikasi umum ImageNet; bukan diagnosis tanaman.",
                "quality": quality,
            }
        except (OSError, RuntimeError, ValueError) as error:
            return {"status": "FAILED", "model": self.name, "message": str(error)}


class TorchvisionEmbeddingProvider(TorchvisionClassificationProvider):
    name = "mobilenet_v3_large_embedding"

    def analyze(self, image_path: str | Path) -> dict:
        quality = assess_image(image_path)
        if quality.status != "GOOD":
            return {"status": quality.status, "quality": quality, "model": self.name}
        import torch
        from PIL import Image

        try:
            model, transform = self._load()
            with Image.open(image_path) as image, torch.inference_mode():
                features = model.features(transform(image).unsqueeze(0))
                vector = torch.nn.functional.adaptive_avg_pool2d(features, 1)
                vector = torch.nn.functional.normalize(vector.flatten(1), dim=1)[0]
            return {
                "status": "READY",
                "model": self.name,
                "dimensions": int(vector.numel()),
                "embedding": [round(float(value), 8) for value in vector],
                "message": "Embedding visual umum; bukan embedding tanaman khusus.",
                "quality": quality,
            }
        except (OSError, RuntimeError, ValueError) as error:
            return {"status": "FAILED", "model": self.name, "message": str(error)}


class TorchvisionSegmentationProvider(VisionProvider):
    name = "deeplabv3_mobilenet_v3_large"
    status = "AVAILABLE"

    def __init__(self, model_path: str | Path):
        self.model_path = Path(model_path)
        self._model = None

    def _load(self):
        import torch
        from torchvision.models.segmentation import (
            deeplabv3_mobilenet_v3_large,
        )

        if self._model is None:
            model = deeplabv3_mobilenet_v3_large(
                weights=None, weights_backbone=None, aux_loss=True
            )
            model.load_state_dict(torch.load(self.model_path, map_location="cpu"))
            model.eval()
            self._model = model
        return self._model

    def analyze(self, image_path: str | Path) -> dict:
        quality = assess_image(image_path)
        if quality.status != "GOOD":
            return {"status": quality.status, "quality": quality, "model": self.name}
        import torch
        from PIL import Image
        from torchvision.transforms import v2

        try:
            transform = v2.Compose(
                [v2.ToImage(), v2.ToDtype(torch.float32, scale=True)]
            )
            with Image.open(image_path) as image, torch.inference_mode():
                output = self._load()(transform(image).unsqueeze(0))["out"]
                mask = output.argmax(1)[0]
            unique, counts = torch.unique(mask, return_counts=True)
            return {
                "status": "READY",
                "model": self.name,
                "class_count": int(mask.max()) + 1,
                "pixel_count": int(mask.numel()),
                "class_distribution": {
                    str(int(class_id)): round(int(count) / mask.numel(), 4)
                    for class_id, count in zip(unique, counts)
                },
                "message": "Segmentasi umum COCO; bukan segmentasi spesies tanaman.",
                "quality": quality,
            }
        except (OSError, RuntimeError, ValueError) as error:
            return {"status": "FAILED", "model": self.name, "message": str(error)}


def analyze_available_models(image_path: str | Path, model_folder: str | Path) -> dict:
    """Run every installed local vision pack and return auditable raw outputs."""
    folder = Path(model_folder)
    results: dict[str, dict] = {}
    results["visual_features"] = extract_visual_features(image_path)
    providers = (
        ("object_detection", YOLOVisionProvider(folder / "yolo11n.pt")),
        (
            "classification",
            TorchvisionClassificationProvider(folder / "mobilenet_v3_large.pth"),
        ),
        ("embedding", TorchvisionEmbeddingProvider(folder / "mobilenet_v3_large.pth")),
        (
            "segmentation",
            TorchvisionSegmentationProvider(
                folder / "deeplabv3_mobilenet_v3_large.pth"
            ),
        ),
    )
    for key, provider in providers:
        if not provider.model_path.exists():
            results[key] = {
                "status": "NOT_INSTALLED",
                "model": provider.name,
                "message": "Model pack belum tersedia.",
            }
            continue
        results[key] = provider.analyze(image_path)
    return results


def build_ai_inspection_note(
    model_results: dict,
    *,
    visual_anomaly: str | None,
) -> tuple[str, float]:
    """Compose an evidence-only examiner note from installed model outputs."""
    visual = model_results.get("visual_features", {})
    detection = model_results.get("object_detection", {})
    classification = model_results.get("classification", {})
    segmentation = model_results.get("segmentation", {})
    evidence: list[str] = []
    confidence_values: list[float] = []
    if visual.get("status") == "READY":
        brightness = visual.get("brightness_mean")
        color = visual.get("color_class")
        sharpness = visual.get("sharpness_proxy")
        evidence.append(
            f"Fitur visual mengukur warna {color}, pencahayaan "
            f"{brightness:.2f}, dan ketajaman {sharpness:.2f}."
        )
        confidence_values.append(float(visual.get("confidence", 0.0)))
    if detection.get("status") == "READY":
        detections = detection.get("detections", [])
        if detections:
            labels = ", ".join(str(item.get("label")) for item in detections)
            evidence.append(f"Deteksi objek menemukan: {labels}.")
            confidence_values.extend(
                float(item.get("confidence", 0.0)) for item in detections
            )
        else:
            evidence.append("Deteksi objek tidak menemukan objek pada foto.")
    if classification.get("status") == "READY":
        evidence.append(
            "Klasifikasi deep learning umum menghasilkan kelas visual "
            f"{classification.get('class_label')}; hasil ini bukan diagnosis pertanian."
        )
        confidence_values.append(float(classification.get("confidence", 0.0)))
    if segmentation.get("status") == "READY":
        evidence.append(
            "Segmentasi deep learning berhasil membuat ringkasan area visual."
        )
    if visual_anomaly:
        evidence.append(f"Penyaringan anomali visual: {visual_anomaly}")
    missing = [
        name
        for name, result in model_results.items()
        if result.get("status") not in {"READY"}
    ]
    if missing:
        evidence.append(
            "Field pertanian khusus yang belum didukung model tetap perlu "
            "diisi atau dikonfirmasi pengguna."
        )
    if not evidence:
        evidence.append(
            "Model vision belum menghasilkan bukti yang cukup; catatan perlu "
            "dilengkapi pengguna."
        )
    confidence = (
        sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
    )
    return " ".join(evidence), round(confidence, 4)


def screen_agricultural_fields(
    visual: dict, detection: dict, segmentation: dict, visual_anomaly: str | None
) -> dict[str, dict]:
    """Run conservative agricultural screening on general vision outputs."""
    detections = detection.get("detections", [])
    pest_labels = {"insect", "spider", "butterfly"}
    pest_hits = [
        item
        for item in detections
        if str(item.get("label", "")).strip().lower() in pest_labels
    ]
    source = "HYBRID_AGRICULTURE_SCREENING"
    screening_confidence = (
        0.2
        if (
            visual.get("status") == "READY"
            or detection.get("status") == "READY"
            or segmentation.get("status") == "READY"
        )
        else 0.0
    )
    pest_value = True if pest_hits else None
    pest_type = (
        "Objek pengganggu visual terdeteksi; konfirmasi kategori" if pest_hits else None
    )
    disease_value = None
    disease_type = (
        "Anomali visual perlu diperiksa; bukan diagnosis"
        if visual_anomaly and "Tidak ada anomali" not in visual_anomaly
        else None
    )
    evidence = (
        "YOLO11, fitur visual, dan segmentasi sudah menjalankan screening "
        "awal; hasil hama, penyakit, dan gulma tetap memerlukan konfirmasi."
    )
    return {
        "pest_present": {
            "value": pest_value,
            "status": "NEEDS_CONFIRMATION",
            "confidence": max(
                (float(item.get("confidence", 0.0)) for item in pest_hits),
                default=screening_confidence,
            ),
            "source": source,
            "evidence": evidence,
        },
        "pest_type": {
            "value": pest_type,
            "status": "NEEDS_CONFIRMATION",
            "confidence": screening_confidence,
            "source": source,
            "evidence": evidence,
        },
        "disease_present": {
            "value": disease_value,
            "status": "NEEDS_CONFIRMATION",
            "confidence": screening_confidence,
            "source": source,
            "evidence": evidence,
        },
        "disease_type": {
            "value": disease_type,
            "status": "NEEDS_CONFIRMATION",
            "confidence": screening_confidence,
            "source": source,
            "evidence": evidence,
        },
        "weed_level": {
            "value": None,
            "status": "NEEDS_CONFIRMATION",
            "confidence": screening_confidence,
            "source": source,
            "evidence": evidence,
        },
        "weed_coverage_percent": {
            "value": None,
            "status": "NEEDS_CONFIRMATION",
            "confidence": screening_confidence,
            "source": source,
            "evidence": evidence,
        },
    }


def screen_flower_fruit_fields(
    detection: dict, visual: dict, segmentation: dict
) -> dict[str, dict]:
    """Screen flower/fruit fields from available vision evidence.

    General-purpose models can support conservative class screening, but they
    are not treated as a rambutan disease or maturity diagnosis model.
    """
    detections = detection.get("detections", [])
    flower_hits = [
        item
        for item in detections
        if str(item.get("label", "")).strip().lower() in {"flower", "flowers"}
    ]
    fruit_hits = [
        item
        for item in detections
        if str(item.get("label", "")).strip().lower()
        in {"fruit", "apple", "orange", "banana"}
    ]
    model_ready = any(
        result.get("status") == "READY" for result in (detection, visual, segmentation)
    )
    confidence = (
        max(
            (float(item.get("confidence", 0.0)) for item in flower_hits + fruit_hits),
            default=0.0,
        )
        if model_ready
        else 0.0
    )
    source = "HYBRID_FLOWER_FRUIT_SCREENING"
    visual_ready = visual.get("status") == "READY"
    color_class = str(visual.get("color_class", "")).upper()
    red = float(visual.get("red_mean", 0.0) or 0.0)
    green = float(visual.get("green_mean", 0.0) or 0.0)
    if fruit_hits and visual_ready:
        if red > green * 1.12:
            fruit_stage = "RIPE"
        elif red > green:
            fruit_stage = "NEAR_RIPE"
        elif color_class == "DOMINAN_HIJAU":
            fruit_stage = "DEVELOPING"
        else:
            fruit_stage = "YOUNG"
    else:
        fruit_stage = None
    flower_stage = "FLOWERING" if flower_hits else None
    positive_confidence = max(0.25, min(0.9, confidence))
    negative_confidence = 0.3 if detection.get("status") == "READY" else 0.0
    evidence = (
        "YOLO11, fitur visual, dan segmentasi menjalankan screening bunga/buah. "
        "Tahap adalah inferensi warna/objek umum, bukan diagnosis varietas rambutan."
    )
    return {
        "flower_present": {
            "value": bool(flower_hits) if detection.get("status") == "READY" else None,
            "status": "OBSERVED" if flower_hits else "INFERRED",
            "confidence": positive_confidence if flower_hits else negative_confidence,
            "source": source,
            "evidence": evidence,
        },
        "flower_stage": {
            "value": flower_stage,
            "status": "ESTIMATED" if flower_stage else "INFERRED",
            "confidence": (
                positive_confidence * 0.7 if flower_stage else negative_confidence
            ),
            "source": source,
            "evidence": evidence,
        },
        "fruit_present": {
            "value": bool(fruit_hits) if detection.get("status") == "READY" else None,
            "status": "OBSERVED" if fruit_hits else "INFERRED",
            "confidence": positive_confidence if fruit_hits else negative_confidence,
            "source": source,
            "evidence": evidence,
        },
        "fruit_stage": {
            "value": fruit_stage,
            "status": "ESTIMATED" if fruit_stage else "INFERRED",
            "confidence": (
                positive_confidence * 0.65 if fruit_stage else negative_confidence
            ),
            "source": source,
            "evidence": evidence,
        },
        "fruit_count_estimate": {
            "value": len(fruit_hits) if fruit_hits else None,
            "status": "ESTIMATED" if fruit_hits else "INFERRED",
            "confidence": positive_confidence if fruit_hits else negative_confidence,
            "source": source,
            "evidence": evidence,
        },
        "fruit_damage_percent": {
            "value": 0 if fruit_hits else None,
            "status": "INFERRED",
            "confidence": (
                positive_confidence * 0.35 if fruit_hits else negative_confidence
            ),
            "source": source,
            "evidence": evidence
            + " Tidak ada kerusakan visual yang cukup kuat terdeteksi; nilai 0 "
            "adalah screening konservatif dan perlu koreksi bila terlihat kerusakan.",
        },
    }


def screen_soil_leaf_fields(visual: dict, segmentation: dict) -> dict[str, dict]:
    """Infer soil/leaf classes from measurable visual signals, never precision."""
    if visual.get("status") != "READY":
        source = "SOIL_LEAF_VISUAL_ENSEMBLE"
        return {
            key: {
                "value": None,
                "status": "NEEDS_CONFIRMATION",
                "confidence": 0.0,
                "source": source,
                "evidence": "Fitur visual tidak tersedia.",
            }
            for key in (
                "surface_dark",
                "standing_water",
                "leaf_wilt",
                "soil_moisture_visual",
            )
        }
    brightness = float(visual.get("brightness_mean", 0.0) or 0.0)
    green = float(visual.get("green_dominance", 0.0) or 0.0)
    blue = float(visual.get("blue_mean", 0.0) or 0.0)
    red = float(visual.get("red_mean", 0.0) or 0.0)
    dark = brightness < 100
    water_signal = (
        dark
        and blue >= red * 0.95
        and (segmentation.get("status") == "READY" or blue >= green * 0.85)
    )
    wilt_signal = green < 12 or (green < 20 and brightness < 75)
    if water_signal:
        moisture = "WATERLOGGED"
    elif dark:
        moisture = "MOIST"
    elif brightness < 145:
        moisture = "SLIGHTLY_DRY"
    else:
        moisture = "DRY"
    confidence = 0.45 if segmentation.get("status") == "READY" else 0.35
    evidence = (
        f"Ensemble visual mengukur brightness {brightness:.2f}, dominasi hijau "
        f"{green:.2f}, dan sinyal warna RGB; segmentasi "
        f"{'tersedia' if segmentation.get('status') == 'READY' else 'belum tersedia'}."
    )
    return {
        "surface_dark": {
            "value": dark,
            "status": "ESTIMATED",
            "confidence": confidence,
            "source": "SOIL_LEAF_VISUAL_ENSEMBLE",
            "evidence": evidence,
        },
        "standing_water": {
            "value": water_signal,
            "status": "INFERRED",
            "confidence": confidence * 0.8,
            "source": "SOIL_LEAF_VISUAL_ENSEMBLE",
            "evidence": evidence
            + " Genangan adalah indikasi visual, bukan pengukuran sensor.",
        },
        "leaf_wilt": {
            "value": wilt_signal,
            "status": "ESTIMATED",
            "confidence": confidence * 0.75,
            "source": "SOIL_LEAF_VISUAL_ENSEMBLE",
            "evidence": evidence
            + " Layu daun disaring dari sinyal warna; bukan diagnosis penyakit.",
        },
        "soil_moisture_visual": {
            "value": moisture,
            "status": "INFERRED",
            "confidence": confidence,
            "source": "SOIL_LEAF_VISUAL_ENSEMBLE",
            "evidence": evidence
            + " Kelembapan adalah kelas visual, bukan nilai sensor numerik.",
        },
    }


def aggregate_inspection_fields(model_results: dict) -> dict:
    """Map model outputs to only fields with explicit measurable evidence."""
    visual = model_results.get("visual_features", {})
    detection = model_results.get("object_detection", {})
    classification = model_results.get("classification", {})
    segmentation = model_results.get("segmentation", {})
    visual_ready = visual.get("status") == "READY"
    detections = detection.get("detections", [])
    detected_labels = {
        str(item.get("label", "")).strip().lower() for item in detections
    }
    detected_flower = bool({"flower", "flowers"} & detected_labels)
    detected_fruit = bool({"fruit", "apple", "orange", "banana"} & detected_labels)
    visual_brightness = visual.get("brightness_mean")
    visual_anomaly = None
    if visual_ready:
        if visual_brightness is not None and visual_brightness < 45:
            visual_anomaly = (
                "Foto terlalu gelap; gejala hama/penyakit tidak dapat dinilai."
            )
        elif visual_brightness is not None and visual_brightness > 220:
            visual_anomaly = (
                "Foto terlalu terang; gejala hama/penyakit tidak dapat dinilai."
            )
        elif visual.get("green_dominance", 0) < 8:
            visual_anomaly = (
                "Warna daun tidak cukup dominan hijau; perlu pemeriksaan pengguna."
            )
        else:
            visual_anomaly = "Tidak ada anomali visual umum yang cukup untuk diagnosis."
    automatic_note, note_confidence = build_ai_inspection_note(
        model_results,
        visual_anomaly=visual_anomaly,
    )
    agricultural_fields = screen_agricultural_fields(
        visual, detection, segmentation, visual_anomaly
    )
    flower_fruit_fields = screen_flower_fruit_fields(detection, visual, segmentation)
    soil_leaf_fields = screen_soil_leaf_fields(visual, segmentation)
    fields = {
        "notes": {
            "value": automatic_note,
            "status": "DERIVED",
            "confidence": note_confidence,
            "source": "HYBRID_VISION_XAI",
        },
        **soil_leaf_fields,
        "height_cm": {
            "value": None,
            "status": "NEEDS_CONFIRMATION",
            "confidence": 0.0,
            "source": "NO_DEPTH_OR_REFERENCE_MODEL",
        },
        "stem_diameter_cm": {
            "value": None,
            "status": "NEEDS_CONFIRMATION",
            "confidence": 0.0,
            "source": "NO_DEPTH_OR_REFERENCE_MODEL",
        },
        "canopy_width_cm": {
            "value": None,
            "status": "NEEDS_CONFIRMATION",
            "confidence": 0.0,
            "source": "NO_DEPTH_OR_REFERENCE_MODEL",
        },
        "flower_present": {
            "value": detected_flower if detection.get("status") == "READY" else None,
            "status": "OBSERVED" if detected_flower else "NEEDS_CONFIRMATION",
            "confidence": max(
                (
                    item.get("confidence", 0.0)
                    for item in detections
                    if str(item.get("label", "")).strip().lower()
                    in {"flower", "flowers"}
                ),
                default=0.0,
            ),
            "source": detection.get("model") or "NO_AGRICULTURE_SPECIFIC_MODEL",
        },
        "flower_stage": {
            "value": None,
            "status": "NEEDS_CONFIRMATION",
            "confidence": 0.0,
            "source": "NO_AGRICULTURE_SPECIFIC_MODEL",
        },
        "fruit_present": {
            "value": detected_fruit if detection.get("status") == "READY" else None,
            "status": "OBSERVED" if detected_fruit else "NEEDS_CONFIRMATION",
            "confidence": max(
                (
                    item.get("confidence", 0.0)
                    for item in detections
                    if str(item.get("label", "")).strip().lower()
                    in {"fruit", "apple", "orange", "banana"}
                ),
                default=0.0,
            ),
            "source": detection.get("model") or "NO_AGRICULTURE_SPECIFIC_MODEL",
        },
        "fruit_stage": {
            "value": None,
            "status": "NEEDS_CONFIRMATION",
            "confidence": 0.0,
            "source": "NO_AGRICULTURE_SPECIFIC_MODEL",
        },
        "fruit_count_estimate": {
            "value": (
                len(
                    [
                        item
                        for item in detections
                        if str(item.get("label", "")).strip().lower()
                        in {"fruit", "apple", "orange", "banana"}
                    ]
                )
                if detected_fruit
                else None
            ),
            "status": "ESTIMATED" if detected_fruit else "NEEDS_CONFIRMATION",
            "confidence": 0.0,
            "source": detection.get("model") or "NO_AGRICULTURE_SPECIFIC_MODEL",
        },
        "fruit_damage_percent": {
            "value": None,
            "status": "NEEDS_CONFIRMATION",
            "confidence": 0.0,
            "source": "NO_AGRICULTURE_SPECIFIC_MODEL",
        },
        **agricultural_fields,
        **flower_fruit_fields,
        "leaf_color_observed": {
            "value": visual.get("color_class"),
            "status": "ESTIMATED" if visual.get("status") == "READY" else "UNKNOWN",
            "confidence": visual.get("confidence", 0.0),
            "source": visual.get("model"),
        },
        "visual_brightness_mean": {
            "value": visual.get("brightness_mean"),
            "status": "MEASURED" if visual.get("status") == "READY" else "UNKNOWN",
            "confidence": visual.get("confidence", 0.0),
            "source": visual.get("model"),
        },
        "visual_sharpness_proxy": {
            "value": visual.get("sharpness_proxy"),
            "status": "MEASURED" if visual.get("status") == "READY" else "UNKNOWN",
            "confidence": visual.get("confidence", 0.0),
            "source": visual.get("model"),
        },
        "detected_objects": {
            "value": (
                detection.get("detections", [])
                if detection.get("status") == "READY"
                else None
            ),
            "status": "OBSERVED" if detection.get("status") == "READY" else "UNKNOWN",
            "confidence": max(
                (
                    item.get("confidence", 0.0)
                    for item in detection.get("detections", [])
                ),
                default=0.0,
            ),
            "source": detection.get("model"),
        },
        "generic_image_class": {
            "value": classification.get("class_label"),
            "status": (
                "ESTIMATED" if classification.get("status") == "READY" else "UNKNOWN"
            ),
            "confidence": classification.get("confidence", 0.0),
            "source": classification.get("model"),
        },
        "segmentation_summary": {
            "value": segmentation.get("class_distribution"),
            "status": (
                "ESTIMATED" if segmentation.get("status") == "READY" else "UNKNOWN"
            ),
            "confidence": 0.0,
            "source": segmentation.get("model"),
        },
        "root_zone_moisture_class": {
            "value": None,
            "status": "NEEDS_CONFIRMATION",
            "confidence": 0.0,
            "source": "NO_SOIL_SPECIFIC_MODEL",
        },
        "pest_or_disease": {
            "value": visual_anomaly,
            "status": "NEEDS_CONFIRMATION",
            "confidence": 0.2 if visual_ready else 0.0,
            "source": (
                "VISUAL_ANOMALY_SCREENING"
                if visual_ready
                else "NO_AGRICULTURE_SPECIFIC_MODEL"
            ),
        },
    }
    return {
        "fields": fields,
        "ready_model_count": sum(
            result.get("status") == "READY" for result in model_results.values()
        ),
        "model_count": len(model_results),
    }


def aggregate_photo_models(analyses: list[dict]) -> dict:
    """Fuse per-photo outputs while preserving uncertainty and provenance."""
    model_keys = {key for analysis in analyses for key in analysis.get("models", {})}
    combined: dict[str, dict] = {}
    for key in model_keys:
        results = [
            analysis["models"][key]
            for analysis in analyses
            if key in analysis.get("models", {})
        ]
        ready = [result for result in results if result.get("status") == "READY"]
        if not ready:
            combined[key] = results[0] if results else {"status": "INSUFFICIENT_DATA"}
            continue
        if key == "visual_features":
            numeric_fields = (
                "brightness_mean",
                "green_mean",
                "green_dominance",
                "sharpness_proxy",
            )
            merged = dict(ready[0])
            for field in numeric_fields:
                values = [float(item[field]) for item in ready if field in item]
                if values:
                    merged[field] = round(sum(values) / len(values), 2)
            colors = [item.get("color_class") for item in ready]
            merged["color_class"] = max(set(colors), key=colors.count)
            merged["confidence"] = round(
                sum(float(item.get("confidence", 0.0)) for item in ready) / len(ready),
                4,
            )
            combined[key] = merged
        elif key == "object_detection":
            merged = dict(ready[0])
            merged["detections"] = [
                detection for item in ready for detection in item.get("detections", [])
            ]
            combined[key] = merged
        else:
            combined[key] = ready[0]
    return combined
