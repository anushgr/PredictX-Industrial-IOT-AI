"""
Chatbot SQL engine for data-driven Q&A.
Parses user questions and executes SQL queries to retrieve real data.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone

import psycopg2

from app.core.config import settings

logger = logging.getLogger(__name__)

SENSOR_KEYWORDS = {
    "vibration": ["vibration", "shake", "oscillat"],
    "temperature": ["temp", "heat", "warm", "cool"],
    "sound": ["sound", "noise", "acoustic", "decibel", "db"],
}

TIME_KEYWORDS = {
    "last_hour": ["last hour", "past hour", "1 hour", "60 minutes"],
    "last_day": ["last day", "past day", "24 hour", "yesterday", "today"],
    "last_week": ["last week", "past week", "7 day", "weekly"],
    "last_month": ["last month", "past month", "30 day", "monthly"],
}


def detect_sensor(question: str) -> str | None:
    """Detect which sensor the question is about."""
    q_lower = question.lower()
    for sensor, keywords in SENSOR_KEYWORDS.items():
        if any(kw in q_lower for kw in keywords):
            return sensor
    return None


def detect_time_range(question: str) -> tuple[datetime, str]:
    """Detect time range from question. Returns (start_datetime, description)."""
    q_lower = question.lower()
    now = datetime.now(timezone.utc)
    
    for timeframe, keywords in TIME_KEYWORDS.items():
        if any(kw in q_lower for kw in keywords):
            if timeframe == "last_hour":
                return (now - timedelta(hours=1), "last 1 hour")
            elif timeframe == "last_day":
                return (now - timedelta(days=1), "last 24 hours")
            elif timeframe == "last_week":
                return (now - timedelta(days=7), "last 7 days")
            elif timeframe == "last_month":
                return (now - timedelta(days=30), "last 30 days")
    
    return (now - timedelta(hours=6), "last 6 hours")  # Default


def query_latest_value(sensor: str) -> dict:
    """Get latest sensor reading."""
    if not settings.database_url:
        return {"status": "error", "message": "Database not configured"}
    
    try:
        with psycopg2.connect(settings.database_url, sslmode="require") as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT value, unit, timestamp
                    FROM sensor_raw_records
                    WHERE machine_id = 'conveyor-07' AND sensor = %s
                    ORDER BY timestamp DESC
                    LIMIT 1
                    """,
                    (sensor,),
                )
                row = cursor.fetchone()
                
                if row:
                    return {
                        "status": "success",
                        "sensor": sensor,
                        "value": row[0],
                        "unit": row[1],
                        "timestamp": row[2].isoformat(),
                    }
                else:
                    return {"status": "no_data", "sensor": sensor}
    except Exception as exc:
        logger.error(f"Query latest value failed: {exc}")
        return {"status": "error", "message": str(exc)}


def query_trend(sensor: str, start_time: datetime) -> dict:
    """Get sensor trend over time period."""
    if not settings.database_url:
        return {"status": "error", "message": "Database not configured"}
    
    try:
        with psycopg2.connect(settings.database_url, sslmode="require") as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 
                        DATE_TRUNC('hour', timestamp) as hour,
                        AVG(value) as avg_value,
                        MIN(value) as min_value,
                        MAX(value) as max_value,
                        COUNT(*) as samples
                    FROM sensor_raw_records
                    WHERE machine_id = 'conveyor-07' 
                    AND sensor = %s
                    AND timestamp >= %s
                    GROUP BY DATE_TRUNC('hour', timestamp)
                    ORDER BY hour ASC
                    """,
                    (sensor, start_time),
                )
                
                rows = cursor.fetchall()
                if rows:
                    return {
                        "status": "success",
                        "sensor": sensor,
                        "samples": len(rows),
                        "trend_data": [
                            {
                                "timestamp": row[0].isoformat(),
                                "avg": round(row[1], 2),
                                "min": round(row[2], 2),
                                "max": round(row[3], 2),
                                "count": row[4],
                            }
                            for row in rows
                        ],
                    }
                else:
                    return {"status": "no_data", "sensor": sensor}
    except Exception as exc:
        logger.error(f"Query trend failed: {exc}")
        return {"status": "error", "message": str(exc)}


def query_anomalies(start_time: datetime) -> dict:
    """Find anomalies across all sensors."""
    if not settings.database_url:
        return {"status": "error", "message": "Database not configured"}
    
    try:
        with psycopg2.connect(settings.database_url, sslmode="require") as connection:
            with connection.cursor() as cursor:
                # Get aggregates with outliers flagged
                cursor.execute(
                    """
                    SELECT 
                        sensor,
                        unit,
                        mean_value,
                        min_value,
                        max_value,
                        created_at,
                        CASE 
                            WHEN sensor = 'vibration' AND mean_value > 5.5 THEN 'HIGH'
                            WHEN sensor = 'temperature' AND mean_value > 80 THEN 'HIGH'
                            WHEN sensor = 'sound' AND mean_value > 85 THEN 'HIGH'
                            ELSE 'NORMAL'
                        END as severity
                    FROM sensor_aggregates
                    WHERE machine_id = 'conveyor-07'
                    AND created_at >= %s
                    ORDER BY created_at DESC
                    """,
                    (start_time,),
                )
                
                rows = cursor.fetchall()
                anomalies = [
                    {
                        "sensor": row[0],
                        "unit": row[1],
                        "value": round(row[2], 2),
                        "min": round(row[3], 2),
                        "max": round(row[4], 2),
                        "timestamp": row[5].isoformat(),
                        "severity": row[6],
                    }
                    for row in rows if row[6] == "HIGH"
                ]
                
                return {
                    "status": "success",
                    "anomalies_count": len(anomalies),
                    "anomalies": anomalies,
                }
    except Exception as exc:
        logger.error(f"Query anomalies failed: {exc}")
        return {"status": "error", "message": str(exc)}


def query_health_summary() -> dict:
    """Get overall machine health summary."""
    if not settings.database_url:
        return {"status": "error", "message": "Database not configured"}
    
    try:
        with psycopg2.connect(settings.database_url, sslmode="require") as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 
                        sensor,
                        COUNT(*) as total_samples,
                        AVG(mean_value) as avg_value,
                        MAX(mean_value) as peak_value,
                        MIN(mean_value) as min_value
                    FROM sensor_aggregates
                    WHERE machine_id = 'conveyor-07'
                    AND created_at >= NOW() - INTERVAL '7 days'
                    GROUP BY sensor
                    """,
                )
                
                rows = cursor.fetchall()
                summary = {
                    "status": "success",
                    "sensors": []
                }
                
                for row in rows:
                    summary["sensors"].append({
                        "sensor": row[0],
                        "samples": row[1],
                        "avg": round(row[2], 2),
                        "peak": round(row[3], 2),
                        "min": round(row[4], 2),
                    })
                
                return summary
    except Exception as exc:
        logger.error(f"Query health summary failed: {exc}")
        return {"status": "error", "message": str(exc)}


def answer_question(question: str) -> dict:
    """Main entry point: parse question and execute appropriate query."""
    logger.info(f"Chatbot question: {question}")
    
    # Detect what sensor the question is about
    sensor = detect_sensor(question)
    time_start, time_desc = detect_time_range(question)
    
    # Determine query type from keywords
    q_lower = question.lower()
    
    if any(kw in q_lower for kw in ["current", "latest", "now", "what is", "what's", "how much"]):
        if sensor:
            result = query_latest_value(sensor)
            if result.get("status") == "success":
                return {
                    "answer": f"The latest {sensor} reading is {result['value']} {result['unit']} (measured at {result['timestamp']}).",
                    "data": result,
                    "context": "queried from sensor_raw_records",
                }
        else:
            return query_health_summary()
    
    elif any(kw in q_lower for kw in ["trend", "history", "over", "during", "last"]):
        if sensor:
            result = query_trend(sensor, time_start)
            if result.get("status") == "success":
                avg_vals = [d["avg"] for d in result["trend_data"]]
                avg_overall = sum(avg_vals) / len(avg_vals) if avg_vals else 0
                return {
                    "answer": f"Over the {time_desc}, {sensor} averaged {round(avg_overall, 2)}, ranging from {min(avg_vals):.2f} to {max(avg_vals):.2f}. Analyzed {result['samples']} time periods.",
                    "data": result,
                    "context": "queried from sensor_raw_records aggregated by hour",
                }
        else:
            return query_health_summary()
    
    elif any(kw in q_lower for kw in ["anomal", "issue", "problem", "alert", "wrong", "abnormal"]):
        result = query_anomalies(time_start)
        if result.get("status") == "success" and result["anomalies_count"] > 0:
            anomaly_list = "; ".join([
                f"{a['sensor']}: {a['value']} {a['unit']} (severity: {a['severity']})"
                for a in result["anomalies"][:3]
            ])
            return {
                "answer": f"Found {result['anomalies_count']} anomalies over {time_desc}: {anomaly_list}",
                "data": result,
                "context": "queried from sensor_aggregates with severity thresholds",
            }
        else:
            return {
                "answer": f"No anomalies detected over {time_desc}. Machine operating normally.",
                "data": result,
                "context": "queried from sensor_aggregates",
            }
    
    elif any(kw in q_lower for kw in ["health", "status", "condition", "how is", "okay", "alright"]):
        return query_health_summary()
    
    else:
        # Default: return summary
        return query_health_summary()
