import json
from datetime import datetime, timezone
from io import BytesIO
from typing import ClassVar

import pytest
from PIL import Image

from app import create_app, db
from app.models import FieldPrediction, ObservationSession, Tree


@pytest.fixture()
def app(tmp_path):
    class TestConfig:
        TESTING = True
        SECRET_KEY = "test"
        WTF_CSRF_ENABLED = False
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.sqlite3'}"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        UPLOAD_FOLDER = tmp_path / "uploads"
        ALLOWED_IMAGE_EXTENSIONS: ClassVar[set[str]] = {"jpg", "jpeg", "png", "webp"}
        AUTO_CREATE_SCHEMA = True

    app = create_app(TestConfig)
    with app.app_context():
        from app.models import User

        user = User(username="tester")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
    yield app
    with app.app_context():
        db.drop_all()


@pytest.fixture()
def client(app):
    client = app.test_client()
    client.post("/auth/login", data={"username": "tester", "password": "password123"})
    return client


def test_seeded_twelve_trees(client, app):
    response = client.get("/trees")
    assert response.status_code == 200
    assert response.data.count(b"RBT-") == 12
    assert b"AI - Analis Rambutan" in response.data


def test_ownership_watermark_is_present_on_shared_layout(client):
    response = client.get("/trees")
    assert response.status_code == 200
    assert b"MILIK MUAMMAR, SST, M.KOM" in response.data
    assert b"copyright" in response.data


def test_inspection_uses_full_width_responsive_layout(client):
    response = client.get("/trees/1/inspection")
    assert response.status_code == 200
    assert b'class="inspection-layout"' in response.data


def test_about_page_lists_algorithm_groups(client):
    response = client.get("/about")
    assert response.status_code == 200
    assert b"Algoritma AI - Analis Rambutan" in response.data
    assert b"YOLO11 Nano" in response.data
    assert b"Random Forest / Gradient Boosting" in response.data
    assert b"Isolation Forest" in response.data
    assert b"LSTM / GRU" in response.data
    assert b"SHAP, LIME, Grad-CAM, dan Heatmap" in response.data
    assert b"Katalog runtime algoritma terpasang" in response.data
    assert b"Isolation Forest" in response.data
    assert b"INSUFFICIENT_DATA" in response.data


def test_developer_center_is_removed_from_user_interface(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"Developer Center" not in response.data
    assert client.get("/developer").status_code == 404


def test_manual_inspection_persists_soil_inference(client, app):
    with app.app_context():
        tree = db.session.scalar(db.select(Tree).where(Tree.code == "RBT-001"))
    response = client.post(
        f"/trees/{tree.id}/inspection",
        data={
            "mode": "PHOTO_FIRST",
            "surface_dark": "y",
            "notes": "Permukaan lembap.",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Data tersimpan" in response.data
    with app.app_context():
        observation = db.session.scalar(
            db.select(ObservationSession).where(ObservationSession.tree_id == tree.id)
        )
        assert observation is not None
        assert observation.soil.soil_moisture_visual == "MOIST"


def test_backup_requires_login(app):
    client = app.test_client()
    assert client.get("/backup.json").status_code == 302


def test_good_photo_runs_local_vision_provider(client, app):
    with app.app_context():
        tree = db.session.scalar(db.select(Tree).where(Tree.code == "RBT-001"))
    image = BytesIO()
    Image.new("RGB", (640, 480), (120, 120, 120)).save(image, format="PNG")
    image.seek(0)
    response = client.post(
        f"/trees/{tree.id}/inspection",
        data={
            "mode": "PHOTO_FIRST",
            "photos": (image, "tree.png"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert db.session.scalar(
            db.select(FieldPrediction).where(
                FieldPrediction.field_key == "root_zone_moisture_class"
            )
        )


def test_photo_analysis_endpoint_returns_all_model_statuses(client, app):
    with app.app_context():
        tree = db.session.scalar(db.select(Tree).where(Tree.code == "RBT-001"))
    image = BytesIO()
    Image.new("RGB", (640, 480), (120, 120, 120)).save(image, format="PNG")
    image.seek(0)
    response = client.post(
        f"/api/trees/{tree.id}/inspection/analyze",
        data={"photos": (image, "preview.png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "READY"
    assert payload["photo_count"] == 1
    assert set(payload["analyses"][0]["models"]) == {
        "object_detection",
        "classification",
        "embedding",
        "segmentation",
        "visual_features",
    }
    assert payload["analyses"][0]["models"]["visual_features"]["status"] == "READY"
    assert payload["auto_fields"]["leaf_color_observed"]["status"] == "ESTIMATED"
    assert payload["auto_fields"]["detected_objects"]["value"] == []
    assert (
        b"Tidak ada objek terdeteksi" in client.get(f"/trees/{tree.id}/inspection").data
    )
    assert payload["pipeline"]["ready_model_count"] >= 1
    assert payload["analyst_summary"]["priority"] == "PERLU KONFIRMASI"
    assert payload["problem_analysis"]["algorithm_count"] >= 8
    assert "flower_fruit" in payload["problem_analysis"]["components"]


def test_saved_inspection_renders_ml_driven_form(client, app):
    with app.app_context():
        tree = db.session.scalar(db.select(Tree).where(Tree.code == "RBT-001"))
    analysis = {
        "auto_fields": {
            "leaf_color_observed": {
                "value": "DOMINAN_HIJAU",
                "status": "ESTIMATED",
                "confidence": 0.65,
                "source": "visual-feature-extractor",
            },
            "pest_or_disease": {
                "value": None,
                "status": "NEEDS_CONFIRMATION",
                "confidence": 0.0,
                "source": "NO_AGRICULTURE_SPECIFIC_MODEL",
            },
        },
        "pipeline": {"ready_model_count": 5, "model_count": 5},
        "algorithms": [
            {
                "name": "Weighted Ensemble",
                "status": "READY",
                "details": "Penggabungan keluaran model lokal",
            }
        ],
    }
    response = client.post(
        f"/trees/{tree.id}/inspection",
        data={"mode": "PHOTO_FIRST", "ai_analysis": json.dumps(analysis)},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Form hasil machine learning" in response.data
    assert b"DOMINAN_HIJAU" in response.data
    assert b"NEEDS_CONFIRMATION" in response.data


def test_inspection_form_renders_database_sections(client, app):
    with app.app_context():
        tree = db.session.scalar(db.select(Tree).where(Tree.code == "RBT-001"))
    response = client.get(f"/trees/{tree.id}/inspection")
    assert response.status_code == 200
    assert b"Tanah dan daun" in response.data
    assert b"Ukuran dan perkembangan pohon" in response.data
    assert b"Bunga dan buah" in response.data
    assert b'name="height_cm"' in response.data
    assert b'name="fruit_stage"' in response.data
    assert b"Ringkasan analisis lapangan" in response.data
    assert b"Keyakinan gabungan" in response.data
    assert b"Masukkan konfirmasi analis" in response.data
    assert b"const formFieldKeys = new Set" in response.data
    assert response.data.count(b"data-after-analysis hidden") == 6
    assert b"Perlu diisi atau dikonfirmasi pengguna" in response.data
    assert b"renderProcessingAlgorithms" in response.data
    assert b"data-ai-locked" in response.data
    assert b"tidak perlu input manual" in response.data
    assert b"YOLO11 Nano" in response.data
    assert b"DeepLabV3 Segmentation" in response.data
    assert b"problem-analysis" in response.data
    assert b"Orkestrasi analisis pertanian" in response.data
    assert b"LSTM / GRU" in response.data
    assert b"SHAP / LIME / Grad-CAM / Heatmap" in response.data
    assert b"Virtual Soil Sensor" in response.data
    html = response.data.decode()
    assert html.index("Ringkasan analisis lapangan") < html.index("Tanah dan daun")
    assert b"Metode:</strong> Pemeriksaan berbasis foto" in response.data
    assert b">Hybrid<" not in response.data
    assert b">Manual<" not in response.data


def test_dashboard_renders_analyst_metrics_and_visualizations(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"Dashboard Analitik Kebun" in response.data
    assert b"Putaran pemeriksaan 30 hari" in response.data
    assert b"Status seluruh pohon" in response.data
    assert b"Object detection" in response.data


def test_dashboard_handles_sqlite_naive_observation_timestamp(client, app):
    with app.app_context():
        tree = db.session.scalar(db.select(Tree).where(Tree.code == "RBT-001"))
        db.session.add(
            ObservationSession(
                tree_id=tree.id,
                observer="tester",
                inspection_mode="MANUAL",
                observation_datetime=datetime(
                    2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc
                ).replace(tzinfo=None),
                general_condition="SEHAT",
            )
        )
        db.session.commit()
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"RBT-001" in response.data
