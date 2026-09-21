from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import (
    BooleanField,
    FloatField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, EqualTo, Length, Optional


class LoginForm(FlaskForm):
    username = StringField("Nama pengguna", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Kata sandi", validators=[DataRequired()])
    submit = SubmitField("Masuk")


class RegisterForm(FlaskForm):
    username = StringField(
        "Nama pengguna", validators=[DataRequired(), Length(min=3, max=80)]
    )
    password = PasswordField(
        "Kata sandi", validators=[DataRequired(), Length(min=8, max=128)]
    )
    password_confirm = PasswordField(
        "Ulangi kata sandi", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Buat akun")


class InspectionForm(FlaskForm):
    mode = HiddenField(default="PHOTO_FIRST")
    surface_dark = BooleanField("Permukaan tanah terlihat gelap")
    standing_water = BooleanField("Terlihat genangan")
    leaf_wilt = BooleanField("Daun tampak layu")
    soil_moisture_visual = SelectField(
        "Kelembapan visual tanah",
        choices=[
            ("", "Belum ditentukan"),
            ("VERY_DRY", "Sangat kering"),
            ("DRY", "Kering"),
            ("SLIGHTLY_DRY", "Agak kering"),
            ("MOIST", "Lembap"),
            ("VERY_MOIST", "Sangat lembap"),
            ("WATERLOGGED", "Tergenang"),
        ],
        validators=[Optional()],
    )
    soil_surface_condition = SelectField(
        "Kondisi permukaan tanah",
        choices=[
            ("", "Belum ditentukan"),
            ("DARK", "Gelap/lembap"),
            ("DRY", "Kering/terang"),
            ("MUDDY", "Berlumpur"),
            ("CRUSTED", "Berkerak"),
            ("MULCHED", "Tertutup mulsa"),
        ],
        validators=[Optional()],
    )
    soil_compaction = SelectField(
        "Pemadatan tanah",
        choices=[
            ("", "Belum ditentukan"),
            ("LOW", "Rendah"),
            ("MEDIUM", "Sedang"),
            ("HIGH", "Tinggi"),
        ],
        validators=[Optional()],
    )
    soil_drainage = SelectField(
        "Drainase zona akar",
        choices=[
            ("", "Belum ditentukan"),
            ("GOOD", "Baik"),
            ("MODERATE", "Sedang"),
            ("POOR", "Buruk"),
        ],
        validators=[Optional()],
    )
    standing_water_depth_cm = FloatField(
        "Kedalaman genangan (cm)", validators=[Optional()]
    )
    visible_cracks = BooleanField("Retakan permukaan terlihat")
    mulch_present = BooleanField("Mulsa tersedia")
    height_cm = FloatField("Tinggi pohon (cm)", validators=[Optional()])
    stem_diameter_cm = FloatField("Diameter batang (cm)", validators=[Optional()])
    canopy_width_cm = FloatField("Lebar tajuk (cm)", validators=[Optional()])
    canopy_height_cm = FloatField("Tinggi tajuk (cm)", validators=[Optional()])
    canopy_ns_cm = FloatField("Lebar tajuk utara–selatan (cm)", validators=[Optional()])
    canopy_ew_cm = FloatField("Lebar tajuk timur–barat (cm)", validators=[Optional()])
    primary_branch_count = IntegerField("Jumlah cabang primer", validators=[Optional()])
    flower_present = BooleanField("Bunga terlihat")
    flower_stage = SelectField(
        "Tahap bunga",
        choices=[
            ("", "Belum ditentukan"),
            ("BUD", "Kuncup"),
            ("EARLY_FLOWERING", "Awal berbunga"),
            ("FLOWERING", "Berbunga"),
            ("FULL_BLOOM", "Mekar penuh"),
            ("FINISHING", "Selesai berbunga"),
        ],
        validators=[Optional()],
    )
    fruit_present = BooleanField("Buah terlihat")
    fruit_stage = SelectField(
        "Tahap buah",
        choices=[
            ("", "Belum ditentukan"),
            ("FRUIT_SET", "Fruit set"),
            ("YOUNG", "Muda"),
            ("DEVELOPING", "Berkembang"),
            ("NEAR_RIPE", "Hampir matang"),
            ("RIPE", "Matang"),
        ],
        validators=[Optional()],
    )
    fruit_count_estimate = IntegerField(
        "Perkiraan jumlah buah", validators=[Optional()]
    )
    fruit_damage_percent = FloatField("Kerusakan buah (%)", validators=[Optional()])
    fruit_drop_count = IntegerField("Jumlah buah rontok", validators=[Optional()])
    fruit_drop_level = SelectField(
        "Tingkat kerontokan buah",
        choices=[
            ("", "Belum ditentukan"),
            ("NONE", "Tidak ada"),
            ("LOW", "Rendah"),
            ("MEDIUM", "Sedang"),
            ("HIGH", "Tinggi"),
        ],
        validators=[Optional()],
    )
    fruit_color = SelectField(
        "Warna buah dominan",
        choices=[
            ("", "Belum ditentukan"),
            ("GREEN", "Hijau"),
            ("YELLOW_GREEN", "Hijau kekuningan"),
            ("RED", "Merah"),
            ("DARK_RED", "Merah tua"),
            ("BROWN", "Cokelat"),
        ],
        validators=[Optional()],
    )
    ripeness = SelectField(
        "Kematangan buah",
        choices=[
            ("", "Belum ditentukan"),
            ("UNRIPE", "Belum matang"),
            ("NEAR_RIPE", "Hampir matang"),
            ("RIPE", "Matang"),
        ],
        validators=[Optional()],
    )
    pest_present = BooleanField("Hama terlihat")
    pest_type = SelectField(
        "Kategori hama",
        choices=[
            ("", "Belum ditentukan"),
            ("INSECT", "Serangga"),
            ("MITE", "Tungau"),
            ("CATERPILLAR", "Ulat"),
            ("SAP_SUCKER", "Pengisap cairan"),
            ("UNKNOWN", "Belum teridentifikasi"),
        ],
        validators=[Optional()],
    )
    pest_affected_part = SelectField(
        "Bagian tanaman terdampak hama",
        choices=[
            ("", "Belum ditentukan"),
            ("LEAF", "Daun"),
            ("SHOOT", "Tunas"),
            ("STEM", "Batang/cabang"),
            ("FLOWER", "Bunga"),
            ("FRUIT", "Buah"),
        ],
        validators=[Optional()],
    )
    pest_spread = SelectField(
        "Penyebaran hama",
        choices=[
            ("", "Belum ditentukan"),
            ("LOCAL", "Lokal"),
            ("SCATTERED", "Terpencar"),
            ("WIDESPREAD", "Menyebar"),
        ],
        validators=[Optional()],
    )
    disease_present = BooleanField("Gejala penyakit terlihat")
    disease_type = SelectField(
        "Kategori penyakit",
        choices=[
            ("", "Belum ditentukan"),
            ("FUNGAL", "Gejala jamur"),
            ("BACTERIAL", "Gejala bakteri"),
            ("VIRAL_LIKE", "Gejala mirip virus"),
            ("PHYSIOLOGICAL", "Gangguan fisiologis"),
            ("UNKNOWN", "Belum teridentifikasi"),
        ],
        validators=[Optional()],
    )
    disease_affected_part = SelectField(
        "Bagian tanaman terdampak penyakit",
        choices=[
            ("", "Belum ditentukan"),
            ("LEAF", "Daun"),
            ("SHOOT", "Tunas"),
            ("STEM", "Batang/cabang"),
            ("FLOWER", "Bunga"),
            ("FRUIT", "Buah"),
        ],
        validators=[Optional()],
    )
    disease_spread = SelectField(
        "Penyebaran penyakit",
        choices=[
            ("", "Belum ditentukan"),
            ("LOCAL", "Lokal"),
            ("SCATTERED", "Terpencar"),
            ("WIDESPREAD", "Menyebar"),
        ],
        validators=[Optional()],
    )
    weed_level = SelectField(
        "Tingkat gulma",
        choices=[
            ("", "Belum ditentukan"),
            ("NONE", "Tidak ada"),
            ("LOW", "Rendah"),
            ("MEDIUM", "Sedang"),
            ("HIGH", "Tinggi"),
        ],
        validators=[Optional()],
    )
    weed_coverage_percent = FloatField("Tutupan gulma (%)", validators=[Optional()])
    weed_density = SelectField(
        "Kepadatan gulma",
        choices=[
            ("", "Belum ditentukan"),
            ("LOW", "Rendah"),
            ("MEDIUM", "Sedang"),
            ("HIGH", "Tinggi"),
        ],
        validators=[Optional()],
    )
    weed_height_cm = FloatField("Tinggi gulma (cm)", validators=[Optional()])
    weed_removed = BooleanField("Gulma sudah dikendalikan")
    weed_removal_method = StringField(
        "Metode pengendalian gulma", validators=[Optional(), Length(max=80)]
    )
    notes = TextAreaField(
        "Catatan pemeriksa", validators=[Optional(), Length(max=5000)]
    )
    photos = MultipleFileField(
        "Foto pemeriksaan",
        validators=[
            FileAllowed(["jpg", "jpeg", "png", "webp"], "Format foto tidak didukung.")
        ],
    )
    ai_analysis = HiddenField()
    submit = SubmitField("Simpan pemeriksaan")
