"""
Analytics service using Supabase real database aggregates.
Queries 7-day trends from sensor_aggregates table instead of mock data.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import psycopg2

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_analytics_from_db() -> dict:
    """Query real aggregated data from Supabase for 7-day analytics."""
    if not settings.database_url:
        logger.warning("DATABASE_URL not set, returning empty analytics")
        return {}

    try:
        with psycopg2.connect(settings.database_url, sslmode="require") as connection:
            with connection.cursor() as cursor:
                now = datetime.now(timezone.utc)
                seven_days_ago = now - timedelta(days=7)

                # Get vibration trend (7 days, grouped by day)
                cursor.execute(
                    """
                    SELECT 
                        DATE(created_at AT TIME ZONE 'UTC') as day,
                        ROUND(AVG(mean_value)::numeric, 2)::float as avg_vibration
                    FROM sensor_aggregates
                    WHERE sensor = 'vibration' 
                    AND machine_id = 'conveyor-07'
                    AND created_at >= %s
                    GROUP BY DATE(created_at AT TIME ZONE 'UTC')
                    ORDER BY day ASC
                    LIMIT 7
                    """,
                    (seven_days_ago,),
                )
                vibration_trend = [row[1] for row in cursor.fetchall()]

                # Get temperature trend (7 days)
                cursor.execute(
                    """
                    SELECT 
                        DATE(created_at AT TIME ZONE 'UTC') as day,
                        ROUND(AVG(mean_value)::numeric, 1)::float as avg_temp
                    FROM sensor_aggregates
                    WHERE sensor = 'temperature' 
                    AND machine_id = 'conveyor-07'
                    AND created_at >= %s
                    GROUP BY DATE(created_at AT TIME ZONE 'UTC')
                    ORDER BY day ASC
                    LIMIT 7
                    """,
                    (seven_days_ago,),
                )
                temperature_trend = [row[1] for row in cursor.fetchall()]

                # Get sound trend
                cursor.execute(
                    """
                    SELECT 
                        DATE(created_at AT TIME ZONE 'UTC') as day,
                        ROUND(AVG(mean_value)::numeric, 1)::float as avg_sound
                    FROM sensor_aggregates
                    WHERE sensor = 'sound' 
                    AND machine_id = 'conveyor-07'
                    AND created_at >= %s
                    GROUP BY DATE(created_at AT TIME ZONE 'UTC')
                    ORDER BY day ASC
                    LIMIT 7
                    """,
                    (seven_days_ago,),
                )
                sound_trend = [row[1] for row in cursor.fetchall()]

                # Get latest stats for summary
                cursor.execute(
                    """
                    SELECT 
                        sensor,
                        ROUND(AVG(mean_value)::numeric, 2)::float as avg_val,
                        ROUND(MIN(min_value)::numeric, 2)::float as min_val,
                        ROUND(MAX(max_value)::numeric, 2)::float as max_val
                    FROM sensor_aggregates
                    WHERE machine_id = 'conveyor-07'
                    AND created_at >= %s
                    GROUP BY sensor
                    """,
                    (seven_days_ago,),
                )
                sensor_stats = {row[0]: row[1] for row in cursor.fetchall()}

                return {
                    "uptimeTrend": [],
                    "temperatureTrend": temperature_trend,
                    "vibrationTrend": vibration_trend,
                    "soundTrend": sound_trend,
                    "downtimeCauses": [],
                    "costTrend": [],
                    "sensorNoise": [],
                    "summary": {
                        "uptime": sensor_stats.get("uptime", 0),
                        "alerts": 0,
                        "avgTemperature": sensor_stats.get("temperature", 0),
                        "failureProbability": 0,
                    },
                }

    except Exception as exc:
        logger.error(f"Failed to query analytics from DB: {exc}")
        return {}
