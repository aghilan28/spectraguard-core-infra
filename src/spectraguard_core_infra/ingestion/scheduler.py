"""Orchestrator for managing frame ingestion pacing and queueing."""

import time
import threading
import queue
from typing import Tuple, Any, Optional
from .base import FrameSource
from .enums import SourceState


class FrameScheduler:
    """
    Manages the active polling of a FrameSource, enforcing target FPS pacing
    and executing drop policies when the downstream queue backs up.
    """

    def __init__(self, source: FrameSource, max_queue_size: int = 30):
        self._source = source
        self._max_queue_size = max_queue_size
        self._queue = queue.Queue(maxsize=self._max_queue_size)
        self._is_running = False
        self._thread: Optional[threading.Thread] = None

        self.frames_processed = 0
        self.frames_dropped = 0

        # Calculate target delay in seconds
        self._target_delay_s = (
            1.0 / self._source.config.target_fps
            if self._source.config.target_fps > 0
            else 0
        )

    def start(self) -> None:
        """Initializes the source and starts the background ingestion thread."""
        if self._is_running:
            return

        if self._source.state == SourceState.INITIALIZED:
            self._source.connect()

        self._is_running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stops the ingestion loop and disconnects the source."""
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        self._source.disconnect()

        # Clear queue to free memory
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def get_next_frame(self, timeout: float = 0.5) -> Tuple[bool, Optional[Any], int]:
        """
        Retrieves the next frame from the scheduler's queue.

        Returns:
            Tuple: (Success, Frame Array, Timestamp ns)
        """
        try:
            frame_data, timestamp = self._queue.get(timeout=timeout)
            return True, frame_data, timestamp
        except queue.Empty:
            return False, None, 0

    def _capture_loop(self) -> None:
        """Background thread executing the paced capture loop."""
        while self._is_running:
            loop_start = time.perf_counter()

            # 1. Read from source
            success, frame, timestamp = self._source.read_frame()

            if success:
                self.frames_processed += 1

                # 2. Queue management (Drop Policy)
                if self._queue.full():
                    try:
                        # Drop oldest frame to maintain live edge
                        self._queue.get_nowait()
                        self.frames_dropped += 1
                    except queue.Empty:
                        pass

                # Push new frame
                try:
                    self._queue.put_nowait((frame, timestamp))
                except queue.Full:
                    pass  # Should be handled by drop policy above

            elif self._source.state in (SourceState.FAILED, SourceState.STOPPED):
                # Critical source failure or EOS, exit loop
                self._is_running = False
                break

            # 3. FPS Pacing
            elapsed = time.perf_counter() - loop_start
            sleep_time = self._target_delay_s - elapsed

            if sleep_time > 0:
                time.sleep(sleep_time)
