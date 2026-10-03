"""A deterministic CPU/GPU multilayer perceptron binary estimator."""

from __future__ import annotations

import numpy as np
import torch
from numpy.typing import NDArray
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils.validation import check_is_fitted
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from prescriptxai.models.base import validate_binary_labels, validate_feature_matrix


class TorchMLPClassifier(ClassifierMixin, BaseEstimator):  # type: ignore[misc]
    """Scikit-learn compatible neural network classifier for calibrated risk scoring."""

    def __init__(
        self,
        hidden_dims: tuple[int, ...] = (64, 32),
        learning_rate: float = 0.001,
        epochs: int = 100,
        batch_size: int = 128,
        seed: int = 1729,
        device: str = "cpu",
    ) -> None:
        self.hidden_dims = hidden_dims
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.seed = seed
        self.device = device

    def _make_network(self, input_dim: int) -> nn.Sequential:
        """Construct an MLP from the estimator's configured layer widths."""
        layers: list[nn.Module] = []
        previous = input_dim
        for width in self.hidden_dims:
            layers.extend((nn.Linear(previous, width), nn.ReLU()))
            previous = width
        layers.append(nn.Linear(previous, 1))
        return nn.Sequential(*layers)

    def fit(self, features: NDArray[np.float64], labels: NDArray[np.int64]) -> TorchMLPClassifier:
        """Train the classifier with deterministic CPU data ordering."""
        validate_feature_matrix(features)
        validate_binary_labels(labels, features.shape[0])
        if self.learning_rate <= 0 or self.epochs < 1 or self.batch_size < 1:
            raise ValueError("learning_rate, epochs, and batch_size must be positive")
        if any(width < 1 for width in self.hidden_dims):
            raise ValueError("hidden_dims values must be positive")
        if self.device.startswith("cuda") and not torch.cuda.is_available():
            raise ValueError("CUDA was requested but is not available")
        torch.manual_seed(self.seed)
        if self.device.startswith("cuda"):
            torch.cuda.manual_seed_all(self.seed)
        generator = torch.Generator(device="cpu").manual_seed(self.seed)
        x_tensor = torch.as_tensor(features, dtype=torch.float32)
        y_tensor = torch.as_tensor(labels, dtype=torch.float32).reshape(-1, 1)
        loader = DataLoader(
            TensorDataset(x_tensor, y_tensor),
            batch_size=self.batch_size,
            shuffle=True,
            generator=generator,
        )
        network = self._make_network(features.shape[1]).to(self.device)
        optimizer = torch.optim.Adam(network.parameters(), lr=self.learning_rate)
        loss_function = nn.BCEWithLogitsLoss()
        network.train()
        for _ in range(self.epochs):
            for batch_features, batch_labels in loader:
                optimizer.zero_grad(set_to_none=True)
                logits = network(batch_features.to(self.device))
                loss = loss_function(logits, batch_labels.to(self.device))
                loss.backward()
                optimizer.step()
        self.network_ = network.eval()
        self.n_features_in_ = features.shape[1]
        self.classes_ = np.asarray([0, 1], dtype=np.int64)
        return self

    def predict_proba(self, features: NDArray[np.float64]) -> NDArray[np.float64]:
        """Return negative/positive class probabilities for each row."""
        check_is_fitted(self, ["network_", "n_features_in_"])
        validate_feature_matrix(features, self.n_features_in_)
        with torch.no_grad():
            values = torch.as_tensor(features, dtype=torch.float32, device=self.device)
            positive = torch.sigmoid(self.network_(values)).cpu().numpy().reshape(-1)
        probabilities = np.column_stack((1.0 - positive, positive))
        if not np.isfinite(probabilities).all():
            raise ValueError("model generated non-finite probabilities")
        return probabilities

    def __sklearn_is_fitted__(self) -> bool:
        """Expose fitted state to recent scikit-learn validation helpers."""
        return hasattr(self, "network_")
