"""Session-owned FAST work with a cancellable debounce and input identity."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import CancelledError, Executor, Future
from dataclasses import dataclass
from threading import Event

from prescriptxai.machine_schema import MachineRecourseResult

DEBOUNCE_SECONDS = 0.4


@dataclass(frozen=True)
class PrescriptionJob:
    """Only the session's current job may be published."""

    input_hash: str
    future: Future[MachineRecourseResult]
    cancelled: Event

    @classmethod
    def start(
        cls,
        executor: Executor,
        input_hash: str,
        solve: Callable[[Event], MachineRecourseResult],
    ) -> PrescriptionJob:
        """Delay a solve until the session's recorded inputs settle."""
        cancelled = Event()

        def run() -> MachineRecourseResult:
            if cancelled.wait(DEBOUNCE_SECONDS):
                raise CancelledError()
            try:
                return solve(cancelled)
            finally:
                if cancelled.is_set():
                    raise CancelledError()

        return cls(input_hash, executor.submit(run), cancelled)

    def cancel(self) -> None:
        """Cancel work before entry and discard results of superseded running calls."""
        self.cancelled.set()
        self.future.cancel()
