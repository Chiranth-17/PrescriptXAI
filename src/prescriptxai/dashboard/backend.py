"""Cached direct/API adapters to the single frozen decision-support contract."""

from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from itertools import permutations
from pathlib import Path
from typing import Any, Literal, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import streamlit as st

from prescriptxai.config import load_config
from prescriptxai.dashboard.state import DashboardSettings
from prescriptxai.pipeline import ArtifactError, InputError, PrescriptXAI
from prescriptxai.schemas import Assessment, InputContext, RecourseResult


class OperatorError(ValueError):
    """Actionable failure safe to show to an operator without a Python traceback."""


def profile_identity(path: Path) -> str:
    """Fingerprint configuration and artifact bytes, invalidating same-path replacements."""
    try:
        config = load_config(path)
        selected = config.pipeline.model_artifacts.get(config.model_choice)
        if selected is not None:
            config.artifacts = selected.model_copy(deep=True)
        paths = [
            path,
            config.pipeline.taxonomy_path,
            config.artifacts.model,
            config.artifacts.mahalanobis,
        ]
        if config.artifacts.coupling is not None:
            paths.append(config.artifacts.coupling)
        return hashlib.sha256(
            b"".join(hashlib.sha256(p.read_bytes()).digest() for p in paths)
        ).hexdigest()
    except (OSError, ValueError) as error:
        raise OperatorError(f"Selected profile/artifacts unavailable: {error}") from error


@st.cache_resource(show_spinner=False, max_entries=8)
def direct_service(path: str, identity: str) -> PrescriptXAI:
    """Cache thread-safe loaded resources by actual content identity, never fit a model."""
    del identity  # Included in the resource key; public factory independently verifies bytes.
    try:
        return PrescriptXAI.from_config(path)
    except ArtifactError as error:
        raise OperatorError(str(error)) from error


@dataclass
class Backend:
    """One selected immutable profile, with direct default and fail-closed remote parity."""

    path: Path
    identity: str
    settings: DashboardSettings

    def remote(self, route: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Call the configured API with environment-only credentials and bounded responses."""
        headers = {"Content-Type": "application/json"}
        secret = os.environ.get(self.settings.api_key_env)
        if secret:
            headers["X-API-Key"] = secret
        request = Request(
            self.settings.api_url.rstrip("/") + route,
            data=json.dumps(payload, allow_nan=False).encode() if payload is not None else None,
            headers=headers,
        )
        try:
            with urlopen(request, timeout=self.settings.timeout_seconds) as response:
                data = response.read(8 * 1024 * 1024 + 1)
            if len(data) > 8 * 1024 * 1024:
                raise OperatorError("API response exceeds the dashboard response limit")
            result = json.loads(data)
            if not isinstance(result, dict):
                raise OperatorError("API returned an invalid response object")
            return result
        except HTTPError as error:
            try:
                detail = json.loads(error.read(65536)).get("detail", "Request rejected")
            except (ValueError, AttributeError):
                detail = "Request rejected"
            raise OperatorError(f"API {error.code}: {detail}") from error
        except (URLError, TimeoutError, OSError, ValueError) as error:
            raise OperatorError(f"API unavailable or malformed response: {error}") from error

    def info(self) -> dict[str, Any]:
        """Check remote artifact/config identity against the locally selected trusted profile."""
        local = direct_service(str(self.path), self.identity).info()
        if self.settings.backend == "direct":
            return local
        remote = self.remote("/config")
        if any(
            remote.get(k) != local.get(k)
            for k in ("config_hash", "model_version", "artifact_identity")
        ):
            raise OperatorError("API profile/artifact identity differs from the selected profile")
        if local.get("artifact_identity") is None:
            raise OperatorError("API artifact identity is unavailable")
        return remote

    def call(
        self,
        operation: Literal["assess", "recommend", "validate-controls"],
        state: dict[str, float],
        context: InputContext,
        mode: Literal["fast", "thorough"],
        controls: dict[str, float] | None = None,
    ) -> Assessment | RecourseResult:
        """Use the public library for every decision; manual previews never reuse tier verdicts."""
        try:
            if self.settings.backend == "api":
                self.info()
                payload: dict[str, Any] = {
                    "state": state,
                    "context": context.model_dump(mode="json"),
                    "mode": mode,
                }
                if controls is not None:
                    payload["controls"] = controls
                raw = self.remote("/" + operation, payload)
                result = (Assessment if operation == "assess" else RecourseResult).model_validate(
                    raw
                )
                expected = direct_service(str(self.path), self.identity)
                effective = expected.config.model_copy(deep=True)
                if operation != "assess":
                    effective.recourse.search_mode = mode
                expected_hash = hashlib.sha256(
                    json.dumps(effective.model_dump(mode="json"), sort_keys=True).encode()
                ).hexdigest()
                if (
                    result.config_hash != expected_hash
                    or result.model_version != expected.model_version
                ):
                    raise OperatorError(
                        "API result identity differs from the requested profile/mode"
                    )
                return result
            service = direct_service(str(self.path), self.identity)
            if operation == "assess":
                return service.assess(state, context, mode)
            if operation == "recommend":
                return service.recommend(state, context, mode)
            return service.validate_controls(state, controls or {}, context, mode)
        except (InputError, ArtifactError, ValueError) as error:
            raise OperatorError(str(error)) from error


@st.cache_resource(show_spinner=False)
def computation_pool() -> ThreadPoolExecutor:
    """Run telemetry scoring/chart contributions away from the Streamlit script thread."""
    return ThreadPoolExecutor(max_workers=2, thread_name_prefix="operator-scoring")


@st.cache_data(show_spinner=False, max_entries=256)
def cached_assessment(
    path: str,
    identity: str,
    settings_json: str,
    state_json: str,
    context_json: str,
    mode: str,
) -> dict[str, Any]:
    """Return copied actual assessments keyed by all data, mode, API and artifact identities."""
    backend = Backend(Path(path), identity, DashboardSettings.model_validate_json(settings_json))
    if mode not in {"fast", "thorough"}:
        raise OperatorError("Unknown mode")
    result = backend.call(
        "assess",
        json.loads(state_json),
        InputContext.model_validate_json(context_json),
        cast(Literal["fast", "thorough"], mode),
    )
    return result.model_dump(mode="json")


@st.cache_data(show_spinner=False, max_entries=256)
def contribution_data(
    path: str,
    identity: str,
    settings_json: str,
    state_json: str,
    context_json: str,
    controls_json: str,
    mode: Literal["fast", "thorough"],
) -> dict[str, Any]:
    """Revalidate partial actions from the same original residual/history, with memoization."""
    backend = Backend(Path(path), identity, DashboardSettings.model_validate_json(settings_json))
    state, controls = json.loads(state_json), json.loads(controls_json)
    context = InputContext.model_validate_json(context_json)
    names = sorted(controls)
    risks: dict[tuple[str, ...], float] = {}

    def risk(subset: tuple[str, ...]) -> float:
        key = tuple(sorted(subset))
        if key not in risks:
            result = backend.call(
                "validate-controls", state, context, mode, {n: controls[n] for n in key}
            )
            assert isinstance(result, RecourseResult)
            risks[key] = result.risk_after
        return risks[key]

    sequential = [risk(tuple(names[: i + 1])) - risk(tuple(names[:i])) for i in range(len(names))]
    averaged = None
    if len(names) <= 3:
        orders = list(permutations(names))
        totals = dict.fromkeys(names, 0.0)
        for order in orders:
            for index, name in enumerate(order):
                totals[name] += risk(order[: index + 1]) - risk(order[:index])
        averaged = [totals[n] / len(orders) for n in names] if orders else []
    return {
        "names": names,
        "sequential": sequential,
        "averaged": averaged,
        "before": risk(()),
        "after": risk(tuple(names)),
        "evaluations": len(risks),
    }
