from fastapi import APIRouter

from app.services.predictions_db import get_predictions_from_db, get_alerts_from_db

router = APIRouter()


@router.get("/predict/failure")
def predict_failure() -> dict:
    return get_predictions_from_db()


@router.get("/predict/alerts")
def predict_alerts() -> dict:
    predictions = get_predictions_from_db()
    alerts = get_alerts_from_db()
    return {
        "predictions": predictions.get("predictions", []),
        "activeAlerts": alerts.get("activeAlerts", []),
    }
