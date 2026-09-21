from app.ai.types import Evidence, InspectionInputs


def evaluate_condition(inputs: InspectionInputs) -> tuple[str, tuple[Evidence, ...]]:
    evidence: list[Evidence] = []
    if inputs.standing_water:
        evidence.append(Evidence("Ada indikasi risiko genangan di zona akar."))
    if inputs.leaf_wilt:
        evidence.append(Evidence("Daun tampak layu berdasarkan observasi."))
    if inputs.standing_water or inputs.leaf_wilt:
        return ("PENTING" if inputs.standing_water else "PERHATIAN", tuple(evidence))
    return "SEHAT", (Evidence("Belum ada aturan risiko yang terpicu."),)
