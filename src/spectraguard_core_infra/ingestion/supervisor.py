"""Health monitoring and failure recovery for ingestion pipelines."""

import time
import threading
from typing import Callable, Dict, Any, Optional, Tuple
from .scheduler import FrameScheduler
from .enums import SourceState


class IngestionSupervisor:
    """
    Watchdog that monitors a FrameScheduler, automatically restarting it
    upon unrecoverable failures and exposing pipeline metrics.
    """

    def __init__(
        self,
        scheduler_factory: Callable[[], FrameScheduler],
        max_restarts: int = 5,
        check_interval_s: float = 1.0,
    ):
        """
        Args:
            scheduler_factory: A callable that returns a fresh FrameScheduler instance.
            max_restarts: Maximum number of times to attempt a full pipeline restart.
            check_interval_s: How often the watchdog checks the pipeline health.
        """
        self._factory = scheduler_factory
        self._max_restarts = max_restarts
        self._check_interval = check_interval_s

        self._restart_count = 0
        self._scheduler: Optional[FrameScheduler] = None
        self._is_running = False
        self._watchdog_thread: Optional[threading.Thread] = None
        self._start_time = 0.0

    def start(self) -> None:
        """Starts the underlying scheduler and the background watchdog thread."""
        if self._is_running:
            return

        self._scheduler = self._factory()
        self._scheduler.start()

        self._start_time = time.time()
        self._is_running = True
        self._watchdog_thread = threading.Thread(
            target=self._watchdog_loop, daemon=True
        )
        self._watchdog_thread.start()

    def stop(self) -> None:
        """Stops the watchdog and safely shuts down the underlying scheduler."""
        self._is_running = False
        if self._watchdog_thread and self._watchdog_thread.is_alive():
            self._watchdog_thread.join(timeout=2.0)

        if self._scheduler:
            self._scheduler.stop()

    def _watchdog_loop(self) -> None:
        """Background thread monitoring the active scheduler's health."""
        while self._is_running:
            time.sleep(self._check_interval)

            if not self._scheduler:
                continue

            # Detect pipeline failure: Scheduler thread died OR source entered a terminal FAILED state
            scheduler_dead = not self._scheduler._is_running
            source_failed = self._scheduler._source.state == SourceState.FAILED

            if scheduler_dead or source_failed:
                if self._restart_count < self._max_restarts:
                    self._restart_count += 1

                    # Tear down the dead pipeline
                    self._scheduler.stop()

                    # Re-instantiate via the factory and start fresh
                    self._scheduler = self._factory()
                    self._scheduler.start()
                else:
                    # Max restarts exceeded, trigger terminal failure
                    self._is_running = False
                    if self._scheduler:
                        self._scheduler.stop()
                    break

    def get_metrics(self) -> Dict[str, Any]:
        """Returns a diagnostic snapshot of the ingestion pipeline health."""
        processed = self._scheduler.frames_processed if self._scheduler else 0
        dropped = self._scheduler.frames_dropped if self._scheduler else 0
        state = (
            self._scheduler._source.state.value
            if self._scheduler and self._scheduler._source
            else "UNKNOWN"
        )

        uptime = time.time() - self._start_time if self._start_time > 0 else 0.0

        return {
            "is_running": self._is_running,
            "uptime_seconds": uptime,
            "restart_count": self._restart_count,
            "source_state": state,
            "frames_processed": processed,
            "frames_dropped": dropped,
        }

    def get_next_frame(self, timeout: float = 0.5) -> Tuple[bool, Optional[Any], int]:
        """Proxies the frame retrieval request to the active scheduler."""
        if not self._scheduler or not self._is_running:
            return False, None, 0
        return self._scheduler.get_next_frame(timeout)
