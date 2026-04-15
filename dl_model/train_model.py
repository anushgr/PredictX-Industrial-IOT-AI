"""
==============================================================================
PART 4b: MODEL TRAINING
==============================================================================
Trains the anomaly detection autoencoder using synthetic normal operating
data. In production, you'd train on weeks/months of real sensor data
collected during known-good operation.

Training Pipeline:
  1. Generate synthetic normal operating data
  2. Add realistic noise patterns
  3. Train autoencoder to reconstruct normal patterns
  4. Calibrate anomaly thresholds using validation data
  5. Save trained model for inference
==============================================================================
"""

import numpy as np
import json
import os
import time
from datetime import datetime, timezone

# Add parent to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dl_model.model import AnomalyAutoencoder


class SyntheticDataGenerator:
    """
    Generates realistic synthetic sensor data for training.

    Normal operation profiles for each sensor type:
    - Vibration: Low-frequency oscillation + white noise
    - Temperature: Slow drift + occasional step changes
    - Sound: Steady baseline with random transients
    """

    def __init__(self, window_size: int = 50, seed: int = 42):
        self.window_size = window_size
        self.rng = np.random.RandomState(seed)

    def _generate_vibration_window(self, n_features: int = 10) -> np.ndarray:
        """Generate vibration features for one time window."""
        # Statistical features of normal vibration
        base_mean = self.rng.uniform(1.5, 3.5)
        base_std = self.rng.uniform(0.2, 0.8)
        base_rms = base_mean * self.rng.uniform(0.9, 1.1)
        base_peak = base_mean + base_std * self.rng.uniform(1.5, 3.0)
        base_kurtosis = self.rng.uniform(-0.5, 1.5)
        base_skewness = self.rng.uniform(-0.3, 0.3)
        base_crest = base_peak / base_rms if base_rms > 0 else 1.0
        base_slope = self.rng.uniform(-0.01, 0.01)
        base_p2p = base_peak - (base_mean - base_std * 1.5)
        base_min = base_mean - base_std * self.rng.uniform(1.0, 2.5)

        features = [base_mean, base_std, base_min, base_peak,
                     base_rms, base_p2p, base_crest, base_kurtosis,
                     base_skewness, base_slope]
        return np.array(features[:n_features])

    def _generate_temperature_window(self, n_features: int = 10) -> np.ndarray:
        """Generate temperature features for one time window."""
        base_mean = self.rng.uniform(45, 65)
        base_std = self.rng.uniform(1.0, 4.0)
        base_rms = np.sqrt(base_mean**2 + base_std**2)
        base_max = base_mean + base_std * self.rng.uniform(1.0, 2.5)
        base_min = base_mean - base_std * self.rng.uniform(1.0, 2.5)
        base_kurtosis = self.rng.uniform(-1.0, 0.5)
        base_skewness = self.rng.uniform(-0.2, 0.2)
        base_crest = base_max / base_rms if base_rms > 0 else 1.0
        base_slope = self.rng.uniform(-0.005, 0.005)
        base_p2p = base_max - base_min

        features = [base_mean, base_std, base_min, base_max,
                     base_rms, base_p2p, base_crest, base_kurtosis,
                     base_skewness, base_slope]
        return np.array(features[:n_features])

    def _generate_sound_window(self, n_features: int = 10) -> np.ndarray:
        """Generate sound features for one time window."""
        base_mean = self.rng.uniform(65, 80)
        base_std = self.rng.uniform(2.0, 5.0)
        base_rms = base_mean * self.rng.uniform(0.95, 1.05)
        base_max = base_mean + base_std * self.rng.uniform(1.5, 3.0)
        base_min = base_mean - base_std * self.rng.uniform(1.0, 2.0)
        base_kurtosis = self.rng.uniform(-0.5, 1.0)
        base_skewness = self.rng.uniform(-0.1, 0.3)
        base_crest = base_max / base_rms if base_rms > 0 else 1.0
        base_slope = self.rng.uniform(-0.008, 0.008)
        base_p2p = base_max - base_min

        features = [base_mean, base_std, base_min, base_max,
                     base_rms, base_p2p, base_crest, base_kurtosis,
                     base_skewness, base_slope]
        return np.array(features[:n_features])

    def generate_normal_dataset(self, n_samples: int = 1000) -> np.ndarray:
        """
        Generate a full dataset of normal operating feature vectors.
        Each sample = [vib_features(10) + temp_features(10) + sound_features(10)]
        Total feature dim = 30
        """
        dataset = np.zeros((n_samples, 30))
        for i in range(n_samples):
            dataset[i, 0:10] = self._generate_vibration_window()
            dataset[i, 10:20] = self._generate_temperature_window()
            dataset[i, 20:30] = self._generate_sound_window()
            # Add inter-sample noise
            dataset[i] += self.rng.randn(30) * 0.05

        return dataset

    def generate_anomaly_dataset(self, n_samples: int = 200,
                                  anomaly_type: str = "bearing_wear") -> np.ndarray:
        """Generate anomalous data for testing."""
        normal = self.generate_normal_dataset(n_samples)

        if anomaly_type == "bearing_wear":
            # Elevated vibration, mild temperature increase
            normal[:, 0] *= self.rng.uniform(2.0, 3.5, n_samples)  # mean
            normal[:, 1] *= self.rng.uniform(1.5, 3.0, n_samples)  # std
            normal[:, 4] *= self.rng.uniform(1.8, 3.0, n_samples)  # rms
            normal[:, 7] += self.rng.uniform(1.0, 4.0, n_samples)  # kurtosis
            normal[:, 10] += self.rng.uniform(5, 15, n_samples)     # temp mean

        elif anomaly_type == "overheating":
            # Strong temperature increase, mild vibration
            normal[:, 10] += self.rng.uniform(20, 40, n_samples)   # temp mean
            normal[:, 13] += self.rng.uniform(10, 25, n_samples)   # temp max
            normal[:, 0] *= self.rng.uniform(1.1, 1.5, n_samples)  # vib mean

        elif anomaly_type == "misalignment":
            # Strong vibration harmonics, sound increase
            normal[:, 0] *= self.rng.uniform(2.5, 4.0, n_samples)
            normal[:, 4] *= self.rng.uniform(2.0, 3.5, n_samples)
            normal[:, 20] += self.rng.uniform(10, 20, n_samples)   # sound mean
            normal[:, 23] += self.rng.uniform(8, 18, n_samples)    # sound max

        return normal


class ModelTrainer:
    """
    Trains the autoencoder with simplified gradient descent.
    Uses reconstruction loss (MSE) with mini-batch SGD.
    """

    def __init__(self, model: AnomalyAutoencoder, learning_rate: float = 0.001):
        self.model = model
        self.lr = learning_rate

    def _compute_loss(self, x: np.ndarray) -> tuple[float, np.ndarray]:
        """Compute MSE loss between normalized input and reconstruction."""
        x_norm = self.model._normalize(x)
        x_recon = self.model.forward(x)   # forward normalizes internally
        loss = float(np.mean((x_norm - x_recon) ** 2))
        return loss, x_recon

    def _backward(self, x: np.ndarray, x_recon: np.ndarray):
        """
        Backpropagate MSE loss through the autoencoder.

        dL/d_recon = 2 * (x_recon - x_norm) / N
        Gradients flow: decoder (reversed) → encoder (reversed)
        """
        x_norm = self.model._normalize(x)
        n = x_norm.shape[0]
        d = 2.0 * (x_recon - x_norm) / n   # dL/d_output, shape (batch, input_dim)

        # Backprop through decoder layers (reverse order)
        for layer in reversed(self.model.decoder_layers):
            d = layer.backward(d)

        # Backprop through encoder layers (reverse order)
        for layer in reversed(self.model.encoder_layers):
            d = layer.backward(d)

    def _apply_gradients(self):
        """Update all layer weights with the computed gradients."""
        all_layers = self.model.encoder_layers + self.model.decoder_layers
        for layer in all_layers:
            layer.apply_gradients(self.lr)

    def train(self, train_data: np.ndarray, val_data: np.ndarray,
              epochs: int = 50, batch_size: int = 32,
              verbose: bool = True) -> dict:
        """
        Train the autoencoder using mini-batch gradient descent with
        real backpropagation (MSE reconstruction loss).
        """
        # Compute normalization statistics from training data
        self.model.input_mean = np.mean(train_data, axis=0)
        self.model.input_std = np.std(train_data, axis=0) + 1e-8

        n_samples = len(train_data)
        history = {"train_loss": [], "val_loss": [], "epochs": []}

        if verbose:
            print(f"\n[TRAINING] Starting training: {n_samples} samples, "
                  f"{epochs} epochs, batch_size={batch_size}, lr={self.lr}")

        best_val_loss = float("inf")
        best_encoder = [dict(w=l.weights.copy(), b=l.biases.copy())
                        for l in self.model.encoder_layers]
        best_decoder = [dict(w=l.weights.copy(), b=l.biases.copy())
                        for l in self.model.decoder_layers]
        patience = 10
        patience_counter = 0

        for epoch in range(epochs):
            # Shuffle training data
            indices = np.random.permutation(n_samples)
            epoch_loss = 0.0
            n_batches = 0

            for start in range(0, n_samples, batch_size):
                batch_idx = indices[start:start + batch_size]
                batch = train_data[batch_idx]

                # Forward pass
                loss, x_recon = self._compute_loss(batch)
                epoch_loss += loss
                n_batches += 1

                # Backward pass (real gradients via chain rule)
                self._backward(batch, x_recon)

                # Gradient descent weight update
                self._apply_gradients()

            avg_train_loss = epoch_loss / n_batches

            # Validation loss (no gradient update)
            val_loss, _ = self._compute_loss(val_data)

            history["epochs"].append(epoch)
            history["train_loss"].append(float(avg_train_loss))
            history["val_loss"].append(float(val_loss))

            # Save best weights (early stopping)
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                best_encoder = [dict(w=l.weights.copy(), b=l.biases.copy())
                                for l in self.model.encoder_layers]
                best_decoder = [dict(w=l.weights.copy(), b=l.biases.copy())
                                for l in self.model.decoder_layers]
            else:
                patience_counter += 1

            if verbose and (epoch % 10 == 0 or epoch == epochs - 1):
                print(f"  Epoch {epoch+1:3d}/{epochs}: "
                      f"train_loss={avg_train_loss:.6f} "
                      f"val_loss={val_loss:.6f}")

            if patience_counter >= patience:
                if verbose:
                    print(f"  Early stopping at epoch {epoch+1}")
                break

        # Restore best weights
        for layer, saved in zip(self.model.encoder_layers, best_encoder):
            layer.weights = saved["w"]
            layer.biases = saved["b"]
        for layer, saved in zip(self.model.decoder_layers, best_decoder):
            layer.weights = saved["w"]
            layer.biases = saved["b"]

        # Calibrate anomaly thresholds on validation data
        self._calibrate_thresholds(val_data)
        self.model.is_trained = True
        self.model.training_history = history

        if verbose:
            print(f"\n[TRAINING] Complete. Best val_loss: {best_val_loss:.6f}")
            print(f"  Warning threshold:  {self.model.threshold_warning:.6f}")
            print(f"  Critical threshold: {self.model.threshold_critical:.6f}")

        return history

    def _calibrate_thresholds(self, normal_data: np.ndarray):
        """Set anomaly thresholds based on normal data distribution."""
        errors = self.model.compute_reconstruction_error(normal_data)
        self.model.threshold_warning = float(np.percentile(errors, 90))
        self.model.threshold_critical = float(np.percentile(errors, 97))


def features_to_vector(features: dict) -> np.ndarray:
    """
    Convert extracted features dict (from cloud_pipeline) to model input vector.

    Maps:
    features["vibration"] → indices 0-9
    features["temperature"] → indices 10-19
    features["sound"] → indices 20-29
    """
    vector = np.zeros(30)
    feature_keys = ["mean", "std", "min", "max", "rms",
                    "peak_to_peak", "crest_factor", "kurtosis",
                    "skewness", "slope"]

    for i, sensor_type in enumerate(["vibration", "temperature", "sound"]):
        offset = i * 10
        sensor_data = features.get(sensor_type, {})
        if "error" in sensor_data:
            continue
        for j, key in enumerate(feature_keys):
            vector[offset + j] = sensor_data.get(key, 0.0)

    return vector


# ── Standalone demo ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  PART 4b: MODEL TRAINING - Standalone Demo")
    print("=" * 60)

    # Generate training data
    gen = SyntheticDataGenerator(seed=42)
    print("\n[DEMO] Generating synthetic datasets...")
    train_data = gen.generate_normal_dataset(n_samples=800)
    val_data = gen.generate_normal_dataset(n_samples=200)
    print(f"  Training: {train_data.shape} | Validation: {val_data.shape}")

    # Create and train model
    model = AnomalyAutoencoder(input_dim=30, latent_dim=32)
    trainer = ModelTrainer(model, learning_rate=0.001)
    history = trainer.train(train_data, val_data, epochs=50, batch_size=32)

    # Test on normal data
    print("\n[DEMO] Evaluating on normal test data:")
    test_normal = gen.generate_normal_dataset(n_samples=50)
    for i in range(3):
        result = model.compute_anomaly_score(test_normal[i:i+1])
        print(f"  Normal sample {i+1}: score={result['score']:.6f} "
              f"class={result['classification']} health={result['health_pct']}%")

    # Test on anomalous data
    print("\n[DEMO] Evaluating on anomalous data:")
    for anomaly_type in ["bearing_wear", "overheating", "misalignment"]:
        test_anom = gen.generate_anomaly_dataset(n_samples=10,
                                                  anomaly_type=anomaly_type)
        result = model.compute_anomaly_score(test_anom[0:1])
        print(f"  {anomaly_type}: score={result['score']:.6f} "
              f"class={result['classification']} health={result['health_pct']}%")

    # Save trained model
    model_path = os.path.join(os.path.dirname(__file__), "trained_model.json")
    model.save(model_path)

    print("\n[DEMO] Model training demo complete.")