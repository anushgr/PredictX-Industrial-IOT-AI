from __future__ import annotations

import logging
from pathlib import Path
from threading import Lock

from dl_model.model import AnomalyAutoencoder
from dl_model.model import HealthScorer
from dl_model.predictor import RealTimePredictor
from app.core.config import settings

logger = logging.getLogger(__name__)


class PredictorRuntimeService:
    """Loads and serves the DL predictor for low-latency inference."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._predictor: RealTimePredictor | None = None
        self._latest_by_machine: dict[str, dict] = {}
        self._initialized = False

    @staticmethod
    def _physical_thresholds() -> dict[str, float]:
        return {
            "temperature": settings.dl_threshold_temperature,
            "vibration": settings.dl_threshold_vibration,
            "sound": settings.dl_threshold_sound,
        }

    @staticmethod
    def _feature_value_for_threshold(sensor_features: dict) -> float | None:
        for key in ("mean", "max", "rms"):
            value = sensor_features.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        return None

    def _apply_physical_threshold_overrides(self, *, features: dict, payload: dict) -> None:
        sensor_scores = payload.get("sensor_scores")
        machine_health = payload.get("machine_health")
        if not isinstance(sensor_scores, dict) or not isinstance(machine_health, dict):
            return

        thresholds = self._physical_thresholds()

        for sensor_name, threshold in thresholds.items():
            score_data = sensor_scores.get(sensor_name)
            sensor_features = features.get(sensor_name)
            if not isinstance(score_data, dict) or not isinstance(sensor_features, dict):
                continue

            sensor_value = self._feature_value_for_threshold(sensor_features)
            if sensor_value is None or sensor_value <= threshold:
                continue

            exceed_ratio = (sensor_value - threshold) / max(threshold, 1e-9)
            threshold_health_pct = max(0.0, min(100.0, 100.0 - exceed_ratio * 100.0))

            score_data["classification"] = "critical"
            score_data["health_pct"] = round(min(float(score_data.get("health_pct", 100.0)), threshold_health_pct), 1)

        recomputed_health = HealthScorer.compute_machine_health(sensor_scores)
        recomputed_health["overall_anomaly_score"] = machine_health.get("overall_anomaly_score", 0.0)

        payload["sensor_scores"] = sensor_scores
        payload["machine_health"] = recomputed_health
        payload["thresholds"] = thresholds

    def initialize(self) -> None:
        with self._lock:
            if self._initialized and self._predictor is not None:
                return

            model_path = Path(__file__).resolve().parents[2] / "dl_model" / "trained_model.json"

            model = AnomalyAutoencoder(input_dim=30, latent_dim=32)
            predictor = RealTimePredictor(model=model)

            if model_path.exists():
                try:
                    model.load(str(model_path))
                    logger.info("DL model loaded from %s", model_path)
                except Exception as exc:
                    logger.warning("Failed to load trained model (%s). Falling back to quick synthetic training.", exc)
                    predictor.train_on_synthetic_data(n_samples=500, epochs=20)
            else:
                logger.warning("trained_model.json not found. Training quick synthetic model.")
                predictor.train_on_synthetic_data(n_samples=500, epochs=20)

            if not predictor.model or not predictor.model.is_trained:
                logger.warning("Predictor model still not trained. Running minimal training.")
                predictor.train_on_synthetic_data(n_samples=300, epochs=10)

            self._predictor = predictor
            self._initialized = True

    def predict(self, features: dict) -> dict | None:
        if not self._initialized or self._predictor is None:
            self.initialize()

        if self._predictor is None:
            return None

        result = self._predictor.predict(features)
        if not result:
            return None

        payload = result.to_dict()
        self._apply_physical_threshold_overrides(features=features, payload=payload)
        machine_id = payload.get("machine_id", "unknown")
        self._latest_by_machine[machine_id] = payload
        return payload

    def get_latest_prediction(self, machine_id: str) -> dict | None:
        return self._latest_by_machine.get(machine_id)


predictor_runtime_service = PredictorRuntimeService()
