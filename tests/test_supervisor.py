"""Validation suite for Ingestion Supervisor and Watchdog operations."""

import time
import unittest
from src.spectraguard_core_infra.ingestion.enums import SourceState, SourceType
from src.spectraguard_core_infra.ingestion.models import SourceConfig
from src.spectraguard_core_infra.ingestion.base import FrameSource
from src.spectraguard_core_infra.ingestion.scheduler import FrameScheduler
from src.spectraguard_core_infra.ingestion.supervisor import IngestionSupervisor


class MockFragileSource(FrameSource):
    """A mock source that simulates sudden failures to trigger watchdog restarts."""

    def __init__(self, config):
        super().__init__(config)
        self.frame_counter = 0

    def connect(self):
        self._state = SourceState.STREAMING

    def disconnect(self):
        self._state = SourceState.STOPPED

    def read_frame(self):
        if self._state != SourceState.STREAMING:
            return False, None, 0

        self.frame_counter += 1

        # Increased to 15 frames (150ms @ 100fps) to allow the metrics test to pass
        if self.frame_counter == 15:
            self._state = SourceState.FAILED
            return False, None, 0

        return True, f"frame_data_{self.frame_counter}", time.time_ns()


class TestIngestionSupervisor(unittest.TestCase):
    def setUp(self):
        self.config = SourceConfig(
            source_id="MOCK_FRAGILE",
            source_type=SourceType.SIMULATOR,
            uri="mock://fragile",
            target_fps=100.0,
        )

        # Factory creates a fresh source and scheduler on every call
        def scheduler_factory():
            source = MockFragileSource(self.config)
            return FrameScheduler(source, max_queue_size=10)

        self.factory = scheduler_factory

    def test_supervisor_metrics(self):
        supervisor = IngestionSupervisor(self.factory, check_interval_s=0.1)

        metrics = supervisor.get_metrics()
        self.assertFalse(metrics["is_running"])
        self.assertEqual(metrics["restart_count"], 0)

        supervisor.start()

        # Wait 0.05s (approx 5 frames at 100fps), source will not have failed yet (fails at 15)
        time.sleep(0.05)
        metrics = supervisor.get_metrics()
        self.assertTrue(metrics["is_running"])
        self.assertEqual(metrics["source_state"], "STREAMING")
        self.assertGreaterEqual(metrics["uptime_seconds"], 0.0)

        supervisor.stop()

    def test_watchdog_auto_restart(self):
        supervisor = IngestionSupervisor(
            self.factory, max_restarts=2, check_interval_s=0.1
        )
        supervisor.start()

        # Let it run long enough to fail on the 15th frame, get caught by the watchdog, and restart
        time.sleep(0.3)

        metrics = supervisor.get_metrics()

        # It should have restarted at least once due to the programmed failure at frame 15
        self.assertGreater(metrics["restart_count"], 0)

        # Pull a frame to verify it is active after restart
        success, frame, ts = supervisor.get_next_frame(timeout=0.1)
        self.assertTrue(success)

        supervisor.stop()


if __name__ == "__main__":
    unittest.main()
