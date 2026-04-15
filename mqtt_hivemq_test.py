#!/usr/bin/env python3
"""
Simple HiveMQ Cloud connectivity tester.

Usage examples:
  python mqtt_hivemq_test.py --username YOUR_USER --password YOUR_PASS
  python mqtt_hivemq_test.py --websocket --username YOUR_USER --password YOUR_PASS

You can also use env vars:
  HIVEMQ_HOST, HIVEMQ_PORT, HIVEMQ_WS_PORT, HIVEMQ_USERNAME, HIVEMQ_PASSWORD, HIVEMQ_TOPIC
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
DEFAULT_TOPIC = "predictx/test"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test MQTT connection to HiveMQ Cloud")
    parser.add_argument("--host", default=os.getenv("HIVEMQ_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.getenv("HIVEMQ_PORT", DEFAULT_TLS_PORT)))
    parser.add_argument("--ws-port", type=int, default=int(os.getenv("HIVEMQ_WS_PORT", DEFAULT_WS_PORT)))
    parser.add_argument("--websocket", action="store_true", help="Use secure WebSocket transport (wss)")
    parser.add_argument("--username", default=os.getenv("HIVEMQ_USERNAME"))
    parser.add_argument("--password", default=os.getenv("HIVEMQ_PASSWORD"))
    parser.add_argument("--topic", default=os.getenv("HIVEMQ_TOPIC", DEFAULT_TOPIC))
    parser.add_argument("--message", default=f"hello-from-predictx-{int(time.time())}")
    parser.add_argument("--timeout", type=int, default=12, help="Seconds to wait for messages")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.username or not args.password:
        print("ERROR: username/password required. Pass --username/--password or set HIVEMQ_USERNAME/HIVEMQ_PASSWORD")
        return 1

    transport = "websockets" if args.websocket else "tcp"
    broker_port = args.ws_port if args.websocket else args.port
    client_id = f"predictx-check-{uuid4().hex[:10]}"

    connected = {"ok": False}

    def _reason_code_value(reason_code) -> int | None:
        if isinstance(reason_code, int):
            return reason_code
        value = getattr(reason_code, "value", None)
        if isinstance(value, int):
            return value
        try:
            return int(reason_code)
        except (TypeError, ValueError):
            return None

    def on_connect(client: mqtt.Client, userdata, flags, reason_code, properties=None):
        code = _reason_code_value(reason_code)
        if code == 0:
            connected["ok"] = True
            print(f"Connected: host={args.host} port={broker_port} transport={transport}")
            client.subscribe(args.topic, qos=1)
            print(f"Subscribed: {args.topic}")
            info = client.publish(args.topic, payload=args.message, qos=1)
            print(f"Publish queued (mid={info.mid}): {args.message}")
        else:
            print(f"Connect failed: reason_code={reason_code}")

    def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        payload = msg.payload.decode("utf-8", errors="replace")
        print(f"Message received: topic={msg.topic} qos={msg.qos} payload={payload}")

    def on_subscribe(client: mqtt.Client, userdata, mid, granted_qos, properties=None):
        print(f"Subscribe acknowledged: mid={mid} qos={granted_qos}")

    def on_publish(client: mqtt.Client, userdata, mid, reason_code=None, properties=None):
        print(f"Publish acknowledged: mid={mid}")

    def on_disconnect(client: mqtt.Client, userdata, disconnect_flags, reason_code, properties=None):
        print(f"Disconnected: reason_code={reason_code}")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, transport=transport)
    client.username_pw_set(args.username, args.password)

    # HiveMQ Cloud requires TLS
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)
    client.tls_insecure_set(False)

    if args.websocket:
        client.ws_set_options(path="/mqtt")

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_subscribe = on_subscribe
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect

    print("Connecting...")
    client.connect(args.host, broker_port, keepalive=60)
    client.loop_start()

    started = time.time()
    try:
        while time.time() - started < args.timeout:
            time.sleep(0.25)
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        client.loop_stop()
        client.disconnect()

    if not connected["ok"]:
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
