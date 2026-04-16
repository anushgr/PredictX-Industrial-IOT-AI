"""
==============================================================================
PART 4a: DEEP LEARNING MODEL ARCHITECTURE
==============================================================================
Implements a time-series anomaly detection model for predictive maintenance.

Architecture: Autoencoder + Statistical threshold
- Encoder compresses normal operating patterns
- Decoder reconstructs input
- High reconstruction error = anomaly
- Additional health score and RUL (Remaining Useful Life) estimation

This is a pure NumPy implementation suitable for classroom demo
without requiring TensorFlow/PyTorch. The same architecture can be
directly ported to PyTorch for production use.
==============================================================================
"""

import numpy as np
import json
import os
from datetime import datetime, timezone


class ActivationFunctions:
    """Neural network activation functions implemented in NumPy."""

    @staticmethod
    def relu(x: np.ndarray) -> np.ndarray:
        return np.maximum(0, x)

    @staticmethod
    def relu_derivative(x: np.ndarray) -> np.ndarray:
        return (x > 0).astype(float)

    @staticmethod
    def sigmoid(x: np.ndarray) -> np.ndarray:
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

    @staticmethod
    def sigmoid_derivative(x: np.ndarray) -> np.ndarray:
        s = ActivationFunctions.sigmoid(x)
        return s * (1 - s)

    @staticmethod
    def tanh(x: np.ndarray) -> np.ndarray:
        return np.tanh(x)

    @staticmethod
    def tanh_derivative(x: np.ndarray) -> np.ndarray:
        return 1 - np.tanh(x) ** 2

    @staticmethod
    def leaky_relu(x: np.ndarray, alpha: float = 0.01) -> np.ndarray:
        return np.where(x > 0, x, alpha * x)

    @staticmethod
    def leaky_relu_derivative(x: np.ndarray, alpha: float = 0.01) -> np.ndarray:
        return np.where(x > 0, 1.0, alpha)

    @staticmethod
    def linear(x: np.ndarray) -> np.ndarray:
        return x

    @staticmethod
    def linear_derivative(x: np.ndarray) -> np.ndarray:
        return np.ones_like(x)


class DenseLayer:
    """Fully connected neural network layer."""

    def __init__(self, input_size: int, output_size: int,
                 activation: str = "relu"):
        # Xavier initialization
        scale = np.sqrt(2.0 / (input_size + output_size))
        self.weights = np.random.randn(input_size, output_size) * scale
        self.biases = np.zeros((1, output_size))
        self.activation_name = activation
        self.activation = getattr(ActivationFunctions, activation)
        self._derivative_fn = getattr(
            ActivationFunctions, f"{activation}_derivative"
        )

        # Cache for forward/backward pass
        self._input = None
        self._pre_activation = None
        self._output = None

        # Gradient storage (populated by backward)
        self.d_weights = None
        self.d_biases = None

    def forward(self, x: np.ndarray) -> np.ndarray:
        self._input = x
        self._pre_activation = x @ self.weights + self.biases
        self._output = self.activation(self._pre_activation)
        return self._output

    def backward(self, d_output: np.ndarray) -> np.ndarray:
        """
        Backpropagate gradients through this layer.

        Args:
            d_output: gradient of loss w.r.t. this layer's output, shape (batch, out)
        Returns:
            gradient of loss w.r.t. this layer's input, shape (batch, in)
        """
        d_pre = d_output * self._derivative_fn(self._pre_activation)
        self.d_weights = self._input.T @ d_pre          # (in, out)
        self.d_biases = np.sum(d_pre, axis=0, keepdims=True)  # (1, out)
        return d_pre @ self.weights.T                    # (batch, in)

    def apply_gradients(self, lr: float):
        """Update weights with accumulated gradients."""
        if self.d_weights is not None:
            self.weights -= lr * self.d_weights
            self.biases -= lr * self.d_biases

    def get_params(self) -> dict:
        return {
            "weights": self.weights.tolist(),
            "biases": self.biases.tolist(),
            "activation": self.activation_name,
        }

    def set_params(self, params: dict):
        self.weights = np.array(params["weights"])
        self.biases = np.array(params["biases"])


class AnomalyAutoencoder:
    """
    Autoencoder for time-series anomaly detection.

    Architecture:
    ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐
    │Input   │──▶│Encoder │──▶│Latent  │──▶│Decoder │──▶│Output  │
    │(30 feat)│  │128→64  │   │Space   │   │64→128  │   │(30 feat)│
    └────────┘   └────────┘   │(32 dim)│   └────────┘   └────────┘
                               └────────┘

    Anomaly Score = Reconstruction Error (MSE)
    High error = input doesn't match learned normal patterns = anomaly
    """

    def __init__(self, input_dim: int = 30, latent_dim: int = 32):
        self.input_dim = input_dim
        self.latent_dim = latent_dim

        # Encoder layers
        self.encoder_layers = [
            DenseLayer(input_dim, 128, "relu"),
            DenseLayer(128, 64, "relu"),
            DenseLayer(64, latent_dim, "tanh"),
        ]

        # Decoder layers (mirror of encoder)
        # Final layer uses linear so output range matches z-score normalized input
        self.decoder_layers = [
            DenseLayer(latent_dim, 64, "relu"),
            DenseLayer(64, 128, "relu"),
            DenseLayer(128, input_dim, "linear"),
        ]

        # Normalization parameters (learned during training)
        self.input_mean = None
        self.input_std = None

        # Anomaly threshold (learned during training)
        self.threshold_warning = None
        self.threshold_critical = None

        # Training history
        self.is_trained = False
        self.training_history = []

    def _normalize(self, x: np.ndarray) -> np.ndarray:
        """Normalize input using learned statistics."""
        if self.input_mean is not None:
            std = np.where(self.input_std > 1e-8, self.input_std, 1.0)
            return (x - self.input_mean) / std
        return x

    def _denormalize(self, x: np.ndarray) -> np.ndarray:
        """Reverse normalization."""
        if self.input_mean is not None:
            std = np.where(self.input_std > 1e-8, self.input_std, 1.0)
            return x * std + self.input_mean
        return x

    def encode(self, x: np.ndarray) -> np.ndarray:
        """Encode input to latent space."""
        h = x
        for layer in self.encoder_layers:
            h = layer.forward(h)
        return h

    def decode(self, z: np.ndarray) -> np.ndarray:
        """Decode from latent space to reconstruction."""
        h = z
        for layer in self.decoder_layers:
            h = layer.forward(h)
        return h

    def forward(self, x: np.ndarray) -> np.ndarray:
        """Full forward pass: encode then decode."""
        x_norm = self._normalize(x)
        z = self.encode(x_norm)
        x_recon = self.decode(z)
        return x_recon

    def compute_reconstruction_error(self, x: np.ndarray) -> np.ndarray:
        """Compute per-sample reconstruction error (MSE)."""
        x_norm = self._normalize(x)
        x_recon = self.forward(x)
        mse = np.mean((x_norm - x_recon) ** 2, axis=1)
        return mse

    def compute_sensor_anomaly_scores(self, x: np.ndarray) -> dict:
        """
        Compute per-sensor anomaly scores from a full 30-dim input.

        Runs one forward pass, then slices reconstruction error into:
          vibration  → features 0–9
          temperature → features 10–19
          sound       → features 20–29

        Returns:
            dict keyed by sensor type, each value is the same schema as
            compute_anomaly_score() (score, classification, health_pct, confidence)
        """
        if not self.is_trained:
            return {
                s: {"score": 0.0, "classification": "unknown",
                    "health_pct": 100.0, "confidence": 0.0}
                for s in ("vibration", "temperature", "sound")
            }

        x_norm = self._normalize(x)
        x_recon = self.forward(x)
        # Per-feature squared error, shape (batch, 30)
        sq_err = (x_norm - x_recon) ** 2

        slices = {
            "vibration":   (0, 10),
            "temperature": (10, 20),
            "sound":       (20, 30),
        }

        result = {}
        for sensor, (lo, hi) in slices.items():
            score = float(np.mean(sq_err[:, lo:hi]))
            if score >= self.threshold_critical:
                classification = "critical"
            elif score >= self.threshold_warning:
                classification = "warning"
            else:
                classification = "normal"

            if self.threshold_critical > 0:
                health_pct = max(0.0, min(100.0,
                    100.0 * (1 - score / self.threshold_critical)))
            else:
                health_pct = 100.0

            if classification == "normal" and self.threshold_warning > 0:
                confidence = min(1.0, score / self.threshold_warning)
            elif classification == "warning":
                span = self.threshold_critical - self.threshold_warning
                confidence = (score - self.threshold_warning) / span if span > 0 else 0.5
            else:
                confidence = min(1.0, score / (self.threshold_critical * 1.5))

            result[sensor] = {
                "score": round(score, 6),
                "classification": classification,
                "health_pct": round(health_pct, 1),
                "confidence": round(float(confidence), 3),
            }
        return result

    def compute_anomaly_score(self, x: np.ndarray) -> dict:
        """
        Compute anomaly score with classification.

        Returns:
            dict with score, classification, and health percentage
        """
        if not self.is_trained:
            return {
                "score": 0.0,
                "classification": "unknown",
                "health_pct": 100.0,
                "confidence": 0.0,
            }

        error = self.compute_reconstruction_error(x)
        score = float(np.mean(error))

        # Classify
        if score >= self.threshold_critical:
            classification = "critical"
        elif score >= self.threshold_warning:
            classification = "warning"
        else:
            classification = "normal"

        # Health percentage (100% = perfect, 0% = critical threshold)
        if self.threshold_critical > 0:
            health_pct = max(0, min(100,
                100 * (1 - score / self.threshold_critical)))
        else:
            health_pct = 100.0

        # Confidence based on distance from thresholds
        if classification == "normal" and self.threshold_warning > 0:
            confidence = min(1.0, score / self.threshold_warning)
        elif classification == "warning":
            span = self.threshold_critical - self.threshold_warning
            if span > 0:
                confidence = (score - self.threshold_warning) / span
            else:
                confidence = 0.5
        else:
            confidence = min(1.0, score / (self.threshold_critical * 1.5))

        return {
            "score": round(score, 6),
            "classification": classification,
            "health_pct": round(health_pct, 1),
            "confidence": round(float(confidence), 3),
        }

    def save(self, filepath: str):
        """Save model parameters to JSON."""
        model_data = {
            "input_dim": self.input_dim,
            "latent_dim": self.latent_dim,
            "is_trained": self.is_trained,
            "input_mean": self.input_mean.tolist() if self.input_mean is not None else None,
            "input_std": self.input_std.tolist() if self.input_std is not None else None,
            "threshold_warning": self.threshold_warning,
            "threshold_critical": self.threshold_critical,
            "encoder_layers": [l.get_params() for l in self.encoder_layers],
            "decoder_layers": [l.get_params() for l in self.decoder_layers],
            "training_history": self.training_history,
        }
        with open(filepath, "w") as f:
            json.dump(model_data, f, indent=2)
        print(f"[MODEL] Saved to {filepath}")

    def load(self, filepath: str):
        """Load model parameters from JSON."""
        with open(filepath, "r") as f:
            model_data = json.load(f)

        self.is_trained = model_data["is_trained"]
        if model_data["input_mean"] is not None:
            self.input_mean = np.array(model_data["input_mean"])
            self.input_std = np.array(model_data["input_std"])
        self.threshold_warning = model_data["threshold_warning"]
        self.threshold_critical = model_data["threshold_critical"]

        for i, params in enumerate(model_data["encoder_layers"]):
            self.encoder_layers[i].set_params(params)
        for i, params in enumerate(model_data["decoder_layers"]):
            self.decoder_layers[i].set_params(params)

        self.training_history = model_data.get("training_history", [])
        print(f"[MODEL] Loaded from {filepath}")


class HealthScorer:
    """
    Computes overall machine health from multi-sensor anomaly scores.
    Combines scores with domain-specific weighting.
    """

    # Sensor importance weights for overall health
    SENSOR_WEIGHTS = {
        "vibration": 0.45,   # Most predictive of mechanical failure
        "temperature": 0.30,  # Important for thermal issues
        "sound": 0.25,        # Good for detecting grinding/looseness
    }

    @staticmethod
    def compute_machine_health(sensor_scores: dict) -> dict:
        """
        Compute weighted machine health from individual sensor scores.

        Args:
            sensor_scores: {sensor_type: anomaly_score_dict} for each sensor
        """
        total_weight = 0
        weighted_health = 0
        worst_sensor = None
        worst_health = 100

        for sensor_type, score_data in sensor_scores.items():
            weight = HealthScorer.SENSOR_WEIGHTS.get(sensor_type, 0.33)
            health = score_data.get("health_pct", 100)
            weighted_health += weight * health
            total_weight += weight

            if health < worst_health:
                worst_health = health
                worst_sensor = sensor_type

        overall_health = weighted_health / total_weight if total_weight > 0 else 100

        # Determine overall status
        if overall_health >= 80:
            status = "healthy"
        elif overall_health >= 50:
            status = "degraded"
        elif overall_health >= 20:
            status = "warning"
        else:
            status = "critical"

        # Estimate remaining useful life (simplified)
        # Based on health trend - in production, use more sophisticated RUL models
        if overall_health >= 95:
            rul_hours = 1000
        elif overall_health >= 80:
            rul_hours = 500
        elif overall_health >= 50:
            rul_hours = 100
        elif overall_health >= 20:
            rul_hours = 24
        else:
            rul_hours = 4

        return {
            "overall_health_pct": round(overall_health, 1),
            "status": status,
            "worst_sensor": worst_sensor,
            "worst_sensor_health": round(worst_health, 1),
            "estimated_rul_hours": rul_hours,
            "recommendation": HealthScorer._get_recommendation(status, worst_sensor),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _get_recommendation(status: str, worst_sensor: str) -> str:
        recommendations = {
            "healthy": "No action required. Continue normal operation.",
            "degraded": f"Schedule inspection. Monitor {worst_sensor} closely.",
            "warning": f"Maintenance recommended within 24h. {worst_sensor} showing abnormal readings.",
            "critical": f"IMMEDIATE ACTION REQUIRED. {worst_sensor} at critical levels. Risk of imminent failure.",
        }
        return recommendations.get(status, "Monitor situation.")


# ── Standalone demo ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  PART 4a: DL MODEL ARCHITECTURE - Standalone Demo")
    print("=" * 60)

    # Create model
    model = AnomalyAutoencoder(input_dim=30, latent_dim=32)
    print(f"\nModel: {model.input_dim} -> 128 -> 64 -> {model.latent_dim} -> 64 -> 128 -> {model.input_dim}")

    # Simulate training data (normal operation)
    print("\n[DEMO] Generating synthetic normal data...")
    np.random.seed(42)
    normal_data = np.random.randn(200, 30) * 0.5 + 0.5

    # Set normalization params manually for demo
    model.input_mean = np.mean(normal_data, axis=0)
    model.input_std = np.std(normal_data, axis=0) + 1e-8

    # Set thresholds
    errors = model.compute_reconstruction_error(normal_data)
    model.threshold_warning = float(np.percentile(errors, 95))
    model.threshold_critical = float(np.percentile(errors, 99))
    model.is_trained = True

    print(f"  Warning threshold: {model.threshold_warning:.4f}")
    print(f"  Critical threshold: {model.threshold_critical:.4f}")

    # Test with normal data
    print("\n[DEMO] Testing with normal data:")
    test_normal = np.random.randn(1, 30) * 0.5 + 0.5
    result = model.compute_anomaly_score(test_normal)
    print(f"  Score: {result['score']:.6f} | Class: {result['classification']} | Health: {result['health_pct']}%")

    # Test with anomalous data
    print("\n[DEMO] Testing with anomalous data:")
    test_anomaly = np.random.randn(1, 30) * 3.0 + 2.0
    result = model.compute_anomaly_score(test_anomaly)
    print(f"  Score: {result['score']:.6f} | Class: {result['classification']} | Health: {result['health_pct']}%")

    # Health scoring
    print("\n[DEMO] Machine health scoring:")
    sensor_scores = {
        "vibration": {"health_pct": 45, "classification": "warning"},
        "temperature": {"health_pct": 72, "classification": "warning"},
        "sound": {"health_pct": 88, "classification": "normal"},
    }
    health = HealthScorer.compute_machine_health(sensor_scores)
    print(f"  Overall health: {health['overall_health_pct']}%")
    print(f"  Status: {health['status']}")
    print(f"  RUL: {health['estimated_rul_hours']} hours")
    print(f"  Recommendation: {health['recommendation']}")

    # Save model
    model.save(os.path.join(os.path.dirname(__file__), "tmp", "demo_model.json"))
    print("\n[DEMO] Model architecture demo complete.")