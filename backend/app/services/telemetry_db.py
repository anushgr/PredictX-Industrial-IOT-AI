"""
Live telemetry service using real sensor_raw_records from Supabase.
Returns latest readings for each sensor for live graphs.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import psycopg2

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_live_sensors_from_db() -> list[dict]:
    """Query latest sensor readings from raw records table."""
    if not settings.database_url:
        logger.warning("DATABASE_URL not set, returning mock sensors")
        return get_mock_sensors()

    try:
        with psycopg2.connect(settings.database_url, sslmode="require") as connection:
            with connection.cursor() as cursor:
                # Get last 20 readings per sensor for trend sparkline
                cursor.execute(
                    """
                    WITH recent_records AS (
                        SELECT 
                            sensor,
                            value,
                            unit,
                            timestamp,
                            ROW_NUMBER() OVER (PARTITION BY sensor ORDER BY timestamp DESC) as rn
                        FROM sensor_raw_records
                        WHERE machine_id = 'conveyor-07'
                        AND timestamp >= NOW() - INTERVAL '2 hours'
                        ORDER BY timestamp DESC
                    ),
                    latest AS (
                        SELECT sensor, value, unit, timestamp
                        FROM recent_records
                        WHERE rn = 1
                    ),
                    series AS (
                        SELECT
                            sensor,
                            ARRAY_AGG(value ORDER BY timestamp ASC) as series
                        FROM recent_records
                        WHERE rn <= 20
                        GROUP BY sensor
                    )
                    SELECT 
                        latest.sensor,
                        latest.value,
                        latest.unit,
                        latest.timestamp as latest_timestamp,
                        series.series
                    FROM latest
                    JOIN series ON series.sensor = latest.sensor
                    ORDER BY latest.sensor
                    """,
                )
                
                records = cursor.fetchall()
                sensors = []
                
                for sensor_name, latest_value, unit, timestamp, series in records:
                    series_list = list(series) if series else [latest_value]
                    
                    # Determine thresholds and anomaly detection
                    thresholds = {
                        "sound": 90,
                        "vibration": 5.5,
                        "temperature": 85,
                    }
                    threshold = thresholds.get(sensor_name, 100)
                    anomaly_count = sum(1 for v in series_list if v > threshold)
                    
                    sensors.append({
                        "id": sensor_name,
                        "name": sensor_name.title(),
                        "unit": unit,
                        "value": round(latest_value, 2),
                        "series": series_list[-20:],  # Last 20 values
                        "threshold": threshold,
                        "anomaly_count": anomaly_count,
                        "timestamp": timestamp.isoformat() if timestamp else datetime.now(timezone.utc).isoformat(),
                    })
                
                return sensors if sensors else get_mock_sensors()

    except Exception as exc:
        logger.error(f"Failed to query live sensors from DB: {exc}")
        return get_mock_sensors()


def get_mock_sensors() -> list[dict]:
    """Fallback mock sensor data when DB is unavailable."""
    return [
        {
            "id": "sound",
            "name": "Sound",
            "unit": "dB",
            "value": 72.5,
            "series": [70.0, 71.0, 72.0, 73.0, 74.0, 73.5, 72.8, 71.9, 70.5, 72.1,
                      71.8, 73.2, 74.1, 72.9, 71.5, 70.8, 72.3, 73.0, 72.5, 71.9],
            "threshold": 90,
            "anomaly_count": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "vibration",
            "name": "Vibration",
            "unit": "mm/s",
            "value": 4.1,
            "series": [2.9, 3.1, 3.3, 3.5, 3.8, 4.0, 4.1, 4.0, 3.9, 3.8,
                      3.7, 3.9, 4.0, 4.1, 4.0, 3.8, 3.9, 4.0, 4.1, 4.0],
            "threshold": 5.5,
            "anomaly_count": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "temperature",
            "name": "Temperature",
            "unit": "C",
            "value": 68.0,
            "series": [63.0, 64.0, 65.0, 66.0, 67.0, 68.0, 67.5, 66.8, 65.9, 67.1,
                      67.8, 68.2, 67.9, 66.5, 65.8, 66.3, 67.0, 67.5, 68.0, 67.6],
            "threshold": 85,
            "anomaly_count": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    ]
