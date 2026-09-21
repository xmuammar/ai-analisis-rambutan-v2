from app.ai.types import Evidence, InspectionInputs, Prediction


def infer_virtual_soil(inputs: InspectionInputs) -> Prediction:
    if inputs.standing_water:
        return Prediction(
            "root_zone_moisture_class",
            "POSSIBLE_WATERLOGGING",
            0.70,
            "INFERRED",
            "AI_INFERRED",
            "rules-1",
            "soil-features-1",
            (Evidence("Genangan terlihat pada observasi tanah."),),
        )

    evidence = []
    if inputs.surface_dark:
        evidence.append(Evidence("Permukaan tanah terlihat gelap."))
    if inputs.leaf_wilt:
        evidence.append(Evidence("Daun dicatat layu pada pemeriksaan ini."))
    if inputs.surface_dark and not inputs.leaf_wilt:
        return Prediction(
            "root_zone_moisture_class",
            "MOIST",
            0.55,
            "INFERRED",
            "AI_INFERRED",
            "rules-1",
            "soil-features-1",
            tuple(evidence),
        )
    evidence = evidence or [
        Evidence(
            "Bukti belum cukup untuk memperkirakan kondisi zona akar.",
            "DATA_QUALITY",
        )
    ]
    return Prediction(
        "root_zone_moisture_class",
        "INSUFFICIENT_DATA",
        0.35,
        "INFERRED",
        "AI_INFERRED",
        "rules-1",
        "soil-features-1",
        tuple(evidence),
    )
