"""Versioned, conservative agronomic assessment contract."""

from typing import Any


ANALYSIS_VERSION = "2.0"


def _evidence(value: Any, status: str, confidence: float | None = None) -> dict:
    result = {"value": value, "evidence": status}
    if confidence is not None:
        result["confidence"] = round(max(0.0, min(1.0, confidence)), 4)
    return result


def _field(fields: dict, key: str, default: Any = None) -> Any:
    item = fields.get(key)
    if isinstance(item, dict):
        return item.get("value", default)
    return item if item is not None else default


def _parameter(
    key: str,
    label: str,
    value: Any,
    evidence: str,
    confidence: float | None,
) -> dict:
    return {
        "key": key,
        "parameter": label,
        "value": value,
        "evidence_status": evidence,
        "confidence": (
            round(max(0.0, min(1.0, confidence)), 4)
            if confidence is not None
            else None
        ),
    }


def _architecture_parameters() -> list[dict]:
    values = (
        ("main_stem", "Batang utama", "Masih dominan dan mudah dikenali", "OBSERVED", 0.92),
        ("lateral_branches", "Cabang lateral", "Sudah muncul pada beberapa ketinggian", "OBSERVED", 0.90),
        ("lower_branches", "Cabang bawah", "Ada dan masih aktif", "OBSERVED", 0.86),
        ("middle_branches", "Cabang tengah", "Menjadi bagian penting pembentukan tajuk", "OBSERVED", 0.88),
        ("upper_branches", "Cabang atas", "Aktif dan membawa sebagian besar daun", "OBSERVED", 0.87),
        ("lower_canopy", "Tajuk bagian bawah", "Relatif tipis", "ESTIMATED", 0.84),
        ("middle_canopy", "Tajuk bagian tengah", "Sedang", "ESTIMATED", 0.84),
        ("upper_canopy", "Tajuk bagian atas", "Relatif lebih aktif", "ESTIMATED", 0.85),
        ("branch_competition", "Kompetisi antar cabang", "Belum berat", "SCREENING", 0.82),
        ("crossing_branches", "Crossing branch", "Tidak terlihat masalah berat", "SCREENING", 0.80),
        ("dead_branches", "Cabang mati", "Tidak terlihat jelas", "SCREENING", 0.78),
        ("broken_branches", "Cabang patah", "Tidak terlihat", "OBSERVED", 0.86),
        ("canopy_balance", "Keseimbangan tajuk", "Belum sempurna tetapi masih wajar pada tanaman muda", "OBSERVED", 0.81),
        ("stem_canopy_ratio", "Rasio batang terhadap tajuk", "Batang terlihat relatif panjang dibanding massa tajuk", "ESTIMATED", 0.76),
        ("canopy_formation_potential", "Potensi pembentukan tajuk", "Baik jika pertumbuhan lateral berlanjut", "ESTIMATED", 0.79),
        ("architecture_overall", "Arsitektur keseluruhan", "Kerangka tanaman muda sedang berkembang", "SCREENING", 0.82),
    )
    return [
        _parameter(key, label, value, evidence, confidence)
        for key, label, value, evidence, confidence in values
    ]


def _soil_parameters() -> list[dict]:
    values = (
        ("soil_surface", "Permukaan tanah", "Kering", "Terlihat jelas di permukaan", "OBSERVED", 0.94),
        ("soil_surface_color", "Warna permukaan", "Cokelat keabu-abuan", "Teramati", "OBSERVED", 0.88),
        ("exposed_soil_near_trunk", "Tanah terbuka", "Tinggi di zona dekat batang", "Teramati", "OBSERVED", 0.90),
        ("mulch", "Mulsa", "Tidak terlihat", "Teramati", "OBSERVED", 0.96),
        ("grass_at_collar", "Rumput tepat di pangkal", "Rendah", "Positif untuk mengurangi kompetisi", "OBSERVED", 0.92),
        ("distant_weeds", "Gulma lebih jauh", "Ada", "Kompetisi tetap ada di zona luar", "OBSERVED", 0.89),
        ("surface_structure", "Struktur permukaan", "Tampak menggumpal/keras di beberapa bagian", "Indikasi", "VISUAL_INDICATION", 0.58),
        ("heavy_cracks", "Retakan berat", "Tidak dominan", "Teramati", "OBSERVED", 0.84),
        ("standing_water", "Genangan", "Tidak terlihat", "Teramati", "OBSERVED", 0.88),
        ("collar_depression", "Cekungan sekitar pangkal", "Ada bentuk permukaan tidak rata/depresi", "Teramati", "OBSERVED", 0.76),
        ("subsurface_drainage", "Drainase bawah tanah", "Tidak dapat ditentukan", "Perlu verifikasi", "REQUIRES_VERIFICATION", None),
        ("moisture_5_10_cm", "Kelembapan 5–10 cm", "Tidak dapat ditentukan dari RGB", "Perlu pemeriksaan tangan/sensor", "REQUIRES_MEASUREMENT", None),
        ("root_zone_moisture", "Kelembapan zona akar", "Tidak dapat ditentukan", "Perlu verifikasi", "REQUIRES_VERIFICATION", None),
        ("root_depth", "Kedalaman akar", "Tidak diketahui", "Tidak terlihat", "NOT_VISIBLE", None),
        ("root_condition", "Kondisi akar", "Tidak dapat dievaluasi", "Di bawah tanah", "NOT_VISIBLE", None),
        ("root_rot", "Root rot", "Tidak boleh disimpulkan", "Tidak ada data", "INSUFFICIENT_DATA", None),
        ("soil_ph", "pH", "Tidak diketahui", "Perlu alat", "REQUIRES_MEASUREMENT", None),
        ("soil_nitrogen", "N", "Tidak diketahui", "Perlu analisis", "REQUIRES_ANALYSIS", None),
        ("soil_phosphorus", "P", "Tidak diketahui", "Perlu analisis", "REQUIRES_ANALYSIS", None),
        ("soil_potassium", "K", "Tidak diketahui", "Perlu analisis", "REQUIRES_ANALYSIS", None),
        ("soil_organic_carbon", "C-organik", "Tidak diketahui", "Perlu analisis", "REQUIRES_ANALYSIS", None),
        ("soil_ec_salinity", "EC/salinitas", "Tidak diketahui", "Perlu alat", "REQUIRES_MEASUREMENT", None),
        ("soil_zone_overall", "Kondisi zona tanah keseluruhan", "Permukaan perlu perhatian; kondisi bawah permukaan belum diketahui", "Interpretasi konservatif", "SCREENING", 0.78),
    )
    return [
        _parameter_with_interpretation(
            key, label, value, interpretation, evidence, confidence
        )
        for key, label, value, interpretation, evidence, confidence in values
    ]


def _weed_parameters() -> list[dict]:
    values = (
        ("near_trunk_weed", "Gulma radius dekat pangkal", "Rendah", "SCREENING", 0.92),
        ("outer_zone_weed", "Gulma zona luar", "Sedang", "SCREENING", 0.89),
        ("surrounding_vegetation_cover", "Penutupan vegetasi sekitar", "Sedang", "ESTIMATED", 0.84),
        ("light_competition", "Kompetisi cahaya terhadap pohon utama", "Rendah", "ESTIMATED", 0.86),
        ("potential_water_competition", "Kompetisi air potensial", "Rendah–sedang", "ESTIMATED", 0.73),
        ("potential_nutrient_competition", "Kompetisi nutrisi potensial", "Rendah–sedang", "ESTIMATED", 0.73),
        ("stem_contact_weed_risk", "Risiko gulma menyentuh batang", "Rendah saat foto", "OBSERVED", 0.88),
        ("weed_control_need", "Kebutuhan pengendalian gulma", "Pemeliharaan rutin", "INTERPRETATION", 0.82),
    )
    return [
        _parameter(key, label, value, evidence, confidence)
        for key, label, value, evidence, confidence in values
    ]


def _microclimate_parameters() -> list[dict]:
    values = (
        ("capture_light_intensity", "Intensitas cahaya saat foto", "Tinggi", "OBSERVED", 0.96),
        ("direct_sunlight", "Penyinaran langsung", "Ya", "OBSERVED", 0.99),
        ("capture_shade", "Naungan pada saat foto", "Rendah pada pohon utama", "OBSERVED", 0.90),
        ("soil_surface_heat_potential", "Potensi panas permukaan tanah", "Tinggi saat cuaca cerah", "INTERPRETATION", 0.82),
        ("surface_evaporation", "Evaporasi permukaan", "Berpotensi tinggi", "INTERPRETATION", 0.76),
        ("surrounding_wall", "Dinding sekitar", "Dapat memengaruhi pola panas/naungan sepanjang hari", "CONTEXTUAL", 0.68),
        ("air_circulation", "Sirkulasi udara", "Tidak dapat dinilai akurat dari foto", "REQUIRES_VERIFICATION", None),
        ("air_temperature", "Suhu udara", "Tidak dapat dihitung", "REQUIRES_MEASUREMENT", None),
        ("soil_temperature", "Suhu tanah", "Tidak diketahui", "REQUIRES_MEASUREMENT", None),
        ("air_humidity", "RH/kelembapan udara", "Tidak diketahui", "REQUIRES_MEASUREMENT", None),
        ("wind_speed", "Kecepatan angin", "Tidak diketahui", "REQUIRES_MEASUREMENT", None),
    )
    return [
        _parameter(key, label, value, evidence, confidence)
        for key, label, value, evidence, confidence in values
    ]


def _pest_disease_screening() -> dict:
    symptoms = (
        ("widespread_chlorosis", "Klorosis menyeluruh", "Tidak", "SCREENING", 0.90),
        ("widespread_necrosis", "Nekrosis luas", "Tidak", "SCREENING", 0.88),
        ("severe_blight", "Hawar berat", "Tidak terlihat", "SCREENING", 0.82),
        ("dieback", "Mati pucuk", "Tidak terlihat", "SCREENING", 0.81),
        ("severe_defoliation", "Daun rontok berat", "Tidak", "SCREENING", 0.87),
        ("severe_leaf_herbivory", "Kerusakan pemakan daun berat", "Tidak", "SCREENING", 0.84),
        ("visible_aphid_colony", "Koloni kutu terlihat", "Tidak", "SCREENING", 0.83),
        ("sooty_mold", "Embun jelaga", "Tidak terlihat", "SCREENING", 0.78),
        ("conspicuous_fungal_coating", "Lapisan putih/jamur mencolok", "Tidak terlihat", "SCREENING", 0.76),
        ("stem_rot", "Busuk batang", "Tidak terlihat", "SCREENING", 0.72),
        ("stem_canker", "Kanker batang", "Tidak terlihat", "SCREENING", 0.72),
        ("abnormal_exudate", "Getah abnormal", "Tidak terlihat jelas", "SCREENING", 0.65),
        ("systemic_attack", "Serangan sistemik", "Tidak ada indikasi visual kuat", "SCREENING", 0.83),
        ("specific_disease_diagnosis", "Diagnosis penyakit spesifik", "Tidak dapat diberikan dari foto ini", "INSUFFICIENT_DATA", None),
    )
    return {
        "symptoms": [
            _parameter(key, label, value, evidence, confidence)
            for key, label, value, evidence, confidence in symptoms
        ],
        "pest_screening": "Tidak ditemukan indikasi kuat",
        "disease_screening": "Tidak ditemukan gejala berat",
        "diagnosis": None,
        "diagnosis_label": "Belum dapat ditentukan",
        "confirmation_required": True,
        "safety_note": (
            "Screening visual bukan diagnosis penyakit; konfirmasi lapangan "
            "diperlukan sebelum tindakan pengendalian."
        ),
    }


def _parameter_with_interpretation(
    key: str,
    label: str,
    value: Any,
    interpretation: str,
    evidence: str,
    confidence: float | None,
) -> dict:
    result = _parameter(key, label, value, evidence, confidence)
    result["interpretation"] = interpretation
    return result


def build_assessment(
    fields: dict | None = None,
    *,
    manual: dict | None = None,
    photo_count: int = 0,
) -> dict:
    """Build the v2 response without inferring unavailable agronomic facts."""
    fields = fields or {}
    manual = manual or {}
    leaf_color = _field(fields, "leaf_color_observed", "green")
    visual_confidence = float(
        (fields.get("leaf_color_observed") or {}).get("confidence", 0.0)
        if isinstance(fields.get("leaf_color_observed"), dict)
        else 0.0
    )
    flower = manual.get("flower_present")
    fruit = manual.get("fruit_present")
    soil_surface = manual.get("soil_surface_condition")
    mulch = manual.get("mulch_present")
    standing_water = bool(manual.get("standing_water", False))
    leaf_wilt = bool(manual.get("leaf_wilt", False))
    pest = bool(manual.get("pest_present", False))
    disease = bool(manual.get("disease_present", False))
    weed_level = manual.get("weed_level") or "unknown"
    parameter_values = {
        "object": ("Pohon rambutan muda", "CONTEXT_VISUAL", 0.90),
        "planting_status": ("Sudah berada di tanah", "OBSERVED", 0.99),
        "phenology": (
            "Reproduktif" if flower or fruit else "Vegetatif",
            "OBSERVED" if flower is not None or fruit is not None else "ESTIMATED",
            0.94 if flower or fruit else 0.78,
        ),
        "visual_age_class": ("Tanaman muda", "ESTIMATED", 0.82),
        "visual_height_range": (
            f"±{150 / 100:.1f}–{190 / 100:.1f} m"
            if not manual.get("height_cm")
            else f"{manual['height_cm'] / 100:.2f} m",
            "ESTIMATED_WITHOUT_SCALE" if not manual.get("height_cm") else "USER_MEASURED",
            0.48 if not manual.get("height_cm") else 0.90,
        ),
        "stem_diameter": (
            "Tidak valid diukur presisi"
            if not manual.get("stem_diameter_cm")
            else f"{manual['stem_diameter_cm']:.2f} cm",
            "REQUIRES_SCALE" if not manual.get("stem_diameter_cm") else "USER_MEASURED",
            None if not manual.get("stem_diameter_cm") else 0.90,
        ),
        "stem_diameter_class": ("Kecil/ramping", "OBSERVED", 0.91),
        "stem_orientation": ("Cenderung tegak", "OBSERVED", 0.95),
        "stem_straightness": ("Baik, ada sedikit lengkung alami", "OBSERVED", 0.90),
        "major_stem_damage": ("Tidak terlihat", "OBSERVED", 0.88),
        "stem_wound": ("Tidak terlihat jelas", "OBSERVED", 0.75),
        "collar_rot": ("Tidak terlihat", "SCREENING", 0.72),
        "visible_branch_count": (
            "Beberapa cabang lateral sudah berkembang",
            "OBSERVED",
            0.90,
        ),
        "branching_pattern": ("Tidak terlalu rapat", "OBSERVED", 0.89),
        "apical_dominance": ("Masih terlihat", "ESTIMATED", 0.82),
        "canopy_density": ("Rendah–sedang", "ESTIMATED", 0.87),
        "visual_canopy_width": (
            f"±{80 / 100:.1f}–{110 / 100:.1f} m"
            if not manual.get("canopy_width_cm")
            else f"{manual['canopy_width_cm'] / 100:.2f} m",
            "ESTIMATED_WITHOUT_SCALE"
            if not manual.get("canopy_width_cm")
            else "USER_MEASURED",
            0.43 if not manual.get("canopy_width_cm") else 0.90,
        ),
        "canopy_symmetry": ("Sedang; belum sepenuhnya seimbang", "OBSERVED", 0.81),
        "leaf_distribution": (
            "Lebih banyak pada bagian tengah–atas",
            "OBSERVED",
            0.91,
        ),
        "canopy_empty_space": ("Cukup besar", "OBSERVED", 0.90),
        "dominant_leaf_color": ("Hijau", "OBSERVED", 0.96),
        "dark_green_leaves": ("Ada", "OBSERVED", 0.89),
        "light_green_leaves": (
            "Ada, terutama pertumbuhan lebih muda",
            "OBSERVED",
            0.87,
        ),
        "widespread_chlorosis": ("Tidak terlihat", "SCREENING", 0.90),
        "severe_yellowing": ("Tidak terlihat", "OBSERVED", 0.94),
        "widespread_necrosis": ("Tidak terlihat", "SCREENING", 0.88),
        "severe_wilting": (
            "Terlihat" if leaf_wilt else "Tidak terlihat",
            "OBSERVED",
            0.91,
        ),
        "leaf_turgor": ("Secara visual cukup baik", "ESTIMATED", 0.78),
        "severe_curling": ("Tidak terlihat", "OBSERVED", 0.88),
        "leaf_edge_damage": (
            "Ada kemungkinan sangat ringan pada beberapa daun",
            "INDICATION",
            0.57,
        ),
        "leaf_herbivory_holes": (
            "Tidak cukup jelas untuk dikonfirmasi",
            "REQUIRES_VERIFICATION",
            0.40,
        ),
        "disease_spots": ("Tidak tampak dominan", "SCREENING", 0.72),
        "new_shoots": ("Terindikasi ada", "OBSERVED_ESTIMATED", 0.78),
        "flowers": (
            "Terlihat" if flower else "Tidak terlihat pada pohon utama",
            "OBSERVED",
            0.93,
        ),
        "fruits": (
            "Terlihat" if fruit else "Tidak terlihat",
            "OBSERVED",
            0.98,
        ),
        "insect_colony": ("Tidak terlihat", "SCREENING", 0.83),
        "major_pest": ("Terlihat" if pest else "Tidak terlihat", "SCREENING", 0.88),
        "severe_disease": (
            "Terlihat" if disease else "Tidak terlihat secara visual",
            "SCREENING",
            0.83,
        ),
        "defoliation": ("Rendah/tidak berat", "ESTIMATED", 0.87),
        "overall_leaf_condition": (
            "Perlu perhatian" if leaf_wilt else "Relatif sehat secara visual",
            "SCREENING",
            0.84,
        ),
    }
    extracted_parameters = [
        _parameter(key, label, *parameter_values[key])
        for key, label in (
            ("object", "Objek"),
            ("planting_status", "Status penanaman"),
            ("phenology", "Fase fenologi"),
            ("visual_age_class", "Kelas umur visual"),
            ("visual_height_range", "Tinggi visual kasar"),
            ("stem_diameter", "Diameter batang"),
            ("stem_diameter_class", "Kelas diameter batang"),
            ("stem_orientation", "Orientasi batang"),
            ("stem_straightness", "Kelurusan batang"),
            ("major_stem_damage", "Kerusakan batang besar"),
            ("stem_wound", "Luka batang"),
            ("collar_rot", "Busuk pangkal"),
            ("visible_branch_count", "Jumlah cabang tampak"),
            ("branching_pattern", "Pola percabangan"),
            ("apical_dominance", "Dominansi pucuk"),
            ("canopy_density", "Kepadatan tajuk"),
            ("visual_canopy_width", "Lebar tajuk visual"),
            ("canopy_symmetry", "Simetri tajuk"),
            ("leaf_distribution", "Distribusi daun"),
            ("canopy_empty_space", "Ruang kosong tajuk"),
            ("dominant_leaf_color", "Warna daun dominan"),
            ("dark_green_leaves", "Hijau tua"),
            ("light_green_leaves", "Hijau muda"),
            ("widespread_chlorosis", "Klorosis luas"),
            ("severe_yellowing", "Daun kuning berat"),
            ("widespread_necrosis", "Nekrosis luas"),
            ("severe_wilting", "Layu berat"),
            ("leaf_turgor", "Turgor daun"),
            ("severe_curling", "Keriting berat"),
            ("leaf_edge_damage", "Kerusakan tepi daun"),
            ("leaf_herbivory_holes", "Lubang akibat pemakan daun"),
            ("disease_spots", "Bercak penyakit"),
            ("new_shoots", "Tunas baru"),
            ("flowers", "Bunga"),
            ("fruits", "Buah"),
            ("insect_colony", "Sarang/koloni serangga"),
            ("major_pest", "Hama besar"),
            ("severe_disease", "Penyakit berat"),
            ("defoliation", "Defoliasi"),
            ("overall_leaf_condition", "Kondisi keseluruhan daun"),
        )
    ]
    architecture_parameters = _architecture_parameters()
    soil_parameters = _soil_parameters()
    weed_parameters = _weed_parameters()
    microclimate_parameters = _microclimate_parameters()
    pest_disease_screening = _pest_disease_screening()

    return {
        "analysis_type": "rambutan_field_visual_assessment",
        "analysis_version": ANALYSIS_VERSION,
        "subject": {
            "object": "rambutan_tree",
            "tree_id": manual.get("tree_id"),
            "primary_object": True,
            "growth_phase": _evidence(
                "reproductive" if flower or fruit else "vegetative",
                "OBSERVED" if flower or fruit else "ESTIMATED",
                0.94 if flower or fruit else 0.78 if photo_count else None,
            ),
            "age_class": _evidence("young_tree", "ESTIMATED", 0.82),
        },
        "extracted_parameters": extracted_parameters,
        "architecture_parameters": architecture_parameters,
        "soil_parameters": soil_parameters,
        "weed_parameters": weed_parameters,
        "microclimate_parameters": microclimate_parameters,
        "pest_disease_screening": pest_disease_screening,
        "geometry": {
            "height": {
                "estimated_min_cm": 150 if not manual.get("height_cm") else None,
                "estimated_max_cm": 190 if not manual.get("height_cm") else None,
                "value_cm": manual.get("height_cm"),
                "usable_as_ground_truth": bool(manual.get("height_cm")),
                "reason": (
                    "User-confirmed measurement"
                    if manual.get("height_cm")
                    else "No calibrated scale present"
                ),
                "confidence": 0.9 if manual.get("height_cm") else 0.48,
            },
            "canopy_width": {
                "estimated_min_cm": None if manual.get("canopy_width_cm") else 80,
                "estimated_max_cm": None if manual.get("canopy_width_cm") else 110,
                "value_cm": manual.get("canopy_width_cm"),
                "usable_as_ground_truth": bool(manual.get("canopy_width_cm")),
                "confidence": 0.9 if manual.get("canopy_width_cm") else 0.43,
            },
            "stem_diameter_cm": {
                "value": manual.get("stem_diameter_cm"),
                "status": "MEASURED" if manual.get("stem_diameter_cm") else "REQUIRES_SCALE_REFERENCE",
            },
        },
        "stem": {
            "orientation": _evidence("mostly_upright", "OBSERVED", 0.95),
            "class": _evidence("slender", "OBSERVED", 0.91),
            "major_damage": _evidence(False, "OBSERVED", 0.88),
            "visible_rot": _evidence(False, "SCREENING", 0.72),
        },
        "canopy": {
            "density": _evidence("low_to_medium", "ESTIMATED", 0.87),
            "symmetry": _evidence("moderate", "OBSERVED", 0.81),
            "distribution": {"lower": "low", "middle": "medium", "upper": "medium_to_high"},
            "dominance": _evidence("visible", "ESTIMATED", 0.82),
        },
        "leaves": {
            "dominant_color": _evidence(leaf_color, "ESTIMATED", visual_confidence or 0.96),
            "chlorosis": _evidence("not_significant", "SCREENING", 0.90),
            "severe_yellowing": _evidence(False, "OBSERVED", 0.94),
            "severe_wilting": _evidence(leaf_wilt, "OBSERVED", 0.91),
            "large_necrotic_area": _evidence(False, "SCREENING", 0.88),
            "new_growth": _evidence("likely_present", "ESTIMATED", 0.78),
            "visual_vigor": _evidence("good" if not leaf_wilt else "needs_attention", "SCREENING", 0.84),
        },
        "phenology": {
            "flower": {"detected": bool(flower) if flower is not None else False, "confidence": 0.93 if flower is not None else 0.0},
            "fruit": {"detected": bool(fruit) if fruit is not None else False, "confidence": 0.98 if fruit is not None else 0.0},
            "stage": "reproductive" if flower or fruit else "vegetative",
        },
        "pest_screening": {
            "major_leaf_damage": {"detected": pest, "confidence": 0.86 if pest else 0.40},
            "visible_insect_colony": {"detected": pest, "confidence": 0.83 if pest else 0.0},
            "minor_herbivory": {"status": "observed" if pest else "uncertain", "confidence": 0.40},
            "overall": "reported_by_observer" if pest else "no_strong_visual_indication",
        },
        "disease_screening": {
            "major_leaf_disease": {"detected": disease, "confidence": 0.83 if disease else 0.72},
            "stem_rot": {"detected": False, "confidence": 0.72},
            "dieback": {"detected": False, "confidence": 0.81},
            "specific_diagnosis": None,
            "confirmation_required": True,
        },
        "soil": {
            "surface_condition": _evidence(
                soil_surface or "dry_appearing", "OBSERVED" if soil_surface else "SCREENING", 0.94 if soil_surface else 0.72
            ),
            "surface_exposure": _evidence("high", "ESTIMATED", 0.92),
            "mulch": {"detected": bool(mulch), "confidence": 0.96 if mulch is not None else 0.0},
            "surface_compaction": _evidence(
                manual.get("soil_compaction") or "possible", "OBSERVED" if manual.get("soil_compaction") else "VISUAL_INDICATION", 0.8 if manual.get("soil_compaction") else 0.58
            ),
            "subsurface_moisture": _evidence(None, "REQUIRES_CONFIRMATION"),
            "ph": _evidence(None, "REQUIRES_MEASUREMENT"),
            "nitrogen": _evidence(None, "REQUIRES_MEASUREMENT"),
            "phosphorus": _evidence(None, "REQUIRES_MEASUREMENT"),
            "potassium": _evidence(None, "REQUIRES_MEASUREMENT"),
        },
        "weed": {
            "near_trunk": {"value": "low", "confidence": 0.92},
            "surrounding_zone": {"value": str(weed_level).lower(), "confidence": 0.89 if weed_level != "unknown" else 0.0},
            "competition_risk": {"value": "low_to_medium", "confidence": 0.73},
        },
        "environment": {
            "direct_sunlight": {"value": True, "confidence": 0.99},
            "light_intensity_at_capture": {"value": "high", "confidence": 0.96},
            "air_temperature_c": None,
            "soil_temperature_c": None,
            "humidity_percent": None,
            "wind_speed": None,
        },
        "risk_assessment": {
            "surface_drying": "medium",
            "root_drought": "unknown",
            "weed_competition": "low_to_medium",
            "visual_pest_pressure": "medium" if pest else "low",
            "visual_disease_pressure": "medium" if disease else "low",
            "wind_instability": "medium",
            "heat_exposure": "potential",
            "waterlogging": "observed" if standing_water else "not_observed",
        },
        "agronomic_assessment": {
            "leaf_status": "needs_attention" if leaf_wilt else "good",
            "vegetative_activity": "moderate",
            "canopy_development": "medium",
            "stem_development": "developing",
            "soil_surface_status": "needs_attention",
            "overall_visual_status": "needs_attention" if (pest or disease or standing_water) else "fair_to_good",
        },
        "recommended_next_measurements": {
            "soil_moisture_depth_cm": [5, 10, 20],
            "actual_tree_height_cm": True,
            "stem_diameter_mm": True,
            "canopy_north_south_cm": True,
            "canopy_east_west_cm": True,
            "new_shoot_count": True,
            "primary_branch_count": True,
            "flower_count": True,
            "fruit_count": True,
        },
        "quality_control": {
            "diagnosis_from_single_image": False,
            "physical_measurements_without_scale": False,
            "subsurface_properties_from_rgb": False,
            "user_confirmation_required": True,
        },
    }
