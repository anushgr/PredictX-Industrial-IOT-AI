from __future__ import annotations

import json
import logging
import ssl
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import mean
from threading import Lock
from typing import DefaultDict

import httpx
import paho.mqtt.client as mqtt
import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json

from app.core.config import settings
from app.core.supabase_config import supabase_config

logger = logging.getLogger(__name__)


@dataclass
class DataPoint:
    value: float
    timestamp: datetime
    unit: str


class MqttIngestionService:
    def __init__(self) -> None:
        self._client: mqtt.Client | None = None
        self._running = False
        self._lock = Lock()
        self._buffers: DefaultDict[tuple[str, str], list[DataPoint]] = defaultdict(list)
        self._last_insert: dict | None = None
        self._last_error: str | None = None
        self._db_connected = False
        self._db_error: str | None = None
        self._next_db_retry_at: datetime | None = None

    @property
    def running(self) -> bool:
        return self._running

    @property
    def last_insert(self) -> dict | None:
        return self._last_insert

    @property
    def last_error(self) -> str | None:
        return self._last_error

    @property
    def database_connected(self) -> bool:
        return self._db_connected

    @property
    def database_error(self) -> str | None:
        return self._db_error

    def verify_database_connection(self) -> bool:
        if settings.database_url:
            try:
                with psycopg2.connect(settings.database_url, sslmode="require") as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("select 1")
                        cursor.fetchone()
                self._db_connected = True
                self._db_error = None
                self._next_db_retry_at = None
                logger.info("Database connected successfully via DATABASE_URL")
                return True
            except Exception as exc:
                self._db_connected = False
                self._db_error = f"Database connection failed: {exc}"
                self._next_db_retry_at = datetime.now(timezone.utc) + timedelta(seconds=30)
                logger.error(self._db_error)
                return False

        if supabase_config.is_configured:
            self._db_connected = True
            self._db_error = None
            logger.info("Supabase REST storage configured")
            return True

        self._db_connected = False
        self._db_error = "No database storage configured (set DATABASE_URL or SUPABASE_URL+SUPABASE_KEY)"
        logger.error(self._db_error)
        return False

    def start(self) -> None:
        if not self.verify_database_connection():
            logger.error("MQTT ingestion not started because database is not connected")
            return

        if not settings.mqtt_enabled:
            logger.info("MQTT ingestion disabled via config")
            return

        if not settings.mqtt_host or not settings.mqtt_username or not settings.mqtt_password:
            self._last_error = "MQTT credentials/host missing"
            logger.warning("MQTT ingestion not started: host/username/password missing")
            return

        transport = "websockets" if settings.mqtt_use_websocket else "tcp"
        client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="predictx-backend-ingestor",
            transport=transport,
        )
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)
        client.tls_insecure_set(False)

        if settings.mqtt_use_websocket:
            client.ws_set_options(path="/mqtt")

        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.on_disconnect = self._on_disconnect

        port = settings.mqtt_ws_port if settings.mqtt_use_websocket else settings.mqtt_port
        client.connect(settings.mqtt_host, port, keepalive=settings.mqtt_keepalive)
        client.loop_start()

        self._client = client
        self._running = True
        logger.info("MQTT ingestion started on %s:%s topic=%s", settings.mqtt_host, port, settings.mqtt_topic)

    def stop(self) -> None:
        if self._client is not None:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None
        self._running = False

    def _on_connect(self, client: mqtt.Client, userdata, flags, reason_code, properties=None) -> None:
        code = getattr(reason_code, "value", reason_code)
        if code == 0:
            client.subscribe(settings.mqtt_topic, qos=settings.mqtt_qos)
            logger.info("MQTT subscribed to %s", settings.mqtt_topic)
        else:
            self._last_error = f"MQTT connect failed: {reason_code}"
            logger.error(self._last_error)

    def _on_disconnect(self, client: mqtt.Client, userdata, disconnect_flags, reason_code, properties=None) -> None:
        logger.warning("MQTT disconnected: %s", reason_code)

    def _on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage) -> None:
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            machine_id = str(payload["machine_id"])
            sensor = str(payload["sensor"])
            value = float(payload["value"])
            unit = str(payload.get("unit", ""))
            ts_raw = payload.get("timestamp")
            timestamp = (
                datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                if isinstance(ts_raw, str)
                else datetime.now(timezone.utc)
            )
        except Exception as exc:
            self._last_error = f"Invalid message payload: {exc}"
            logger.warning(self._last_error)
            return

        raw_record = {
            "machine_id": machine_id,
            "sensor": sensor,
            "value": value,
            "unit": unit,
            "timestamp": timestamp.isoformat(),
            "received_at": datetime.now(timezone.utc).isoformat(),
            "topic": msg.topic,
            "payload": payload,
        }

        self._store_raw_record(raw_record)

        key = (machine_id, sensor)
        with self._lock:
            self._buffers[key].append(DataPoint(value=value, timestamp=timestamp, unit=unit))
            window_size = max(2, settings.aggregation_window_size)
            if len(self._buffers[key]) < window_size:
                return

            points = self._buffers[key][:window_size]
            self._buffers[key] = self._buffers[key][window_size:]

        self._aggregate_and_store(machine_id, sensor, points)

    def _filter_outliers_iqr(self, values: list[float]) -> list[float]:
        if len(values) < 4:
            return values

        sorted_values = sorted(values)
        q1 = sorted_values[int(0.25 * (len(sorted_values) - 1))]
        q3 = sorted_values[int(0.75 * (len(sorted_values) - 1))]
        iqr = q3 - q1

        if iqr == 0:
            return values

        m = settings.outlier_iqr_multiplier
        lower = q1 - m * iqr
        upper = q3 + m * iqr
        filtered = [v for v in values if lower <= v <= upper]
        return filtered or values

    def _aggregate_and_store(self, machine_id: str, sensor: str, points: list[DataPoint]) -> None:
        values = [p.value for p in points]
        cleaned = self._filter_outliers_iqr(values)

        record = {
            "machine_id": machine_id,
            "sensor": sensor,
            "unit": points[0].unit,
            "window_size": len(values),
            "kept_count": len(cleaned),
            "mean_value": round(mean(cleaned), 4),
            "min_value": round(min(cleaned), 4),
            "max_value": round(max(cleaned), 4),
            "window_start": min(p.timestamp for p in points).isoformat(),
            "window_end": max(p.timestamp for p in points).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        if settings.database_url:
            if self._store_aggregate_postgres(record):
                return

        if not supabase_config.is_configured:
            self._last_insert = {**record, "storage": "disabled-no-supabase-config"}
            logger.info("Aggregated (not stored): %s", self._last_insert)
            return

        try:
            with httpx.Client(timeout=supabase_config.timeout_seconds) as client:
                response = client.post(supabase_config.endpoint, headers=supabase_config.headers, json=record)
                response.raise_for_status()
            self._last_insert = {**record, "storage": "supabase"}
            self._last_error = None
            logger.info("Stored aggregate in Supabase: %s", self._last_insert)
        except Exception as exc:
            self._last_error = f"Supabase insert failed: {exc}"
            logger.error(self._last_error)

    def _store_raw_record(self, record: dict) -> None:
        if settings.database_url:
            if self._store_raw_postgres(record):
                return

        if not supabase_config.is_configured:
            self._last_insert = {**record, "storage": "raw-disabled-no-supabase-config"}
            logger.info("Raw record not stored: %s", self._last_insert)
            return

        try:
            with httpx.Client(timeout=supabase_config.timeout_seconds) as client:
                response = client.post(
                    supabase_config.raw_endpoint(),
                    headers=supabase_config.headers,
                    json=record,
                )
                response.raise_for_status()
            self._last_insert = {**record, "storage": "supabase-raw"}
            self._last_error = None
            logger.info("Stored raw record in Supabase: %s", self._last_insert)
        except Exception as exc:
            self._last_error = f"Supabase raw insert failed: {exc}"
            logger.error(self._last_error)

    def _store_aggregate_postgres(self, record: dict) -> bool:
        if not self._can_retry_database():
            return False

        try:
            with psycopg2.connect(settings.database_url, sslmode="require") as connection:
                with connection.cursor() as cursor:
                    query = sql.SQL(
                        """
                        insert into {} (
                            machine_id, sensor, unit, window_size, kept_count,
                            mean_value, min_value, max_value, window_start, window_end, created_at
                        ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                    ).format(sql.Identifier(settings.supabase_table))
                    cursor.execute(
                        query,
                        (
                            record["machine_id"],
                            record["sensor"],
                            record["unit"],
                            record["window_size"],
                            record["kept_count"],
                            record["mean_value"],
                            record["min_value"],
                            record["max_value"],
                            record["window_start"],
                            record["window_end"],
                            record["created_at"],
                        ),
                    )
            self._last_insert = {**record, "storage": "postgres-aggregate"}
            self._last_error = None
            self._db_connected = True
            self._db_error = None
            logger.info("Stored aggregate in Postgres: %s", self._last_insert)
            return True
        except Exception as exc:
            self._last_error = f"Postgres aggregate insert failed: {exc}"
            self._db_connected = False
            self._db_error = self._last_error
            self._next_db_retry_at = datetime.now(timezone.utc) + timedelta(seconds=30)
            logger.error(self._last_error)
            return False

    def _store_raw_postgres(self, record: dict) -> bool:
        if not self._can_retry_database():
            return False

        try:
            with psycopg2.connect(settings.database_url, sslmode="require") as connection:
                with connection.cursor() as cursor:
                    query = sql.SQL(
                        """
                        insert into {} (
                            machine_id, sensor, value, unit, timestamp, received_at, topic, payload
                        ) values (%s, %s, %s, %s, %s, %s, %s, %s)
                        """
                    ).format(sql.Identifier(settings.supabase_raw_table))
                    cursor.execute(
                        query,
                        (
                            record["machine_id"],
                            record["sensor"],
                            record["value"],
                            record["unit"],
                            record["timestamp"],
                            record["received_at"],
                            record["topic"],
                            Json(record["payload"]),
                        ),
                    )
            self._last_insert = {**record, "storage": "postgres-raw"}
            self._last_error = None
            self._db_connected = True
            self._db_error = None
            logger.info("Stored raw record in Postgres: %s", self._last_insert)
            return True
        except Exception as exc:
            self._last_error = f"Postgres raw insert failed: {exc}"
            self._db_connected = False
            self._db_error = self._last_error
            self._next_db_retry_at = datetime.now(timezone.utc) + timedelta(seconds=30)
            logger.error(self._last_error)
            return False

    def _can_retry_database(self) -> bool:
        if self._next_db_retry_at is None:
            return True
        now = datetime.now(timezone.utc)
        return now >= self._next_db_retry_at


ingestion_service = MqttIngestionService()
