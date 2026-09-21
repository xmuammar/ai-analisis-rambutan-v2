# AiAnalisRambutan Web

Versi web full-stack Python Flask untuk domain yang sama dengan aplikasi mobile di `mobile/`.
Source web sepenuhnya berada di direktori ini dan tidak memakai Django, React, Vue, Next.js,
Flutter Web, atau Node.js sebagai application server.

## Stack

- Flask application factory + Jinja2
- SQLAlchemy dan Flask-Migrate (Alembic)
- Flask-WTF untuk form/CSRF
- Flask-Login untuk autentikasi lokal
- SQLite sebagai development default; `DATABASE_URL` dapat diarahkan ke PostgreSQL
- Rule engine dan Virtual Soil Sensor sebagai baseline yang eksplisit, tanpa fake computer vision
- AI provider abstraction, feature versioning, confidence engine, XAI evidence, image quality,
  model manifest/checksum, ML trend/anomaly/ensemble primitives, dan backup integrity
- Runtime CPU nyata: PyTorch, torchvision, Ultralytics YOLO, ONNX Runtime, OpenCV,
  scikit-learn, Transformers, SHAP, dan LIME

Komponen vision/ML berat bersifat modular. Jika model belum diinstal, sistem menampilkan
`NOT_INSTALLED` atau `INSUFFICIENT_DATA`; sistem tidak mengarang diagnosis, confidence, atau
pengukuran foto.

## Menjalankan

```bash
cd web
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env
flask --app run.py run --debug
```

Buka `http://127.0.0.1:5000`, buat akun, lalu buka salah satu dari 12 pohon awal.
Untuk production PostgreSQL, set `DATABASE_URL` ke URL `postgresql+psycopg://...`.

## Migrasi dan tes

```bash
flask --app run.py db init
flask --app run.py db migrate -m "initial schema"
flask --app run.py db upgrade
pytest
```

Startup membuat schema/seed secara aman untuk development ketika `AUTO_CREATE_SCHEMA=1`.
Untuk production, set `AUTO_CREATE_SCHEMA=0`, jalankan migrasi, lalu seed data secara eksplisit:

```bash
flask --app run.py db upgrade
flask --app run.py seed-data
```

Migrasi produksi tidak menghapus database. Model visual belum tersedia; UI menyatakan
keterbatasan tersebut dan tidak mengarang prediksi foto.

Developer diagnostics tersedia setelah login di `/developer/diagnostics.json`.
Model lokal YOLO11 Nano tersedia di `instance/models/yolo11n.pt` dan digunakan hanya untuk
object detection umum. Hasilnya bukan diagnosis pertanian; foto yang lolos quality gate
dicatat sebagai provenance `COMPUTER_VISION`.

Model pack lokal yang tersedia:

- YOLO11 Nano: object detection
- MobileNetV3 Large: klasifikasi ImageNet umum
- MobileNetV3 Large backbone: embedding visual umum
- DeepLabV3 MobileNetV3 Large: semantic segmentation umum

Semua model disimpan di `instance/models` dan memiliki manifest SHA-256 di
`model_manifests`. Model-model umum tersebut tidak boleh dipresentasikan sebagai diagnosis
hama, penyakit, atau ukuran agronomi rambutan tanpa dataset dan evaluasi pertanian khusus.

## Lembar kerja analis kebun

Antarmuka web menggunakan istilah kerja lapangan: register pohon, identitas
petak, timeline tanaman, kondisi vegetatif, pertumbuhan, fase produktif,
perlindungan tanaman, perawatan, dan hasil panen. Skema longitudinal mencatat
posisi baris/kolom, jarak tanam, tanggal tanam, baseline ukuran, kondisi zona
akar, pemadatan/drainase tanah, genangan, mulsa, ukuran tajuk, cabang primer,
aktivitas bunga, kerontokan buah, bagian tanaman yang terdampak, penyebaran
hama/penyakit, serta kepadatan dan metode pengendalian gulma.

Field tambahan tersebut berada pada migration
`a1b2c3d4e5f6_add_professional_agronomic_fields.py` dan dapat diterapkan tanpa
menghapus database:

```bash
flask --app run.py db upgrade
```
Untuk database development yang dibuat dengan `AUTO_CREATE_SCHEMA=1`, sinkronkan marker
migrasi satu kali tanpa menghapus data:

```bash
flask --app run.py db stamp head
flask --app run.py db check
```
