from app.ai.types import Prediction


def explain_prediction(prediction: Prediction) -> tuple[str, ...]:
    if prediction.evidence:
        return tuple(item.text for item in prediction.evidence)
    return ("Tidak ada bukti yang cukup untuk menjelaskan prediksi ini.",)


def explain_as_user_text(prediction: Prediction) -> str:
    return " ".join(explain_prediction(prediction))
