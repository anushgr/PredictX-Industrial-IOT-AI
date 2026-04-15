"""
Machine predictions service.
Returns ML model predictions for failure risk, anomalies, and recommended actions.
Uses dummy fallback data until real DL model output is available.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import psycopg2

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_predictions_from_db() -> dict:
    """Query predictions from DB or return dummy data."""
    if not settings.database_url:
        logger.info("DATABASE_URL not set, returning dummy predictions")
        return get_dummy_predictions()

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
                        "source": "database",
                    }
                    return predictions
                else:
                    logger.info("No predictions in DB, returning dummy data")
                    return get_dummy_predictions()

    except Exception as exc:
        logger.error(f"Failed to query predictions from DB: {exc}")
        return get_dummy_predictions()


def get_dummy_predictions() -> dict:
    """Fallback dummy ML predictions."""
    return {
        "predictions": [
            {
                "sensor": "vibration",
                "predictionScore": 0.72,
                "anomalyFlag": True,
                "failureProbability": 72,
                "recommendedAction": "Bearing inspection within 24 hours",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            {
                "sensor": "temperature",
                "predictionScore": 0.35,
                "anomalyFlag": False,
                "failureProbability": 35,
                "recommendedAction": "Normal operation, monitor thermal trends",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            {
                "sensor": "sound",
                "predictionScore": 0.28,
                "anomalyFlag": False,
                "failureProbability": 28,
                "recommendedAction": "Continue normal operation",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        ],
        "source": "dummy",
    }


def get_alerts_from_db() -> dict:
    """Get predictive alerts/anomalies."""
    predictions = get_predictions_from_db()
    
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
