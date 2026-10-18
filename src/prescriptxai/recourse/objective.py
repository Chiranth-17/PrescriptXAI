"""Differentiable objective terms for physically bounded recourse search."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import numpy as np
import torch
from numpy.typing import NDArray

L1Mode = Literal["smooth", "split"]
PredictionLoss = Literal["hinge", "squared_hinge"]
TorchRiskFunction = Callable[[torch.Tensor], torch.Tensor]


@dataclass(frozen=True)
class ObjectiveTerms:
    """Weighted objective components and calibrated surrogate risk at one point."""

    l1: float
    prediction: float
    immutable: float
    bounds: float
    total: float
    risk: float
    feasibility: float = 0.0


class RecourseObjective:
    r"""Evaluate synopsis objective components and torch gradients.

    The decision vector contains scaled changes for controllable features only. Immutable and
    dependent channels are not variables; the former therefore have a hard-zero change and the
    latter are propagated inside ``risk_function``. Physical bounds are also passed to L-BFGS-B;
    the penalty remains available as a separately reported term and is zero in the feasible box.
    """

    def __init__(
        self,
        risk_function: TorchRiskFunction,
        lower_change: NDArray[np.float64],
        upper_change: NDArray[np.float64],
        *,
        safe_threshold: float,
        safety_margin: float,
        alpha: float,
        beta: float,
        gamma: float,
        l1_weight: float,
        l1_mode: L1Mode,
        smoothing_epsilon: float,
        prediction_loss: PredictionLoss,
        device: torch.device | str = "cpu",
        feasibility_function: Callable[[torch.Tensor], torch.Tensor] | None = None,
        feasibility_weight: float = 0.0,
    ) -> None:
        """Validate objective settings and bind risk, bound, and loss functions."""
        if lower_change.ndim != 1 or upper_change.shape != lower_change.shape:
            raise ValueError("change bounds must be aligned one-dimensional vectors")
        if (
            lower_change.size == 0
            or not np.isfinite(lower_change).all()
            or not np.isfinite(upper_change).all()
        ):
            raise ValueError("change bounds must be nonempty and finite")
        if np.any(lower_change > upper_change):
            raise ValueError("lower change bounds must not exceed upper change bounds")
        if not 0 < safe_threshold < 1 or not 0 <= safety_margin < safe_threshold:
            raise ValueError("safe threshold and safety margin are invalid")
        if any(not np.isfinite(value) or value < 0 for value in (alpha, beta, gamma)):
            raise ValueError("objective weights must be finite and nonnegative")
        if not np.isfinite(l1_weight) or l1_weight <= 0:
            raise ValueError("l1_weight must be positive and finite")
        if not np.isfinite(smoothing_epsilon) or smoothing_epsilon <= 0:
            raise ValueError("smoothing_epsilon must be positive and finite")
        self.risk_function = risk_function
        self.lower_change = np.asarray(lower_change, dtype=np.float64)
        self.upper_change = np.asarray(upper_change, dtype=np.float64)
        self.safe_threshold = safe_threshold
        self.safety_margin = safety_margin
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.l1_weight = l1_weight
        self.l1_mode = l1_mode
        self.smoothing_epsilon = smoothing_epsilon
        self.prediction_loss = prediction_loss
        self.device = torch.device(device)
        if not np.isfinite(feasibility_weight) or feasibility_weight < 0:
            raise ValueError("feasibility_weight must be finite and nonnegative")
        self.feasibility_function = feasibility_function
        self.feasibility_weight = feasibility_weight

    @property
    def control_count(self) -> int:
        """Number of controllable scaled feature changes."""
        return int(self.lower_change.size)

    @property
    def decision_bounds(self) -> tuple[tuple[float, float], ...]:
        """Return independent L-BFGS-B bounds for smooth or positive/negative variables."""
        if self.l1_mode == "smooth":
            return tuple(
                (float(lower), float(upper))
                for lower, upper in zip(self.lower_change, self.upper_change, strict=True)
            )
        positive_lower = np.maximum(self.lower_change, 0.0)
        positive_upper = np.maximum(self.upper_change, 0.0)
        negative_lower = np.maximum(-self.upper_change, 0.0)
        negative_upper = np.maximum(-self.lower_change, 0.0)
        bounds = tuple(
            (float(lower), float(upper))
            for lower, upper in zip(positive_lower, positive_upper, strict=True)
        )
        bounds += tuple(
            (float(lower), float(upper))
            for lower, upper in zip(negative_lower, negative_upper, strict=True)
        )
        return bounds

    def encode(self, delta: NDArray[np.float64]) -> NDArray[np.float64]:
        """Encode scaled changes as direct variables or nonnegative positive/negative parts."""
        values = np.asarray(delta, dtype=np.float64)
        if values.shape != (self.control_count,) or not np.isfinite(values).all():
            raise ValueError("delta must be a finite vector aligned with controllable features")
        if self.l1_mode == "smooth":
            return values.copy()
        positive = np.maximum(values, 0.0)
        negative = np.maximum(-values, 0.0)
        return np.concatenate((positive, negative))

    def decode(
        self, decision: NDArray[np.float64] | torch.Tensor
    ) -> NDArray[np.float64] | torch.Tensor:
        """Recover feature changes from the configured solver parameterization."""
        expected = self.control_count if self.l1_mode == "smooth" else 2 * self.control_count
        if decision.ndim != 1 or decision.shape[0] != expected:
            raise ValueError(f"decision must be a vector of length {expected}")
        if self.l1_mode == "smooth":
            return decision
        return decision[: self.control_count] - decision[self.control_count :]

    def torch_terms(self, decision: torch.Tensor) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        """Return weighted terms as torch scalars for autograd and diagnostics."""
        if decision.ndim != 1:
            raise ValueError("decision must be one-dimensional")
        delta = self.decode(decision)
        assert isinstance(delta, torch.Tensor)
        if self.l1_mode == "split":
            l1_value = decision.sum()
        else:
            epsilon = torch.as_tensor(
                self.smoothing_epsilon, dtype=decision.dtype, device=decision.device
            )
            l1_value = (torch.sqrt(delta.square() + epsilon.square()) - epsilon).sum()
        risk = self.risk_function(delta).reshape(()).to(dtype=decision.dtype)
        hinge = torch.relu(risk - (self.safe_threshold - self.safety_margin))
        prediction_value = hinge.square() if self.prediction_loss == "squared_hinge" else hinge
        lower = torch.as_tensor(self.lower_change, dtype=decision.dtype, device=decision.device)
        upper = torch.as_tensor(self.upper_change, dtype=decision.dtype, device=decision.device)
        violation = torch.relu(lower - delta).square() + torch.relu(delta - upper).square()
        bounds_value = violation.sum()
        # All immutable coordinates are excluded from the decision vector, so beta multiplies 0.
        immutable_value = torch.zeros((), dtype=decision.dtype, device=decision.device)
        terms = {
            "l1": self.l1_weight * l1_value,
            "prediction": self.alpha * prediction_value,
            "immutable": self.beta * immutable_value,
            "bounds": self.gamma * bounds_value,
            "feasibility": (
                self.feasibility_weight * self.feasibility_function(delta)
                if self.feasibility_function is not None
                else torch.zeros_like(risk)
            ),
        }
        total = torch.stack(tuple(terms.values())).sum()
        return total, {**terms, "risk": risk}

    def value_and_grad(self, decision: NDArray[np.float64]) -> tuple[float, NDArray[np.float64]]:
        """Calculate objective and gradient using torch autograd for SciPy."""
        values = np.asarray(decision, dtype=np.float64)
        if values.shape != (len(self.decision_bounds),) or not np.isfinite(values).all():
            raise ValueError(
                "decision must be finite and align with the configured parameterization"
            )
        tensor = torch.tensor(values, dtype=torch.float64, device=self.device, requires_grad=True)
        objective, _ = self.torch_terms(tensor)
        gradient = torch.autograd.grad(objective, tensor)[0]
        output = np.asarray(gradient.detach().cpu().numpy(), dtype=np.float64)
        if not np.isfinite(output).all() or not np.isfinite(float(objective.detach())):
            raise ValueError("objective or gradient is non-finite")
        return float(objective.detach()), output

    def components(self, decision: NDArray[np.float64]) -> ObjectiveTerms:
        """Return weighted objective terms and risk as plain numeric fields."""
        values = np.asarray(decision, dtype=np.float64)
        if values.shape != (len(self.decision_bounds),) or not np.isfinite(values).all():
            raise ValueError(
                "decision must be finite and align with the configured parameterization"
            )
        tensor = torch.as_tensor(values, dtype=torch.float64, device=self.device)
        with torch.no_grad():
            total, terms = self.torch_terms(tensor)
        return ObjectiveTerms(
            l1=float(terms["l1"]),
            prediction=float(terms["prediction"]),
            immutable=float(terms["immutable"]),
            bounds=float(terms["bounds"]),
            total=float(total),
            risk=float(terms["risk"]),
            feasibility=float(terms["feasibility"]),
        )


def prediction_flip_loss(
    risk: float,
    safe_threshold: float,
    *,
    safety_margin: float = 0.0,
    squared: bool = True,
) -> float:
    """Return a hinge penalty above ``safe_threshold - safety_margin``."""
    if not np.isfinite(risk) or not 0 <= risk <= 1:
        raise ValueError("risk must be finite and within [0, 1]")
    if not 0 < safe_threshold < 1 or not 0 <= safety_margin < safe_threshold:
        raise ValueError("safe_threshold and safety_margin are invalid")
    hinge = max(0.0, risk - safe_threshold + safety_margin)
    return float(hinge**2 if squared else hinge)


def scaled_l1_distance(candidate: NDArray[np.float64], original: NDArray[np.float64]) -> float:
    """Return L1 distance in scaled feature space, validating aligned finite vectors."""
    if candidate.ndim != 1 or original.ndim != 1 or candidate.shape != original.shape:
        raise ValueError("candidate and original must be same-shaped one-dimensional vectors")
    if not np.isfinite(candidate).all() or not np.isfinite(original).all():
        raise ValueError("candidate and original vectors must be finite")
    return float(np.abs(candidate - original).sum())


def recourse_objective(
    candidate: NDArray[np.float64],
    original: NDArray[np.float64],
    predicted_risk: float,
    safe_threshold: float,
    prediction_weight: float,
) -> float:
    """Compute scaled L1 change plus weighted squared prediction hinge loss."""
    if prediction_weight <= 0 or not np.isfinite(prediction_weight):
        raise ValueError("prediction_weight must be positive and finite")
    return scaled_l1_distance(candidate, original) + prediction_weight * prediction_flip_loss(
        predicted_risk, safe_threshold
    )
