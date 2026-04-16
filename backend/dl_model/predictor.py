"""
==============================================================================
PART 4c: REAL-TIME PREDICTOR
==============================================================================
Wraps the trained model for real-time inference on streaming data.
Integrates with the cloud pipeline to process feature vectors and
generate predictions, alerts, and maintenance recommendations.

Data Flow: Cloud Pipeline (features) --> predictor.py --> Dashboard (alerts)
==============================================================================
"""

import time
import threading
import queue
from datetime import datetime, timezone
from typing import Optional, Callable
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dl_model.model import AnomalyAutoencoder, HealthScorer
from dl_model.train_model import SyntheticDataGenerator, ModelTrainer, features_to_vector


class PredictionResult:
    """Container for a single prediction with all metadata."""

    def __init__(self, machine_id: str, sensor_scores: dict,
                 machine_health: dict, features_used: dict):
        self.machine_id = machine_id
        self.sensor_scores = sensor_scores
        self.machine_health = machine_health
        self.features_used = features_used
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "machine_id": self.machine_id,
            "timestamp": self.timestamp,
            "sensor_scores": self.sensor_scores,
            "machine_health": self.machine_health,
            "features_summary": {
                k: {"mean": v.get("mean"), "std": v.get("std")}
                for k, v in self.features_used.items()
                if isinstance(v, dict) and "mean" in v
            },
        }

    def is_alert(self) -> bool:
        return self.machine_health.get("status") in ("warning", "critical")


class RealTimePredictor:
    """
    Real-time prediction engine.

    Continuously processes feature vectors from the cloud pipeline
    and generates predictions with the trained DL model.

    Architecture:
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │  Feature     │────▶│  DL Model   │────▶│  Health     │
    │  Queue       │     │  Inference  │     │  Scoring    │
    └─────────────┘     └─────────────┘     └──────┬──────┘
                                                    │
                                   ┌────────────────┤
                                   ▼                ▼
                            ┌──────────┐     ┌──────────┐
                            │  Alert   │     │Dashboard │
                            │  Engine  │     │   Feed   │
                            └──────────┘     └──────────┘
    """

    def __init__(self, model: Optional[AnomalyAutoencoder] = None):
        self.model = model
        self.health_scorer = HealthScorer()

        self.input_queue = queue.Queue(maxsize=500)
        self.output_queue = queue.Queue(maxsize=500)
        self.alert_queue = queue.Queue(maxsize=100)

        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Prediction history per machine
        self.prediction_history: dict[str, list] = {}
        self.stats = {
            "total_predictions": 0,
            "alerts_generated": 0,
            "avg_inference_ms": 0,
        }

        # Alert callbacks
        self._alert_callbacks: list[Callable] = []

        print("[PREDICTOR] Initialized")

    def register_alert_callback(self, callback: Callable):
        self._alert_callbacks.append(callback)

    def train_on_synthetic_data(self, n_samples: int = 800, epochs: int = 50):
        """Train a new model using synthetic data (for demo purposes)."""
        print("[PREDICTOR] Training model on synthetic data...")
        gen = SyntheticDataGenerator(seed=42)
        train_data = gen.generate_normal_dataset(n_samples)
        val_data = gen.generate_normal_dataset(n_samples // 4)

        self.model = AnomalyAutoencoder(input_dim=30, latent_dim=32)
        trainer = ModelTrainer(self.model, learning_rate=0.001)
        trainer.train(train_data, val_data, epochs=epochs, verbose=True)
        print("[PREDICTOR] Model trained and ready")

    def predict(self, features: dict) -> Optional[PredictionResult]:
        """
        Run prediction on a feature vector for a single machine.

        Args:
            features: Dict from FeatureExtractor with keys:
                machine_id, vibration, temperature, sound
        """
        if self.model is None or not self.model.is_trained:
            return None

        machine_id = features.get("machine_id", "unknown")
        start_time = time.time()

        # Convert features to model input vector
        input_vector = features_to_vector(features)
        input_array = input_vector.reshape(1, -1)

        # Per-sensor anomaly scores via full reconstruction + sliced error
        sensor_scores = self.model.compute_sensor_anomaly_scores(input_array)

        # Mark any sensor whose feature dict had an error as unknown
        for sensor_type in ["vibration", "temperature", "sound"]:
            if "error" in features.get(sensor_type, {}):
                sensor_scores[sensor_type] = {
                    "score": 0, "classification": "unknown",
                    "health_pct": 100, "confidence": 0,
                }

        # Overall anomaly score (full vector)
        overall_score = self.model.compute_anomaly_score(input_array)

        # Compute machine health
        machine_health = self.health_scorer.compute_machine_health(sensor_scores)
        machine_health["overall_anomaly_score"] = overall_score["score"]

        inference_ms = (time.time() - start_time) * 1000

        # Create prediction result
        result = PredictionResult(
            machine_id=machine_id,
            sensor_scores=sensor_scores,
            machine_health=machine_health,
            features_used=features,
        )

        # Update stats
        self.stats["total_predictions"] += 1
        self.stats["avg_inference_ms"] = (
            self.stats["avg_inference_ms"] * 0.95 + inference_ms * 0.05
        )

        # Store in history
        if machine_id not in self.prediction_history:
            self.prediction_history[machine_id] = []
        self.prediction_history[machine_id].append(result.to_dict())
        # Keep only last 100 predictions per machine
        if len(self.prediction_history[machine_id]) > 100:
            self.prediction_history[machine_id] = \
                self.prediction_history[machine_id][-100:]

        # Generate alert if needed
        if result.is_alert():
            self.stats["alerts_generated"] += 1
            alert = {
                "type": "prediction_alert",
                "level": machine_health["status"],
                "machine_id": machine_id,
                "health_pct": machine_health["overall_health_pct"],
                "worst_sensor": machine_health.get("worst_sensor"),
                "rul_hours": machine_health.get("estimated_rul_hours"),
                "recommendation": machine_health.get("recommendation"),
                "timestamp": result.timestamp,
            }
            try:
                self.alert_queue.put(alert, timeout=0.5)
            except queue.Full:
                pass
            for cb in self._alert_callbacks:
                try:
                    cb(alert)
                except Exception:
                    pass

        try:
            self.output_queue.put(result.to_dict(), timeout=0.5)
        except queue.Full:
            pass

        return result

    def _prediction_loop(self):
        """Background prediction loop processing feature queue."""
        while self._running:
            try:
                features = self.input_queue.get(timeout=1.0)
                self.predict(features)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[PREDICTOR] Error: {e}")

    def start(self):
        """Start background prediction thread."""
        if self.model is None or not self.model.is_trained:
            print("[PREDICTOR] WARNING: Model not trained. Training now...")
            self.train_on_synthetic_data()

        self._running = True
        self._thread = threading.Thread(
            target=self._prediction_loop, daemon=True, name="predictor"
        )
        self._thread.start()
        print("[PREDICTOR] Started (background inference active)")

    def stop(self):
        """Stop the predictor."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3.0)
        print(f"[PREDICTOR] Stopped | Stats: {self.stats}")

    def get_latest_prediction(self, machine_id: str) -> Optional[dict]:
        """Get the most recent prediction for a machine."""
        history = self.prediction_history.get(machine_id, [])
        return history[-1] if history else None

    def get_all_predictions(self) -> dict:
        """Get latest predictions for all machines."""
        return {
            mid: hist[-1] if hist else None
            for mid, hist in self.prediction_history.items()
        }

    def get_alerts(self, max_alerts: int = 20) -> list:
        """Drain alert queue."""
        alerts = []
        while len(alerts) < max_alerts:
            try:
                alerts.append(self.alert_queue.get_nowait())
            except queue.Empty:
                break
        return alerts


# ── Standalone demo ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  PART 4c: REAL-TIME PREDICTOR - Standalone Demo")
    print("=" * 60)

    predictor = RealTimePredictor()
    predictor.train_on_synthetic_data(n_samples=500, epochs=30)

    # Simulate feature inputs
    print("\n[DEMO] Running predictions on simulated features...")

    # Normal operation features
    normal_features = {
        "machine_id": "CNC-MILL-001",
        "vibration": {"mean": 2.5, "std": 0.5, "min": 1.2, "max": 3.8,
                       "rms": 2.55, "peak_to_peak": 2.6, "crest_factor": 1.49,
                       "kurtosis": 0.3, "skewness": 0.1, "slope": 0.002},
        "temperature": {"mean": 55.0, "std": 2.5, "min": 50.0, "max": 60.0,
                         "rms": 55.06, "peak_to_peak": 10.0, "crest_factor": 1.09,
                         "kurtosis": -0.5, "skewness": 0.05, "slope": 0.001},
        "sound": {"mean": 72.0, "std": 3.0, "min": 65.0, "max": 80.0,
                   "rms": 72.06, "peak_to_peak": 15.0, "crest_factor": 1.11,
                   "kurtosis": 0.2, "skewness": 0.1, "slope": -0.003},
    }
    result = predictor.predict(normal_features)
    print(f"\n  Normal operation:")
    print(f"    Health: {result.machine_health['overall_health_pct']}%")
    print(f"    Status: {result.machine_health['status']}")

    # Failing machine features
    failing_features = {
        "machine_id": "CNC-MILL-001",
        "vibration": {"mean": 8.5, "std": 2.8, "min": 3.2, "max": 14.8,
                       "rms": 8.95, "peak_to_peak": 11.6, "crest_factor": 1.65,
                       "kurtosis": 3.5, "skewness": 0.8, "slope": 0.05},
        "temperature": {"mean": 88.0, "std": 5.5, "min": 78.0, "max": 96.0,
                         "rms": 88.17, "peak_to_peak": 18.0, "crest_factor": 1.09,
                         "kurtosis": 0.2, "skewness": 0.3, "slope": 0.02},
        "sound": {"mean": 95.0, "std": 6.0, "min": 82.0, "max": 108.0,
                   "rms": 95.19, "peak_to_peak": 26.0, "crest_factor": 1.13,
                   "kurtosis": 1.5, "skewness": 0.5, "slope": 0.015},
    }
    result = predictor.predict(failing_features)
    print(f"\n  Failing machine:")
    print(f"    Health: {result.machine_health['overall_health_pct']}%")
    print(f"    Status: {result.machine_health['status']}")
    print(f"    RUL: {result.machine_health['estimated_rul_hours']} hours")
    print(f"    Recommendation: {result.machine_health['recommendation']}")

    # Check alerts
    alerts = predictor.get_alerts()
    print(f"\n  Alerts generated: {len(alerts)}")
    for alert in alerts:
        print(f"    [{alert['level'].upper()}] {alert['machine_id']}: "
              f"{alert['recommendation']}")

    print(f"\n[DEMO] Predictor stats: {predictor.stats}")
    print("[DEMO] Predictor demo complete.")