"""Actuator interval calculations for absolute bounds and rate limits."""

from prescriptxai.constraints.taxonomy import ActuatorConstraint


def allowed_interval(current: float, constraint: ActuatorConstraint) -> tuple[float, float]:
    """Intersect an actuator's absolute range with its per-step rate limit."""
    lower = max(constraint.minimum, current - constraint.max_change_per_step)
    upper = min(constraint.maximum, current + constraint.max_change_per_step)
    if lower > upper:
        raise ValueError("current actuator state and rate limit have no feasible interval")
    return lower, upper
