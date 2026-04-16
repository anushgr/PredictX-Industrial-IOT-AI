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
        logger.warning("DATABASE_URL not set, returning no telemetry data")
        return []

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
                        "sound": 4,
                        "vibration": 10,
                        "temperature": 30,
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
                
                return sensors

    except Exception as exc:
        logger.error(f"Failed to query live sensors from DB: {exc}")
        return []
