"""
Machine predictions service.
Returns ML model predictions for failure risk, anomalies, and recommended actions.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import psycopg2

from app.core.config import settings
from app.services.predictor_runtime import predictor_runtime_service

logger = logging.getLogger(__name__)


def _format_realtime_prediction(prediction: dict) -> dict:
    sensor_scores = prediction.get("sensor_scores", {})
    machine_health = prediction.get("machine_health", {})
    timestamp = prediction.get("timestamp") or datetime.now(timezone.utc).isoformat()

    predictions = []
    for sensor_name, score_data in sensor_scores.items():
        health_pct = float(score_data.get("health_pct", 100.0))
        prediction_score = float(score_data.get("score", 0.0))
        classification = str(score_data.get("classification", "normal"))
        predictions.append(
            {
                "sensor": sensor_name,
                "predictionScore": prediction_score,
                "anomalyFlag": classification in {"warning", "critical"},
                "failureProbability": int(max(0, min(100, round(100.0 - health_pct)))),
                "recommendedAction": machine_health.get("recommendation", "Monitor machine condition."),
                "timestamp": timestamp,
                "classification": classification,
                "healthPct": health_pct,
                "confidence": float(score_data.get("confidence", 0.0)),
            },
        )

    return {
        "machine_id": prediction.get("machine_id", "unknown"),
        "timestamp": timestamp,
        "sensor_scores": sensor_scores,
        "machine_health": machine_health,
        "predictions": predictions,
        "source": "realtime-model",
    }


def get_predictions_from_db() -> dict:
    """Query predictions from DB or return empty data."""
    latest_prediction = predictor_runtime_service.get_latest_prediction("conveyor-07")
    if latest_prediction:
        return _format_realtime_prediction(latest_prediction)

    if not settings.database_url:
        logger.info("DATABASE_URL not set, returning no predictions")
        return {"predictions": [], "source": "empty"}

    try:
        with psycopg2.connect(settings.database_url, sslmode="require") as connection:
            with connection.cursor() as cursor:
                # Get latest prediction for each sensor
                cursor.execute(
                    """
                    SELECT 
                        sensor,
                        prediction_score,
                        anomaly_flag,
                        failure_probability_percent,
                        recommended_action,
                        created_at
                    FROM machine_predictions
                    WHERE machine_id = 'conveyor-07'
                    ORDER BY created_at DESC
                    LIMIT 3
                    """,
                )
                rows = cursor.fetchall()
                
                if rows:
                    predictions = {
                        "predictions": [
                            {
                                "sensor": row[0],
                                "predictionScore": row[1],
                                "anomalyFlag": row[2],
                                "failureProbability": row[3],
                                "recommendedAction": row[4],
                                "timestamp": row[5].isoformat() if row[5] else datetime.now(timezone.utc).isoformat(),
                            }
                            for row in rows
                        ],
                        "machine_id": "conveyor-07",
                        "sensor_scores": {},
                        "machine_health": {},
                        "source": "database",
                    }
                    return predictions
                else:
                    logger.info("No predictions in DB, returning empty predictions")
                    return {"predictions": [], "machine_id": "conveyor-07", "sensor_scores": {}, "machine_health": {}, "source": "empty"}

    except Exception as exc:
        logger.error(f"Failed to query predictions from DB: {exc}")
        return {"predictions": [], "source": "empty"}


def get_alerts_from_db() -> dict:
    """Get predictive alerts/anomalies."""
    predictions = get_predictions_from_db()

    if not predictions.get("predictions"):
        return {"activeAlerts": []}
    
    active_alerts = [
        {
            "id": f"alert-{idx}",
            "machine": "Conveyor-07",
            "sensor": pred["sensor"],
            "alertType": "Anomaly Detected" if pred["anomalyFlag"] else "Normal",
            "severity": "High" if pred["predictionScore"] > 0.7 else "Medium" if pred["predictionScore"] > 0.4 else "Low",
            "predictedCause": pred["recommendedAction"],
            "status": "Active" if pred["anomalyFlag"] else "Monitoring",
            "timestamp": pred["timestamp"],
        }
        for idx, pred in enumerate(predictions["predictions"])
    ]
    
    return {"activeAlerts": active_alerts}
