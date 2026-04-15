#!/usr/bin/env python3
"""
Simulated sensor publisher for HiveMQ Cloud.

Publishes JSON payloads every N seconds to:
  predictx/machines/<machine_id>/sensors/<sensor_name>

Example:
  python mqtt_sensor_publisher.py --username anush --password Anush@123
  python mqtt_sensor_publisher.py --username anush --password Anush@123 --interval 1 --count 60
"""

from __future__ import annotations

import argparse
import json
import os
import random
import ssl
import sys
import time
from datetime import datetime, timezone
from uuid import uuid4

import paho.mqtt.client as mqtt

DEFAULT_HOST = "805bdf7166664409a14daa5bf806ef48.s1.eu.hivemq.cloud"
DEFAULT_TLS_PORT = 8883
DEFAULT_WS_PORT = 8884


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish simulated sensor data to HiveMQ")
    parser.add_argument("--host", default=os.getenv("HIVEMQ_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.getenv("HIVEMQ_PORT", DEFAULT_TLS_PORT)))
    parser.add_argument("--ws-port", type=int, default=int(os.getenv("HIVEMQ_WS_PORT", DEFAULT_WS_PORT)))
    parser.add_argument("--websocket", action="store_true", help="Use secure WebSocket transport")
    parser.add_argument("--username", default=os.getenv("HIVEMQ_USERNAME"))
    parser.add_argument("--password", default=os.getenv("HIVEMQ_PASSWORD"))
    parser.add_argument("--machine-id", default="conveyor-07")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between publish cycles")
    parser.add_argument("--count", type=int, default=0, help="Number of cycles, 0 means forever")
    parser.add_argument("--qos", type=int, choices=[0, 1, 2], default=1)
    parser.add_argument("--retain", action="store_true")
    return parser.parse_args()


def build_payload(machine_id: str, sensor: str, value: float, unit: str) -> str:
    payload = {
        "machine_id": machine_id,
        "sensor": sensor,
        "value": round(value, 3),
        "unit": unit,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(payload)


def main() -> int:
    args = parse_args()

    if not args.username or not args.password:
        print("ERROR: provide --username and --password (or HIVEMQ_USERNAME/HIVEMQ_PASSWORD)")
        return 1

    transport = "websockets" if args.websocket else "tcp"
    broker_port = args.ws_port if args.websocket else args.port

    client_id = f"predictx-pub-{uuid4().hex[:10]}"
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, transport=transport)
    client.username_pw_set(args.username, args.password)
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)
    client.tls_insecure_set(False)

    if args.websocket:
        client.ws_set_options(path="/mqtt")

    connected = {"ok": False}

    def on_connect(c: mqtt.Client, userdata, flags, reason_code, properties=None):
        code = getattr(reason_code, "value", reason_code)
        if code == 0:
            connected["ok"] = True
            print(f"Connected to {args.host}:{broker_port} ({transport})")
        else:
            print(f"Connection failed: {reason_code}")

    client.on_connect = on_connect

    client.connect(args.host, broker_port, keepalive=60)
    client.loop_start()

    # Wait briefly for connection callback
    wait_until = time.time() + 8
    while not connected["ok"] and time.time() < wait_until:
        time.sleep(0.1)

    if not connected["ok"]:
        print("ERROR: could not establish MQTT connection")
        client.loop_stop()
        client.disconnect()
        return 2

    sound = 70.0
    vibration = 4.0
    temp = 66.0

    cycle = 0
    try:
        while True:
            cycle += 1
            sound = max(40.0, min(95.0, sound + random.uniform(-1.2, 1.4)))
            vibration = max(1.0, min(8.0, vibration + random.uniform(-0.2, 0.25)))
            temp = max(35.0, min(95.0, temp + random.uniform(-0.6, 0.8)))

            messages = [
                ("sound", sound, "dB"),
                ("vibration", vibration, "mm/s"),
                ("temperature", temp, "C"),
            ]

            for sensor_name, value, unit in messages:
                topic = f"predictx/machines/{args.machine_id}/sensors/{sensor_name}"
                payload = build_payload(args.machine_id, sensor_name, value, unit)
                info = client.publish(topic, payload=payload, qos=args.qos, retain=args.retain)
                print(f"[{cycle}] published topic={topic} mid={info.mid} payload={payload}")

            if args.count > 0 and cycle >= args.count:
                break

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        client.loop_stop()
        client.disconnect()

    return 0


if __name__ == "__main__":
    sys.exit(main())
