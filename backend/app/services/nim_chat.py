from __future__ import annotations

import httpx

from app.core.config import settings
from app.services.mock_data import get_failure_predictions, get_live_sensors, get_machines


def build_realtime_context() -> dict:
    machine = get_machines()[0]
    sensors = get_live_sensors()
    predictions = get_failure_predictions()
    return {
        "machine": {
            "id": machine["id"],
            "name": machine["name"],
            "status": machine["status"],
            "rpm": machine["rpm"],
            "temperature": machine["temperature"],
            "vibration": machine["vibration"],
            "failure_probability": machine["failure_probability"],
        },
        "sensors": [
            {
                "id": sensor["id"],
                "name": sensor["name"],
                "value": sensor["value"],
                "unit": sensor["unit"],
                "threshold": sensor["threshold"],
            }
            for sensor in sensors
        ],
        "predictions": predictions,
    }


def fallback_answer(user_message: str, context: dict) -> str:
    machine = context["machine"]
    sensor_summary = ", ".join(
        [f"{sensor['name']}: {sensor['value']}{sensor['unit']}" for sensor in context["sensors"]]
    )
    top_risk = context["predictions"][0]
    return (
        f"Assistant running in basic mode. You asked: '{user_message}'. "
        f"Current machine: {machine['name']} ({machine['status']}). "
        f"Live sensors: {sensor_summary}. "
        f"Top model risk: {top_risk['label']} at {top_risk['value']}%."
    )


def query_nim_chat(user_message: str, context: dict) -> tuple[str, str]:
    if not settings.nim_api_key:
        return fallback_answer(user_message, context), "fallback"

    system_prompt = (
        "You are PredictX Assistant. Give concise operational guidance for industrial maintenance. "
        "Use only provided context and avoid making up unavailable data."
    )

    payload = {
        "model": settings.nim_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"User question: {user_message}\n"
                    f"Realtime context JSON: {context}"
                ),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 280,
    }

    headers = {
        "Authorization": f"Bearer {settings.nim_api_key}",
        "Content-Type": "application/json",
    }

    url = f"{settings.nim_base_url.rstrip('/')}/chat/completions"

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content, "nim"
    except Exception:
        return fallback_answer(user_message, context), "fallback"
