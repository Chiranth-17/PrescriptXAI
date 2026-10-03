"""Structured logging and run correlation tests."""

import json
import logging

from prescriptxai.logging_utils import JsonLogFormatter, current_run_id, new_run_id


def test_json_log_record_contains_contextual_run_id() -> None:
    """Log format includes parseable structured fields and the active per-run ID."""
    run_id = new_run_id()
    record = logging.LogRecord(
        name="prescriptxai.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="phase zero",
        args=(),
        exc_info=None,
    )

    payload = json.loads(JsonLogFormatter().format(record))

    assert current_run_id() == run_id
    assert payload["run_id"] == run_id
    assert payload["level"] == "INFO"
    assert payload["message"] == "phase zero"
