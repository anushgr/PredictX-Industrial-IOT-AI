from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.services.mock_data import get_alert_records, get_failure_predictions, get_predicted_alerts

router = APIRouter()


@router.get("/predict/failure")
def predict_failure(_: dict = Depends(get_current_user)) -> list[dict]:
    return get_failure_predictions()


@router.get("/predict/alerts")
def predict_alerts(_: dict = Depends(get_current_user)) -> dict:
    return {
        "predictions": get_predicted_alerts(),
        "activeAlerts": get_alert_records(),
    }
