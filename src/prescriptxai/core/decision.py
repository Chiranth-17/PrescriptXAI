"""Shared decision boundary for machine-scoped runtime requests."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Literal, Protocol

import pandas as pd

from prescriptxai.core.data_quality import RecommendationWithheld, require_clean_window
from prescriptxai.machine_schema import FeedbackRecord, MachineAssessment, MachineRecourseResult
from prescriptxai.machine_spec import MachineSpec
from prescriptxai.schemas import Assessment, Explanation, InputContext, RecourseResult

SearchMode = Literal["fast", "thorough"]


class DecisionRuntime(Protocol):
    """Numerical inference and validation operations used by this boundary."""

    def assess(
        self, x_raw: Mapping[str, float], context: InputContext, mode: SearchMode | None
    ) -> Assessment:
        """Score the observed state."""

    def recommend(
        self, x_raw: Mapping[str, float], context: InputContext, mode: SearchMode | None
    ) -> RecourseResult:
        """Run the bounded search and independent checks."""

    def validate_controls(
        self,
        x_raw: Mapping[str, float],
        controls: Mapping[str, float],
        context: InputContext,
        mode: SearchMode | None,
    ) -> RecourseResult:
        """Score and independently validate applied settings."""


class MachineDecision:
    """Apply a machine's quality, publication, provenance and wording policies."""

    def __init__(
        self,
        spec: MachineSpec,
        runtime: DecisionRuntime,
        features: tuple[str, ...],
        protocol_version: str,
        history_rows: int = 0,
    ) -> None:
        if protocol_version not in spec.validation.plausibility:
            raise ValueError(f"unknown protocol version: {protocol_version}")
        self.spec = spec
        self._runtime = runtime
        self.features = features
        self.history_rows = history_rows
        self.protocol_version = protocol_version

    def _observed(self, window: pd.DataFrame) -> tuple[dict[str, float], InputContext]:
        require_clean_window(window, self.spec)
        if len(window) <= self.history_rows:
            raise RecommendationWithheld(
                f"missing history: need {self.history_rows} prior observations"
            )
        names = list(self.features)
        current = {
            feature.id: float(window[feature.id].iloc[-1])
            for feature in self.spec.measurement_features
        }
        prior = window.loc[:, names].iloc[-self.history_rows - 1 : -1]
        history = tuple(
            tuple(float(value) for value in row) for row in prior.itertuples(index=False, name=None)
        )
        return current, InputContext(history=history or None)

    def _publishable(self) -> None:
        if not self.spec.confirmation.confirmed:
            raise RecommendationWithheld("Alerts only: limits not yet confirmed by an engineer")

    def assess(self, window: pd.DataFrame, mode: SearchMode | None = None) -> MachineAssessment:
        """Score the checked observation without publishing a prescription."""
        state, context = self._observed(window)
        observed = self._runtime.assess(state, context, mode)
        return MachineAssessment(
            **observed.model_dump(),
            machine_id=self.spec.machine_id,
            spec_hash=self.spec.spec_hash,
            protocol_version=self.protocol_version,
            synthetic=self.spec.synthetic,
        )

    def recommend(
        self, window: pd.DataFrame, mode: SearchMode | None = None
    ) -> MachineRecourseResult:
        """Withhold advice if quality, confirmation or a required check fails."""
        state, context = self._observed(window)
        self._publishable()
        return self._checked_result(self._runtime.recommend(state, context, mode))

    def _checked_result(self, result: RecourseResult) -> MachineRecourseResult:
        if result.alert and not (result.validation_report.joint and result.action_feasible):
            reasons = ", ".join(result.validation_report.failing_tiers)
            raise RecommendationWithheld(reasons or "no feasible adjustment passed all checks")
        return self._scoped(result)

    def _scoped(self, result: RecourseResult) -> MachineRecourseResult:
        return MachineRecourseResult.from_decision(
            result,
            machine_id=self.spec.machine_id,
            spec_hash=self.spec.spec_hash,
            protocol_version=self.protocol_version,
            synthetic=self.spec.synthetic,
        )

    def _verify_provenance(self, result: MachineRecourseResult) -> None:
        if (
            result.machine_id != self.spec.machine_id
            or result.spec_hash != self.spec.spec_hash
            or result.protocol_version != self.protocol_version
            or result.synthetic != self.spec.synthetic
        ):
            raise ValueError("decision provenance differs from the active machine and protocol")

    def explain_result(self, result: MachineRecourseResult) -> Explanation:
        """Render measured actions using the declared feature labels and wording."""
        self._verify_provenance(result)
        self._publishable()
        return self._explanation(result)

    def _explanation(self, result: MachineRecourseResult) -> Explanation:
        features = {feature.id: feature for feature in self.spec.measurement_features}
        actions = []
        for name in result.action_features if result.status == "RECOVERABLE" else ():
            feature = features[name]
            delta = result.delta_per_feature[name].raw_delta
            template = self.spec.sentences.increase if delta >= 0 else self.spec.sentences.decrease
            actions.append(
                template.format(
                    label=feature.label,
                    amount=f"{abs(delta):.6g}",
                    unit=feature.unit,
                    why=feature.why,
                )
            )
        return Explanation(
            summary=result.status if result.alert else "No intervention required",
            actions=tuple(actions),
            risk_before=result.risk_before,
            risk_after=result.risk_after,
            verdict={
                "model_valid": result.validation_report.model_valid,
                "plausible": result.plausible,
                "constraints_ok": result.constraints_ok,
                "joint": result.joint,
            },
            evidence_level=result.evidence_level,
            warnings=(*result.warnings, *result.assumptions),
        )

    def validate_controls(
        self,
        window: pd.DataFrame,
        controls: Mapping[str, float],
        mode: SearchMode | None = None,
    ) -> MachineRecourseResult:
        """Check a manually entered state without issuing a prescription."""
        state, context = self._observed(window)
        self._publishable()
        return self._scoped(self._runtime.validate_controls(state, controls, context, mode))

    def feedback(
        self,
        window: pd.DataFrame,
        result: MachineRecourseResult,
        applied: dict[str, float],
        source: Literal["operator", "simulated_operator"] = "operator",
    ) -> FeedbackRecord:
        """Recheck the applied values before constructing a local feedback row."""
        self._publishable()
        return self._measure_feedback(window, result, applied, source)

    def _measure_feedback(
        self,
        window: pd.DataFrame,
        result: MachineRecourseResult,
        applied: dict[str, float],
        source: Literal["operator", "simulated_operator"],
    ) -> FeedbackRecord:
        self._verify_provenance(result)
        state, context = self._observed(window)
        if state != result.original_state:
            raise ValueError("observed values differ from the recommendation input")
        if (
            not result.joint
            or not result.action_feasible
            or not result.action_features
            or set(applied) != set(result.action_features)
        ):
            raise ValueError("feedback requires the action fields of a feasible recommendation")
        mode: SearchMode = "fast" if result.mode == "FAST" else "thorough"
        observed = self._runtime.validate_controls(state, applied, context, mode)
        scores = action_adherence(
            result.original_state,
            result.new_state,
            applied,
        )
        report = observed.validation_report
        return FeedbackRecord(
            machine_id=self.spec.machine_id,
            spec_hash=self.spec.spec_hash,
            protocol_version=self.protocol_version,
            result_run_id=result.run_id,
            recorded_at=datetime.now(UTC),
            synthetic=self.spec.synthetic,
            source=source,
            applied=applied,
            adherence=sum(scores.values()) / len(scores),
            action_adherence=scores,
            applied_risk=observed.risk_after,
            applied_tier_passes={
                "model_valid": report.model_valid,
                "plausible": report.plausible,
                "engineering": report.tier3_engineering.passed,
                "coupling": report.tier4_sensor_coupling.passed,
            },
        )


def action_adherence(
    original: Mapping[str, float],
    proposed: Mapping[str, float],
    applied: Mapping[str, float],
) -> dict[str, float]:
    """Compute clipped adherence to each recommended action."""
    return {
        name: max(
            0.0,
            1.0 - abs(value - proposed[name]) / max(abs(proposed[name] - original[name]), 1e-12),
        )
        for name, value in applied.items()
    }
