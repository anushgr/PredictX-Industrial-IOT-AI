#!/usr/bin/env python3
"""
Sensor stream listener for HiveMQ Cloud.

Subscribes to topic wildcard:
  predictx/machines/+/sensors/+

Example:
  python mqtt_sensor_listener.py --username anush --password Anush@123
  python mqtt_sensor_listener.py --username anush --password Anush@123 --machine-id conveyor-07
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

import paho.mqtt.client as mqtt

DEFAULT_HOST = "805bdf7166664409a14daa5bf806ef48.s1.eu.hivemq.cloud"
DEFAULT_TLS_PORT = 8883
DEFAULT_WS_PORT = 8884


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Listen to sensor MQTT messages from HiveMQ")
    parser.add_argument("--host", default=os.getenv("HIVEMQ_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.getenv("HIVEMQ_PORT", DEFAULT_TLS_PORT)))
    parser.add_argument("--ws-port", type=int, default=int(os.getenv("HIVEMQ_WS_PORT", DEFAULT_WS_PORT)))
    parser.add_argument("--websocket", action="store_true", help="Use secure WebSocket transport")
    parser.add_argument("--username", default=os.getenv("HIVEMQ_USERNAME"))
    parser.add_argument("--password", default=os.getenv("HIVEMQ_PASSWORD"))
    parser.add_argument("--machine-id", default="", help="Optional machine id filter")
    parser.add_argument("--qos", type=int, choices=[0, 1, 2], default=1)
    parser.add_argument(
        "--output",
        default=os.getenv("MQTT_TIMESERIES_FILE", "mqtt_sensor_timeseries.json"),
        help="Path to JSON file where time-series messages are stored",
    )
    return parser.parse_args()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_machine_and_sensor(topic: str) -> tuple[str, str]:
    parts = topic.split("/")
    if len(parts) >= 5:
        return parts[2], parts[4]
    return "unknown-machine", "unknown-sensor"


def load_timeseries(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "meta": {
                "created_at": utc_now_iso(),
                "updated_at": utc_now_iso(),
            },
            "series": {},
        }

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("root JSON value must be an object")
        data.setdefault("meta", {})
        data.setdefault("series", {})
        if not isinstance(data["meta"], dict):
            data["meta"] = {}
        if not isinstance(data["series"], dict):
            data["series"] = {}
        data["meta"].setdefault("created_at", utc_now_iso())
        data["meta"]["updated_at"] = utc_now_iso()
        return data
    except Exception:
        # Start clean if the file exists but contains invalid JSON.
        return {
            "meta": {
                "created_at": utc_now_iso(),
                "updated_at": utc_now_iso(),
            },
            "series": {},
        }


def persist_timeseries(path: Path, data: dict[str, Any]) -> None:
    data.setdefault("meta", {})
    data["meta"]["updated_at"] = utc_now_iso()
    path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temp_path.replace(path)


def append_message(
    store: dict[str, Any],
    topic: str,
    qos: int,
    retain: bool,
    payload_obj: Any,
    payload_text: str,
) -> dict[str, Any]:
    machine_id, sensor = _extract_machine_and_sensor(topic)

    if isinstance(payload_obj, dict):
        machine_id = str(payload_obj.get("machine_id", machine_id))
        sensor = str(payload_obj.get("sensor", sensor))
        timestamp = str(payload_obj.get("timestamp", utc_now_iso()))
        value = payload_obj.get("value")
        unit = payload_obj.get("unit")
    else:
        timestamp = utc_now_iso()
        value = None
        unit = None

    event = {
        "timestamp": timestamp,
        "ingested_at": utc_now_iso(),
        "value": value,
        "unit": unit,
        "topic": topic,
        "qos": qos,
        "retain": bool(retain),
        "payload": payload_obj,
        "payload_text": payload_text,
    }

    series = store.setdefault("series", {})
    machine_bucket = series.setdefault(machine_id, {})
    sensor_bucket = machine_bucket.setdefault(sensor, [])
    sensor_bucket.append(event)
    sensor_bucket.sort(key=lambda item: str(item.get("timestamp", "")))
    return event


def main() -> int:
    args = parse_args()

    if not args.username or not args.password:
        print("ERROR: provide --username and --password (or HIVEMQ_USERNAME/HIVEMQ_PASSWORD)")
        return 1

    transport = "websockets" if args.websocket else "tcp"
    broker_port = args.ws_port if args.websocket else args.port

    if args.machine_id:
        topic = f"predictx/machines/{args.machine_id}/sensors/+"
    else:
        topic = "predictx/machines/+/sensors/+"

    output_path = Path(args.output).expanduser().resolve()
    store = load_timeseries(output_path)
    store_lock = Lock()

    client_id = f"predictx-sub-{uuid4().hex[:10]}"
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, transport=transport)
    client.username_pw_set(args.username, args.password)
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)
    client.tls_insecure_set(False)

    if args.websocket:
        client.ws_set_options(path="/mqtt")

    def on_connect(c: mqtt.Client, userdata, flags, reason_code, properties=None):
        code = getattr(reason_code, "value", reason_code)
        if code == 0:
            print(f"Connected to {args.host}:{broker_port} ({transport})")
            c.subscribe(topic, qos=args.qos)
            print(f"Subscribed: {topic}")
        else:
            print(f"Connection failed: {reason_code}")

    def on_message(c: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        payload_text = msg.payload.decode("utf-8", errors="replace")
        try:
            payload_obj: Any = json.loads(payload_text)
        except json.JSONDecodeError:
            payload_obj = payload_text

        with store_lock:
            event = append_message(
                store=store,
                topic=msg.topic,
                qos=msg.qos,
                retain=bool(msg.retain),
                payload_obj=payload_obj,
                payload_text=payload_text,
            )
            persist_timeseries(output_path, store)

            machine_id, sensor = _extract_machine_and_sensor(msg.topic)
            sensor_events = store.get("series", {}).get(machine_id, {}).get(sensor, [])
            total_points = len(sensor_events)

        print(
            "message"
            f" topic={msg.topic}"
            f" qos={msg.qos}"
            f" retain={msg.retain}"
            f" ts={event['timestamp']}"
            f" value={event['value']}"
            f" unit={event['unit']}"
            f" points_for_stream={total_points}"
            f" stored={output_path}"
        )

    def on_disconnect(c: mqtt.Client, userdata, disconnect_flags, reason_code, properties=None):
        print(f"Disconnected: reason_code={reason_code}")

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    client.connect(args.host, broker_port, keepalive=60)
    client.loop_start()

    print(f"Time-series output file: {output_path}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        client.loop_stop()
        client.disconnect()

    return 0


if __name__ == "__main__":
    sys.exit(main())
