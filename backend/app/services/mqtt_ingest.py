from __future__ import annotations

import json
import logging
import os
import ssl
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import mean
from threading import Lock
from typing import DefaultDict

import httpx
import numpy as np
import paho.mqtt.client as mqtt
import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json

from app.core.config import settings
from app.core.supabase_config import supabase_config
from app.services.predictor_runtime import predictor_runtime_service

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class DataPoint:
    value: float
    timestamp: datetime
    unit: str


class MqttIngestionService:
    def __init__(self) -> None:
        self._client: mqtt.Client | None = None
        self._client_id: str | None = None
        self._running = False
        self._lock = Lock()
        self._buffers: DefaultDict[tuple[str, str], list[DataPoint]] = defaultdict(list)
        self._prediction_points: DefaultDict[tuple[str, str], list[DataPoint]] = defaultdict(list)
        self._feature_cache: DefaultDict[str, dict[str, dict]] = defaultdict(dict)
        self._last_insert: dict | None = None
        self._last_error: str | None = None
        self._db_connected = False
        self._db_error: str | None = None
        self._next_db_retry_at: datetime | None = None
        self._received_messages = 0
        self._last_received: dict | None = None
        self._subscribed_topic: str | None = None
        self._subscribe_result: int | None = None

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

    @property
    def received_messages(self) -> int:
        return self._received_messages

    @property
    def last_received_message(self) -> dict | None:
        return self._last_received

    @property
    def mqtt_client_id(self) -> str | None:
        return self._client_id

    @property
    def subscribed_topic(self) -> str | None:
        return self._subscribed_topic

    @property
    def subscribe_result(self) -> int | None:
        return self._subscribe_result

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
        client_id = f"predictx-backend-ingestor-{os.getpid()}"
        client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
            transport=transport,
        )
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)
        client.tls_insecure_set(False)
        # Ensure paho performs exponential reconnect attempts after network drops.
        client.reconnect_delay_set(min_delay=1, max_delay=30)

        if settings.mqtt_use_websocket:
            client.ws_set_options(path="/mqtt")

        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.on_disconnect = self._on_disconnect

        port = settings.mqtt_ws_port if settings.mqtt_use_websocket else settings.mqtt_port
        client.connect(settings.mqtt_host, port, keepalive=settings.mqtt_keepalive)
        client.loop_start()

        self._client = client
        self._client_id = client_id
        self._running = True
        logger.info(
            "MQTT ingestion started host=%s port=%s topic=%s client_id=%s",
            settings.mqtt_host,
            port,
            settings.mqtt_topic,
            client_id,
        )

    def stop(self) -> None:
        if self._client is not None:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None
        self._running = False

    def _on_connect(self, client: mqtt.Client, userdata, flags, reason_code, properties=None) -> None:
        code = getattr(reason_code, "value", reason_code)
        if code == 0:
            sub_result, sub_mid = client.subscribe(settings.mqtt_topic, qos=settings.mqtt_qos)
            self._subscribed_topic = settings.mqtt_topic
            self._subscribe_result = int(sub_result)
            logger.info(
                "MQTT connected client_id=%s topic=%s qos=%s subscribe_result=%s mid=%s",
                self._client_id,
                settings.mqtt_topic,
                settings.mqtt_qos,
                sub_result,
                sub_mid,
            )
        else:
            self._last_error = f"MQTT connect failed: {reason_code}"
            logger.error(self._last_error)

    def _on_disconnect(self, client: mqtt.Client, userdata, disconnect_flags, reason_code, properties=None) -> None:
        code = getattr(reason_code, "value", reason_code)
        logger.warning("MQTT disconnected: %s", reason_code)

        # code==0 is an intentional disconnect from shutdown path.
        if code == 0 or not self._running:
            return

        try:
            client.reconnect()
            logger.info("MQTT reconnect attempt triggered")
        except Exception as exc:
            self._last_error = f"MQTT reconnect failed: {exc}"
            logger.error(self._last_error)

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

        logger.info(
            "MQTT received topic=%s machine_id=%s sensor=%s value=%s %s ts=%s",
            msg.topic,
            machine_id,
            sensor,
            value,
            unit,
            timestamp.isoformat(),
        )
        self._received_messages += 1
        self._last_received = {
            "topic": msg.topic,
            "machine_id": machine_id,
            "sensor": sensor,
            "value": value,
            "unit": unit,
            "timestamp": timestamp.isoformat(),
            "received_at": datetime.now(timezone.utc).isoformat(),
        }

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

        # Store raw record before touching shared state (no lock needed here)
        self._store_raw_record(raw_record)

        key = (machine_id, sensor)
        points_to_aggregate: list[DataPoint] | None = None

        # Lock only covers buffer mutations — no I/O or blocking calls inside
        with self._lock:
            rolling_window_size = max(3, settings.aggregation_window_size)
            self._prediction_points[key].append(DataPoint(value=value, timestamp=timestamp, unit=unit))
            if len(self._prediction_points[key]) > rolling_window_size:
                self._prediction_points[key] = self._prediction_points[key][-rolling_window_size:]

            self._buffers[key].append(DataPoint(value=value, timestamp=timestamp, unit=unit))
            window_size = max(2, settings.aggregation_window_size)
            if len(self._buffers[key]) >= window_size:
                points_to_aggregate = self._buffers[key][:window_size]
                self._buffers[key] = self._buffers[key][window_size:]

        # All DB / prediction work happens outside the lock to prevent deadlock.
        # _run_prediction_from_rolling_buffers acquires self._lock internally,
        # so it must never be called while the lock is already held.
        self._run_prediction_from_rolling_buffers(machine_id)

        if points_to_aggregate is not None:
            self._aggregate_and_store(machine_id, sensor, points_to_aggregate)

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

    def _extract_features_from_points(self, points: list[DataPoint]) -> dict:
        values = np.array([p.value for p in points], dtype=float)

        mean_value = float(np.mean(values))
        std_value = float(np.std(values))
        min_value = float(np.min(values))
        max_value = float(np.max(values))
        rms_value = float(np.sqrt(np.mean(np.square(values))))
        peak_to_peak = float(max_value - min_value)
        crest_factor = float(abs(max_value) / rms_value) if rms_value > 1e-12 else 1.0

        centered = values - mean_value
        variance = float(np.mean(np.square(centered)))
        if variance > 1e-12:
            skewness = float(np.mean(centered ** 3) / (variance ** 1.5))
            kurtosis = float(np.mean(centered ** 4) / (variance ** 2) - 3.0)
        else:
            skewness = 0.0
            kurtosis = 0.0

        if len(values) >= 2:
            slope = float(np.polyfit(np.arange(len(values), dtype=float), values, 1)[0])
        else:
            slope = 0.0

        return {
            "mean": round(mean_value, 6),
            "std": round(std_value, 6),
            "min": round(min_value, 6),
            "max": round(max_value, 6),
            "rms": round(rms_value, 6),
            "peak_to_peak": round(peak_to_peak, 6),
            "crest_factor": round(crest_factor, 6),
            "kurtosis": round(kurtosis, 6),
            "skewness": round(skewness, 6),
            "slope": round(slope, 6),
        }

    def _run_prediction_for_window(self, machine_id: str, sensor: str, points: list[DataPoint]) -> None:
        if sensor not in {"vibration", "temperature", "sound"}:
            return

        try:
            sensor_features = self._extract_features_from_points(points)

            with self._lock:
                self._feature_cache[machine_id][sensor] = sensor_features
                cache = self._feature_cache[machine_id]
                required = {"vibration", "temperature", "sound"}
                if not required.issubset(cache.keys()):
                    return

                feature_payload = {
                    "machine_id": machine_id,
                    "vibration": cache["vibration"],
                    "temperature": cache["temperature"],
                    "sound": cache["sound"],
                }

            prediction = predictor_runtime_service.predict(feature_payload)
            if not prediction:
                return

            self._store_prediction_postgres(prediction)
        except Exception as exc:
            logger.error("Failed to run DL prediction: %s", exc)

    def _run_prediction_from_rolling_buffers(self, machine_id: str) -> None:
        try:
            with self._lock:
                sensors = {
                    sensor: list(self._prediction_points.get((machine_id, sensor), []))
                    for sensor in ("vibration", "temperature", "sound")
                }

            if not all(len(points) >= 3 for points in sensors.values()):
                return

            feature_payload = {
                "machine_id": machine_id,
                "vibration": self._extract_features_from_points(sensors["vibration"]),
                "temperature": self._extract_features_from_points(sensors["temperature"]),
                "sound": self._extract_features_from_points(sensors["sound"]),
            }

            prediction = predictor_runtime_service.predict(feature_payload)
            if prediction:
                self._store_prediction_postgres(prediction)
        except Exception as exc:
            logger.error("Failed to run rolling DL prediction: %s", exc)

    def _store_prediction_postgres(self, prediction: dict) -> None:
        if not settings.database_url:
            return

        machine_id = str(prediction.get("machine_id", "unknown"))
        timestamp = prediction.get("timestamp")
        sensor_scores = prediction.get("sensor_scores", {})
        machine_health = prediction.get("machine_health", {})
        recommendation = machine_health.get("recommendation", "Monitor machine condition.")

        rows: list[tuple] = []
        for sensor_name, score_data in sensor_scores.items():
            score = float(score_data.get("score", 0.0))
            classification = str(score_data.get("classification", "normal"))
            health_pct = float(score_data.get("health_pct", 100.0))
            failure_probability = int(max(0, min(100, round(100.0 - health_pct))))
            anomaly_flag = classification in {"warning", "critical"}
            rows.append(
                (
                    machine_id,
                    sensor_name,
                    score,
                    anomaly_flag,
                    failure_probability,
                    recommendation,
                    timestamp,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

        if not rows:
            return

        connection = None
        try:
            connection = psycopg2.connect(settings.database_url, sslmode="require")
            with connection:
                with connection.cursor() as cursor:
                    cursor.executemany(
                        """
                        INSERT INTO machine_predictions (
                            machine_id,
                            sensor,
                            prediction_score,
                            anomaly_flag,
                            failure_probability_percent,
                            recommended_action,
                            created_at,
                            updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        rows,
                    )
        except Exception as exc:
            logger.error("Failed to store DL prediction rows: %s", exc)
        finally:
            if connection is not None:
                connection.close()

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

        connection = None
        try:
            connection = psycopg2.connect(settings.database_url, sslmode="require")
            with connection:
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
            logger.info(
                "DB aggregate insert ok table=%s machine_id=%s sensor=%s mean=%s",
                settings.supabase_table,
                record["machine_id"],
                record["sensor"],
                record["mean_value"],
            )
            logger.info("Stored aggregate in Postgres: %s", self._last_insert)
            return True
        except Exception as exc:
            self._last_error = f"Postgres aggregate insert failed: {exc}"
            self._db_connected = False
            self._db_error = self._last_error
            self._next_db_retry_at = datetime.now(timezone.utc) + timedelta(seconds=30)
            logger.error(self._last_error)
            return False
        finally:
            if connection is not None:
                connection.close()

    def _store_raw_postgres(self, record: dict) -> bool:
        if not self._can_retry_database():
            return False

        connection = None
        try:
            connection = psycopg2.connect(settings.database_url, sslmode="require")
            with connection:
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
            logger.info(
                "DB raw insert ok table=%s machine_id=%s sensor=%s value=%s",
                settings.supabase_raw_table,
                record["machine_id"],
                record["sensor"],
                record["value"],
            )
            logger.info("Stored raw record in Postgres: %s", self._last_insert)
            return True
        except Exception as exc:
            self._last_error = f"Postgres raw insert failed: {exc}"
            self._db_connected = False
            self._db_error = self._last_error
            self._next_db_retry_at = datetime.now(timezone.utc) + timedelta(seconds=30)
            logger.error(self._last_error)
            return False
        finally:
            if connection is not None:
                connection.close()

    def _can_retry_database(self) -> bool:
        if self._next_db_retry_at is None:
            return True
        now = datetime.now(timezone.utc)
        return now >= self._next_db_retry_at


ingestion_service = MqttIngestionService()
