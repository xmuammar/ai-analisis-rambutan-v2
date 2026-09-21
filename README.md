# AiAnalisRambutan Web

Versi web full-stack Python Flask untuk domain yang sama dengan aplikasi mobile di `mobile/`.
Source web sepenuhnya berada di direktori ini dan tidak memakai Django, React, Vue, Next.js,
Flutter Web, atau Node.js sebagai application server.

## Stack

- Flask application factory + Jinja2
- SQLAlchemy dan Flask-Migrate (Alembic)
- Flask-WTF untuk form/CSRF
- Flask-Login untuk autentikasi lokal
- PostgreSQL sebagai database runtime versi 2; SQLite hanya dipakai untuk test dan sumber ETL legacy
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
Untuk production PostgreSQL, set `DATABASE_URL` ke URL
`postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE`. Driver `psycopg[binary]`
sudah ada di `requirements.txt`; jangan memasukkan password ke repository.

## Migrasi dan tes

```bash
flask --app run.py db init
flask --app run.py db migrate -m "initial schema"
flask --app run.py db upgrade
pytest
```

Startup hanya membuat schema otomatis untuk SQLite development. Untuk PostgreSQL,
`AUTO_CREATE_SCHEMA` otomatis bernilai `0`; jalankan migrasi dan seed secara eksplisit:

```bash
flask --app run.py db upgrade
flask --app run.py seed-data
```

### Migrasi PostgreSQL versi 2

Gunakan database kosong atau salinan database staging terlebih dahulu. Pastikan user
PostgreSQL memiliki hak `CONNECT`, `CREATE` pada database, dan `USAGE, CREATE` pada
schema target. Contoh:

```bash
createdb ai_rambutan
export DATABASE_URL='postgresql+psycopg://app_user:password@localhost:5432/ai_analis_rambutan'
export AUTO_CREATE_SCHEMA=0
flask --app run.py db current
flask --app run.py db upgrade
flask --app run.py seed-data
flask --app run.py db check
```

Jika role aplikasi belum memiliki hak schema, administrator dapat menjalankan
`scripts/grant_postgres_app_privileges.sql` pada database target:

```bash
psql -h 127.0.0.1 -U postgres -d ai_rambutan \
  -f scripts/grant_postgres_app_privileges.sql
```

Migration `b2c3d4e5f6a7_add_v2_agronomic_assessment.py` menambahkan tabel
`agronomic_assessment`. Payload JSON versi `2.0` menyimpan hasil assessment
konservatif lengkap, provenance, confidence, kebutuhan konfirmasi, risiko,
pengukuran lanjutan, dan batasan diagnosis. Migration tidak menghapus data lama.

Sebelum cutover produksi:

1. Backup database sumber dan uji restore.
2. Jalankan `flask db upgrade` pada staging PostgreSQL.
3. Verifikasi jumlah baris pada tabel longitudinal dan `agronomic_assessment`.
4. Jalankan smoke test login, inspeksi foto, backup JSON, dan seed.
5. Hentikan penulisan ke sumber saat migrasi data, lalu verifikasi ulang checksum dan jumlah baris.

Untuk memindahkan data SQLite lama, gunakan dump terkontrol (ETL atau `pgloader`),
bukan menyalin file `.sqlite3` ke server PostgreSQL. Setelah data dipindahkan,
set marker Alembic sesuai histori sumber hanya jika seluruh migration sudah diterapkan:

```bash
flask --app run.py db stamp head
flask --app run.py db check
```

Repository juga menyediakan ETL terkontrol untuk migrasi ke database PostgreSQL
kosong. Perintah pertama hanya membaca dan menghitung baris:

```bash
PYTHONPATH=. .venv/bin/python scripts/migrate_sqlite_to_postgres.py \
  --source sqlite:///instance/ai_analis_rambutan.sqlite3 \
  --target "$DATABASE_URL"
```

Setelah backup dan verifikasi staging, jalankan dengan `--apply`. Tool menolak
target yang tidak kosong, tidak pernah menggabungkan baris, mempertahankan ID
dan kolom yang tersedia, serta mengatur ulang sequence PostgreSQL:

```bash
PYTHONPATH=. .venv/bin/python scripts/migrate_sqlite_to_postgres.py \
  --source sqlite:///instance/ai_analis_rambutan.sqlite3 \
  --target "$DATABASE_URL" --apply
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
## Laporan dan analitik profesional

Menu **Laporan** membaca assessment v2 terbaru dari PostgreSQL dan menyediakan
ringkasan per pohon, tabel parameter lengkap, screening konservatif, risiko,
quality control, serta payload JSON asli. Laporan dapat diunduh sebagai:

- **Excel** (`/reports/export.xlsx`) untuk analisis lanjutan dan penyaringan data.
- **PDF** (`/reports/export.pdf`) untuk arsip dan distribusi lapangan.

Menu **Analitik** (`/analytics`) menampilkan cakupan assessment, rata-rata
confidence parameter (bukan skor kesehatan), distribusi status visual, level
risiko, dan daftar prioritas verifikasi. Grafik digunakan sebagai alat bantu
keputusan; analis tetap perlu mengonfirmasi kondisi tanah, ukuran pohon, hama,
dan penyakit melalui pemeriksaan lapangan.
