"""Validation suite for Frame Scheduler pacing and queue management."""

import time
import unittest
from src.spectraguard_core_infra.ingestion.enums import SourceState, SourceType
from src.spectraguard_core_infra.ingestion.models import SourceConfig
from src.spectraguard_core_infra.ingestion.base import FrameSource
from src.spectraguard_core_infra.ingestion.scheduler import FrameScheduler


class MockFastSource(FrameSource):
    """A mock source that generates frames instantly for testing."""

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
        return True, f"frame_data_{self.frame_counter}", time.time_ns()


class TestFrameScheduler(unittest.TestCase):
    def setUp(self):
        # Target 100 FPS (10ms delay) for fast testing
        self.config = SourceConfig(
            source_id="MOCK_1",
            source_type=SourceType.SIMULATOR,
            uri="mock://stream",
            target_fps=100.0,
        )
        self.source = MockFastSource(self.config)

    def test_scheduler_lifecycle(self):
        scheduler = FrameScheduler(self.source, max_queue_size=5)
        self.assertEqual(self.source.state, SourceState.INITIALIZED)

        # Start should trigger connect()
        scheduler.start()
        time.sleep(0.05)  # Allow thread to spin up and read frames

        self.assertEqual(self.source.state, SourceState.STREAMING)
        self.assertTrue(scheduler._is_running)

        # Retrieve frame
        success, frame, ts = scheduler.get_next_frame(timeout=0.1)
        self.assertTrue(success)
        self.assertIn("frame_data", frame)

        scheduler.stop()
        self.assertFalse(scheduler._is_running)
        self.assertEqual(self.source.state, SourceState.STOPPED)

    def test_queue_drop_policy(self):
        # Very small queue to force drops quickly
        scheduler = FrameScheduler(self.source, max_queue_size=2)
        scheduler.start()

        # Sleep long enough for a 100 FPS source to overflow a size=2 queue
        time.sleep(0.2)

        # Force stop to freeze states
        scheduler.stop()

        # We should have processed many frames but dropped the older ones
        self.assertGreater(scheduler.frames_processed, 5)
        self.assertGreater(scheduler.frames_dropped, 0)

    def test_get_timeout(self):
        scheduler = FrameScheduler(self.source, max_queue_size=5)
        # Don't start it, queue remains empty

        start_time = time.time()
        success, frame, ts = scheduler.get_next_frame(timeout=0.1)
        duration = time.time() - start_time

        self.assertFalse(success)
        self.assertIsNone(frame)
        self.assertGreaterEqual(duration, 0.09)  # Ensure it actually blocked


if __name__ == "__main__":
    unittest.main()
