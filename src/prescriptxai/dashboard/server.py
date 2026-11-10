"""Authenticated deployment of the installed Streamlit simulator."""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
import uvicorn

from prescriptxai.artifacts import require_deployment_manifest
from prescriptxai.security import AuthStore, tls_files
from prescriptxai.security_http import SessionGate


def serve_dashboard(settings: Path, script: str, host: str, port: int) -> int:
    """Start Streamlit with the same HTTP and WebSocket authentication boundary."""
    auth = AuthStore.from_environment()
    require_deployment_manifest()
    cert, key = tls_files()
    os.environ["PRESCRIPTXAI_DASHBOARD_CONFIG"] = str(settings)
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION"] = "true"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    application = SessionGate(st.App(script), auth, dashboard=True)
    uvicorn.run(application, host=host, port=port, ssl_certfile=cert, ssl_keyfile=key)
    return 0
