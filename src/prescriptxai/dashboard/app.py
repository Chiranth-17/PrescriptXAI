"""Streamlit operator interface for validated PrescriptXAI recommendations."""

from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

from prescriptxai.config import load_config
from prescriptxai.constraints.taxonomy import load_taxonomy
from prescriptxai.dashboard.components import show_recommendation
from prescriptxai.dashboard.state import parse_state_document
from prescriptxai.logging_utils import configure_logging
from prescriptxai.pipeline import PrescriptXAIEngine

LOGGER = logging.getLogger(__name__)


def main() -> None:
    """Render the configured dashboard without synthetic defaults or case-study values."""
    configure_logging()
    st.set_page_config(page_title="PrescriptXAI", layout="wide")
    st.title("PrescriptXAI · Prescriptive Maintenance")
    st.warning(
        "C-MAPSS is static run-to-failure data. This tool does not establish real-machine safety "
        "or RUL extension. Model validity and physical plausibility are separate checks."
    )
    config_path = Path("configs/default.yaml")
    taxonomy_path = Path("configs/features.yaml")
    config = load_config(config_path)
    taxonomy = load_taxonomy(taxonomy_path)
    if not config.artifacts.model.is_file() or not config.artifacts.mahalanobis.is_file():
        st.error(
            "Trained model and training-only plausibility artifacts are required. "
            "Run `prescriptxai train` first."
        )
        st.stop()
    if not taxonomy.feature_groups.controllable_actuators.features:
        st.info(
            "No verified controllable actuators are configured; recourse will report failure "
            "explicitly."
        )
    if not taxonomy.coupling_rules:
        st.info("No validated sensor-coupling rules are configured; Tier 4 will fail closed.")
    upload = st.file_uploader("Upload one raw-unit state as JSON or CSV", type=["json", "csv"])
    if upload is None:
        st.info("Upload a single state record to calculate risk and request a candidate.")
        return
    required = {
        name
        for group in taxonomy.feature_groups.model_dump().values()
        for name in group["features"]
    }
    try:
        state = parse_state_document(upload.getvalue().decode("utf-8"), upload.name, required)
    except (UnicodeDecodeError, ValueError) as error:
        st.error(str(error))
        return
    if st.button("Evaluate state", type="primary"):
        try:
            engine = PrescriptXAIEngine.from_files(config_path, taxonomy_path)
            result = engine.recommend(state)
        except (ValueError, FileNotFoundError) as error:
            LOGGER.exception("Recommendation request failed")
            st.error(str(error))
            return
        show_recommendation(result, config.model.danger_threshold, config.model.safe_threshold)


main()
