from dataclasses import dataclass


@dataclass
class SoilInference:
    moisture: str
    confidence: float
    explanations: list[str]


def infer_soil(*, surface_dark=False, standing_water=False, leaf_wilt=False):
    if standing_water:
        return SoilInference(
            "POSSIBLE_WATERLOGGING",
            0.70,
            ["Genangan terlihat pada observasi tanah."],
        )
    reasons = []
    if surface_dark:
        reasons.append("Permukaan tanah terlihat gelap.")
    if leaf_wilt:
        reasons.append("Daun dicatat layu pada pemeriksaan ini.")
    if surface_dark and not leaf_wilt:
        return SoilInference("MOIST", 0.55, reasons)
    return SoilInference(
        "SLIGHTLY_DRY",
        0.35,
        reasons or ["Bukti belum cukup untuk memperkirakan kondisi zona akar."],
    )


def evaluate_rules(
    *, leaf_wilt=False, pest_present=False, disease_present=False, waterlogging=False
):
    reasons = []
    if pest_present:
        reasons.append("Tanda hama perlu diverifikasi.")
    if disease_present:
        reasons.append("Gejala penyakit perlu diamati.")
    if leaf_wilt:
        reasons.append("Daun tampak layu berdasarkan observasi.")
    if waterlogging:
        reasons.append("Ada indikasi risiko genangan di zona akar.")
    if pest_present or disease_present or waterlogging:
        return "PENTING", reasons
    if leaf_wilt:
        return "PERHATIAN", reasons
    return "SEHAT", ["Belum ada aturan risiko yang terpicu."]


def confidence_label(value):
    if value >= 0.75:
        return "Tinggi"
    if value >= 0.45:
        return "Sedang"
    return "Rendah"
