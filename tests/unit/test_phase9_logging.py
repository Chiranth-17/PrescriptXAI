"""JSON logging remains usable after temporary CLI/caller capture streams close."""

import io
import json
import logging
from contextlib import redirect_stderr

from prescriptxai.logging_utils import configure_logging


def test_json_logging_does_not_retain_a_closed_caller_stream() -> None:
    """Library logs after a CliRunner-like capture cannot emit raw logging-error tracebacks."""
    first = io.StringIO()
    with redirect_stderr(first):
        configure_logging(run_id="first-capture")
        logging.getLogger("prescriptxai.probe").warning("first message")
    first.close()
    second = io.StringIO()
    with redirect_stderr(second):
        logging.getLogger("prescriptxai.probe").warning("second message")
    output = second.getvalue()
    assert "Logging error" not in output
    assert json.loads(output)["message"] == "second message"
