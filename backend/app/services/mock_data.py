from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone, date
from pathlib import Path

from app.core.security import hash_password

_DATA_PATH = Path(__file__).with_name("mock_data.json")


def _load_payload() -> dict:
    with _DATA_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


_RAW = _load_payload()

USERS = [
    {
        **user,
        "password_hash": hash_password(user["password"]),
    }
    for user in _RAW["users"]
]

MACHINES = [
    {
        **machine,
        "last_maintenance": date.fromisoformat(machine["last_maintenance"]),
    }
    for machine in _RAW["machines"]
]

_BASE_SENSORS = _RAW["sensors"]
PREDICTION_RISKS = _RAW["predictions"]
ALERTS = _RAW["alerts"]
ANALYTICS = _RAW["analytics"]


def get_users() -> list[dict]:
    return USERS


def get_user_by_email(email: str) -> dict | None:
    return next((user for user in USERS if user["email"].lower() == email.lower()), None)


def get_machines() -> list[dict]:
    return MACHINES


def get_machine_by_id(machine_id: str) -> dict | None:
    return next((machine for machine in MACHINES if machine["id"] == machine_id), None)


def _next_value(value: float, drift: float = 0.0) -> float:
    return round(value + random.uniform(-1.4, 1.4) + drift, 2)


def get_live_sensors() -> list[dict]:
    sensors = []
    for sensor in _BASE_SENSORS:
        value = _next_value(sensor["value"], 0.08 if sensor["id"] == "temp" else 0.0)
        series = [*sensor["series"][-19:], value]
        sensors.append(
            {
                **sensor,
                "value": value,
                "series": series,
                "anomaly_count": sensor["anomaly_count"] + (1 if value > sensor["threshold"] else 0),
            }
        )
    return sensors


def get_sensor_history() -> list[dict]:
    now = datetime.now(timezone.utc)
    history = []
    for sensor in _BASE_SENSORS:
        points = []
        for idx in range(30):
            timestamp = now - timedelta(minutes=(30 - idx) * 2)
            points.append(
                {
                    "timestamp": timestamp.isoformat(),
                    "value": _next_value(sensor["value"]),
                }
            )
        history.append({"sensor_id": sensor["id"], "points": points})
    return history


def get_failure_predictions() -> list[dict]:
    return PREDICTION_RISKS


def get_predicted_alerts() -> list[dict]:
    return ALERTS


def get_alert_records() -> list[dict]:
    return ALERTS


def get_analytics() -> dict:
    return ANALYTICS
