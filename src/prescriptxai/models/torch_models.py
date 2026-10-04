"""Deterministic differentiable snapshot and sequence predictors built with PyTorch."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import joblib
import numpy as np
import torch
from numpy.typing import NDArray
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils.validation import check_is_fitted
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from prescriptxai.models.base import FailureModel, validate_binary_labels, validate_feature_matrix


def _set_determinism(seed: int, deterministic: bool) -> torch.Generator:
    """Set framework seeds and return the deterministic data-order generator."""
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(deterministic)
    torch.backends.cudnn.deterministic = deterministic
    torch.backends.cudnn.benchmark = False
    return torch.Generator(device="cpu").manual_seed(seed)


def _validate_targets(targets: NDArray[np.float64], row_count: int) -> None:
    """Validate finite probability targets, which may be hard or distilled labels."""
    if targets.ndim != 1 or len(targets) != row_count:
        raise ValueError("targets must be one-dimensional and match feature rows")
    if not np.isfinite(targets).all() or ((targets < 0) | (targets > 1)).any():
        raise ValueError("targets must be finite probabilities within [0, 1]")


def _validate_sequence_matrix(
    features: NDArray[np.float64],
    expected_window: int | None = None,
    expected_features: int | None = None,
) -> None:
    """Validate an ``(n, window, features)`` finite, nonempty sequence tensor."""
    if features.ndim != 3:
        raise ValueError("sequence features must have shape (n, window, features)")
    if features.shape[0] == 0 or features.shape[1] == 0 or features.shape[2] == 0:
        raise ValueError("sequence features must have nonzero samples, timesteps, and features")
    if expected_window is not None and features.shape[1] != expected_window:
        raise ValueError(f"expected sequence window {expected_window}, got {features.shape[1]}")
    if expected_features is not None and features.shape[2] != expected_features:
        raise ValueError(f"expected {expected_features} sequence features, got {features.shape[2]}")
    if not np.isfinite(features).all():
        raise ValueError("sequence features must be finite")


def _fit_network(
    network: nn.Module,
    features: NDArray[np.float64],
    targets: NDArray[np.float64],
    validation_data: tuple[NDArray[np.float64], NDArray[np.float64]] | None,
    *,
    learning_rate: float,
    epochs: int,
    batch_size: int,
    seed: int,
    device: str,
    patience: int,
    gradient_clip_norm: float,
    deterministic: bool,
    sequence: bool,
    loss_kind: str = "bce",
) -> nn.Module:
    """Optimize a network with validation loss, early stopping, and clipped gradients."""
    if learning_rate <= 0 or epochs < 1 or batch_size < 1 or patience < 1:
        raise ValueError("learning rate, epochs, batch size, and patience must be positive")
    if gradient_clip_norm <= 0:
        raise ValueError("gradient_clip_norm must be positive")
    if device.startswith("cuda") and not torch.cuda.is_available():
        raise ValueError("CUDA was requested but is not available")
    if sequence:
        _validate_sequence_matrix(features)
    else:
        validate_feature_matrix(features)
    _validate_targets(targets, len(features))
    generator = _set_determinism(seed, deterministic)
    x_tensor = torch.as_tensor(features, dtype=torch.float32)
    y_tensor = torch.as_tensor(targets, dtype=torch.float32).reshape(-1, 1)
    loader = DataLoader(
        TensorDataset(x_tensor, y_tensor), batch_size=batch_size, shuffle=True, generator=generator
    )
    validation_tensors: tuple[torch.Tensor, torch.Tensor] | None = None
    if validation_data is not None:
        val_x, val_y = validation_data
        if sequence:
            _validate_sequence_matrix(val_x, features.shape[1], features.shape[2])
        else:
            validate_feature_matrix(val_x, features.shape[-1])
        _validate_targets(val_y, len(val_x))
        validation_tensors = (
            torch.as_tensor(val_x, dtype=torch.float32, device=device),
            torch.as_tensor(val_y, dtype=torch.float32, device=device).reshape(-1, 1),
        )

    model = network.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    bce = nn.BCEWithLogitsLoss()
    best_loss = float("inf")
    best_state: dict[str, torch.Tensor] | None = None
    stale_epochs = 0
    for _ in range(epochs):
        model.train()
        for batch_features, batch_targets in loader:
            optimizer.zero_grad(set_to_none=True)
            logits = model(batch_features.to(device))
            loss = (
                bce(logits, batch_targets.to(device))
                if loss_kind == "bce"
                else torch.mean((torch.sigmoid(logits) - batch_targets.to(device)) ** 2)
            )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), gradient_clip_norm)
            optimizer.step()
        if validation_tensors is None:
            continue
        model.eval()
        with torch.no_grad():
            val_x_tensor, val_y_tensor = validation_tensors
            val_logits = model(val_x_tensor)
            val_loss = (
                bce(val_logits, val_y_tensor)
                if loss_kind == "bce"
                else torch.mean((torch.sigmoid(val_logits) - val_y_tensor) ** 2)
            )
            score = float(val_loss.cpu())
        if score < best_loss - 1e-8:
            best_loss = score
            best_state = {
                key: value.detach().cpu().clone() for key, value in model.state_dict().items()
            }
            stale_epochs = 0
        else:
            stale_epochs += 1
            if stale_epochs >= patience:
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    return model.eval()


class TorchMLPClassifier(ClassifierMixin, BaseEstimator):  # type: ignore[misc]
    """Scikit-learn compatible two-column MLP retained for legacy integrations."""

    def __init__(
        self,
        hidden_dims: tuple[int, ...] = (64, 32),
        learning_rate: float = 0.001,
        epochs: int = 100,
        batch_size: int = 128,
        seed: int = 1729,
        device: str = "cpu",
        early_stopping_patience: int = 12,
        gradient_clip_norm: float = 1.0,
        deterministic: bool = True,
    ) -> None:
        self.hidden_dims = hidden_dims
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.seed = seed
        self.device = device
        self.early_stopping_patience = early_stopping_patience
        self.gradient_clip_norm = gradient_clip_norm
        self.deterministic = deterministic

    def _make_network(self, input_dim: int) -> nn.Sequential:
        """Construct an MLP from the configured hidden layer widths."""
        layers: list[nn.Module] = []
        previous = input_dim
        for width in self.hidden_dims:
            layers.extend((nn.Linear(previous, width), nn.ReLU()))
            previous = width
        layers.append(nn.Linear(previous, 1))
        return nn.Sequential(*layers)

    def fit(
        self,
        features: NDArray[np.float64],
        labels: NDArray[np.int64],
        validation_data: tuple[NDArray[np.float64], NDArray[np.int64]] | None = None,
    ) -> TorchMLPClassifier:
        """Fit binary labels, optionally early-stopping on engine-disjoint validation rows."""
        validate_feature_matrix(features)
        validate_binary_labels(labels, len(features))
        if any(width < 1 for width in self.hidden_dims):
            raise ValueError("hidden_dims values must be positive")
        _set_determinism(self.seed, self.deterministic)
        self.network_ = _fit_network(
            self._make_network(features.shape[1]),
            features,
            np.asarray(labels, dtype=np.float64),
            None
            if validation_data is None
            else (validation_data[0], np.asarray(validation_data[1], dtype=float)),
            learning_rate=self.learning_rate,
            epochs=self.epochs,
            batch_size=self.batch_size,
            seed=self.seed,
            device=self.device,
            patience=self.early_stopping_patience,
            gradient_clip_norm=self.gradient_clip_norm,
            deterministic=self.deterministic,
            sequence=False,
        )
        self.network_.to(self.device)
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
        return np.column_stack((1.0 - positive, positive))

    def __sklearn_is_fitted__(self) -> bool:
        """Expose fitted state to scikit-learn validation helpers."""
        return hasattr(self, "network_")


class MLPFailureModel(FailureModel):
    """Differentiable MLP snapshot predictor used by gradient-based recourse."""

    supports_gradients = True

    def __init__(
        self,
        hidden_dims: tuple[int, ...] = (64, 32),
        learning_rate: float = 0.001,
        epochs: int = 100,
        batch_size: int = 128,
        seed: int = 1729,
        device: str = "cpu",
        early_stopping_patience: int = 12,
        gradient_clip_norm: float = 1.0,
        deterministic: bool = True,
    ) -> None:
        self.hidden_dims = hidden_dims
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.seed = seed
        self.device = device
        self.early_stopping_patience = early_stopping_patience
        self.gradient_clip_norm = gradient_clip_norm
        self.deterministic = deterministic
        self.network_: nn.Sequential | None = None

    def _make_network(self, input_dim: int) -> nn.Sequential:
        """Build the snapshot MLP with a probability logit output."""
        layers: list[nn.Module] = []
        previous = input_dim
        for width in self.hidden_dims:
            layers.extend((nn.Linear(previous, width), nn.ReLU()))
            previous = width
        layers.append(nn.Linear(previous, 1))
        return nn.Sequential(*layers)

    def fit(
        self,
        features: NDArray[np.float64],
        labels: NDArray[np.float64],
        validation_data: tuple[NDArray[np.float64], NDArray[np.float64]] | None = None,
    ) -> MLPFailureModel:
        """Fit the MLP, using only the supplied validation partition for early stopping."""
        validate_feature_matrix(features)
        validate_binary_labels(labels, len(features))
        self.network_ = self._fit(
            features, np.asarray(labels, dtype=np.float64), validation_data, "bce"
        )
        self.n_features_in_ = features.shape[1]
        return self

    def _fit(
        self,
        features: NDArray[np.float64],
        targets: NDArray[np.float64],
        validation_data: tuple[NDArray[np.float64], NDArray[np.float64]] | None,
        loss_kind: str,
    ) -> nn.Sequential:
        """Train the network for hard-label prediction or soft-target distillation."""
        if any(width < 1 for width in self.hidden_dims):
            raise ValueError("hidden_dims values must be positive")
        _set_determinism(self.seed, self.deterministic)
        network = _fit_network(
            self._make_network(features.shape[1]),
            features,
            targets,
            validation_data,
            learning_rate=self.learning_rate,
            epochs=self.epochs,
            batch_size=self.batch_size,
            seed=self.seed,
            device=self.device,
            patience=self.early_stopping_patience,
            gradient_clip_norm=self.gradient_clip_norm,
            deterministic=self.deterministic,
            sequence=False,
            loss_kind=loss_kind,
        )
        return network  # type: ignore[return-value]

    def fit_distillation(
        self,
        features: NDArray[np.float64],
        teacher_probabilities: NDArray[np.float64],
        validation_data: tuple[NDArray[np.float64], NDArray[np.float64]],
    ) -> MLPFailureModel:
        """Fit soft probabilities from the XGBoost teacher, early-stopping on validation engines."""
        validate_feature_matrix(features)
        if len(teacher_probabilities) != len(features):
            raise ValueError("teacher probabilities must match training feature rows")
        _validate_targets(teacher_probabilities, len(features))
        val_features, val_targets = validation_data
        validate_feature_matrix(val_features, features.shape[1])
        _validate_targets(val_targets, len(val_features))
        self.network_ = self._fit(features, teacher_probabilities, validation_data, "mse")
        self.n_features_in_ = features.shape[1]
        return self

    def predict_proba(self, features: NDArray[np.float64]) -> NDArray[np.float64]:
        """Return positive-class probabilities as a one-dimensional vector."""
        if self.network_ is None:
            raise ValueError("MLP model has not been fitted")
        validate_feature_matrix(features, self.n_features_in_)
        tensor = torch.as_tensor(features, dtype=torch.float32, device=self.device)
        with torch.no_grad():
            values = self.torch_forward(tensor).cpu().numpy().reshape(-1)
        if not np.isfinite(values).all():
            raise ValueError("model generated non-finite probabilities")
        return np.asarray(values, dtype=np.float64)

    def torch_forward(self, x_tensor: torch.Tensor) -> torch.Tensor:
        """Forward a scaled snapshot through the differentiable MLP."""
        if self.network_ is None:
            raise ValueError("MLP model has not been fitted")
        if x_tensor.ndim != 2 or x_tensor.shape[1] != self.n_features_in_:
            raise ValueError(f"snapshot tensor must have shape (n, {self.n_features_in_})")
        if not torch.isfinite(x_tensor).all():
            raise ValueError("snapshot tensor must be finite")
        return torch.sigmoid(self.network_(x_tensor.to(self.device))).reshape(-1)

    def save(self, path: Path) -> Path:
        """Persist this fitted MLP and its architecture parameters."""
        if self.network_ is None:
            raise ValueError("cannot save an unfitted MLP model")
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        return path

    @classmethod
    def load(cls, path: Path) -> MLPFailureModel:
        """Load a fitted MLP predictor."""
        loaded = joblib.load(path)
        if not isinstance(loaded, cls):
            raise ValueError("artifact is not an MLPFailureModel")
        return loaded


class _LSTMNetwork(nn.Module):
    """LSTM feature encoder whose final output uses the latest sequence context."""

    def __init__(self, feature_count: int, hidden_size: int, layers: int) -> None:
        super().__init__()
        self.encoder = nn.LSTM(feature_count, hidden_size, num_layers=layers, batch_first=True)
        self.output = nn.Linear(hidden_size, 1)

    def forward(self, sequences: torch.Tensor) -> torch.Tensor:
        """Return the final-time-step failure logit."""
        _, (hidden, _) = self.encoder(sequences)
        return cast(torch.Tensor, self.output(hidden[-1]))


class LSTMFailureModel(FailureModel):
    """Differentiable sequence model over within-engine snapshot windows.

    Recourse may perturb only the final timestep in ``torch_forward``. Earlier timesteps encode
    observed history and stay fixed, preventing a recommendation from rewriting telemetry.
    """

    supports_gradients = True

    def __init__(
        self,
        window: int = 10,
        hidden_dims: tuple[int, ...] = (32,),
        learning_rate: float = 0.001,
        epochs: int = 100,
        batch_size: int = 128,
        seed: int = 1729,
        device: str = "cpu",
        early_stopping_patience: int = 12,
        gradient_clip_norm: float = 1.0,
        deterministic: bool = True,
    ) -> None:
        if window < 1:
            raise ValueError("LSTM window must be positive")
        self.window = window
        self.hidden_dims = hidden_dims
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.seed = seed
        self.device = device
        self.early_stopping_patience = early_stopping_patience
        self.gradient_clip_norm = gradient_clip_norm
        self.deterministic = deterministic
        self.network_: _LSTMNetwork | None = None

    def fit(
        self,
        features: NDArray[np.float64],
        labels: NDArray[np.float64],
        validation_data: tuple[NDArray[np.float64], NDArray[np.float64]] | None = None,
    ) -> LSTMFailureModel:
        """Fit sequence windows with engine-disjoint validation early stopping."""
        _validate_sequence_matrix(features, self.window)
        validate_binary_labels(labels, len(features))
        hidden = self.hidden_dims[0]
        if hidden < 1 or any(layer < 1 for layer in self.hidden_dims):
            raise ValueError("LSTM hidden dimensions must be positive")
        _set_determinism(self.seed, self.deterministic)
        network = _LSTMNetwork(features.shape[2], hidden, len(self.hidden_dims))
        fitted = _fit_network(
            network,
            features,
            np.asarray(labels, dtype=float),
            validation_data,
            learning_rate=self.learning_rate,
            epochs=self.epochs,
            batch_size=self.batch_size,
            seed=self.seed,
            device=self.device,
            patience=self.early_stopping_patience,
            gradient_clip_norm=self.gradient_clip_norm,
            deterministic=self.deterministic,
            sequence=True,
        )
        self.network_ = cast(_LSTMNetwork, fitted)
        self.n_features_in_ = features.shape[2]
        return self

    def predict_proba(self, features: NDArray[np.float64]) -> NDArray[np.float64]:
        """Return one positive-class probability for each input sequence."""
        if self.network_ is None:
            raise ValueError("LSTM model has not been fitted")
        _validate_sequence_matrix(features, self.window, self.n_features_in_)
        sequences = torch.as_tensor(features, dtype=torch.float32, device=self.device)
        with torch.no_grad():
            values = self.torch_forward(sequences).cpu().numpy().reshape(-1)
        if not np.isfinite(values).all():
            raise ValueError("model generated non-finite probabilities")
        return np.asarray(values, dtype=np.float64)

    def torch_forward(self, x_tensor: torch.Tensor) -> torch.Tensor:
        """Forward a window; callers alter only ``x_tensor[:, -1, :]`` for recourse."""
        if self.network_ is None:
            raise ValueError("LSTM model has not been fitted")
        if x_tensor.ndim != 3 or tuple(x_tensor.shape[1:]) != (self.window, self.n_features_in_):
            raise ValueError(
                f"sequence tensor must have shape (n, {self.window}, {self.n_features_in_})"
            )
        if not torch.isfinite(x_tensor).all():
            raise ValueError("sequence tensor must be finite")
        return torch.sigmoid(self.network_(x_tensor.to(self.device))).reshape(-1)

    def save(self, path: Path) -> Path:
        """Persist this fitted LSTM and its architecture parameters."""
        if self.network_ is None:
            raise ValueError("cannot save an unfitted LSTM model")
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        return path

    @classmethod
    def load(cls, path: Path) -> LSTMFailureModel:
        """Load a fitted LSTM predictor."""
        loaded = joblib.load(path)
        if not isinstance(loaded, cls):
            raise ValueError("artifact is not an LSTMFailureModel")
        return loaded
