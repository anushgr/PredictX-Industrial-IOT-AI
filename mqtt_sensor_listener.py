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
import os
import ssl
import sys
import time
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
    return parser.parse_args()


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
        payload = msg.payload.decode("utf-8", errors="replace")
        print(f"message topic={msg.topic} qos={msg.qos} retain={msg.retain} payload={payload}")

    def on_disconnect(c: mqtt.Client, userdata, disconnect_flags, reason_code, properties=None):
        print(f"Disconnected: reason_code={reason_code}")

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    client.connect(args.host, broker_port, keepalive=60)
    client.loop_start()

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
