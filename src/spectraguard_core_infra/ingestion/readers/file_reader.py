"""Local video file ingestion source."""

import cv2
import time
from typing import Tuple, Any, Optional
from ..base import FrameSource
from ..models import SourceConfig
from ..enums import SourceState, IngestionErrorCode
from ..exceptions import IngestionError


class VideoFileReader(FrameSource):
    """Concrete FrameSource for ingesting local video files (.mp4, .avi, etc.)."""

    def __init__(self, config: SourceConfig):
        super().__init__(config)
        self._capture: Optional[cv2.VideoCapture] = None
        self._frame_count = 0

        # Calculate simulated nanosecond interval between frames based on target FPS
        self._ns_per_frame = (
            int(1e9 / self._config.target_fps) if self._config.target_fps > 0 else 0
        )
        self._simulated_base_time = 0

    def connect(self) -> None:
        """Opens the local video file for decoding."""
        self._state = SourceState.CONNECTING
        self._capture = cv2.VideoCapture(self._config.uri)

        if not self._capture.isOpened():
            self._state = SourceState.FAILED
            raise IngestionError(
                f"Failed to open video file at {self._config.uri}",
                IngestionErrorCode.SOURCE_UNREACHABLE,
            )

        self._state = SourceState.STREAMING
        self._frame_count = 0
        self._simulated_base_time = time.time_ns()

    def disconnect(self) -> None:
        """Releases the cv2 video capture resource."""
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        self._state = SourceState.STOPPED

    def read_frame(self) -> Tuple[bool, Optional[Any], int]:
        """
        Reads the next sequential frame from the video file.
        Simulates accurate timestamps based on the target framerate.

        Returns:
            Tuple: (Success, Frame Array, Timestamp ns)
        """
        if self._state != SourceState.STREAMING or self._capture is None:
            return False, None, 0

        success, frame = self._capture.read()

        if not success:
            # End of Stream (EOS) reached
            self._state = SourceState.STOPPED
            return False, None, 0

        # Generate monotonic timestamp simulation for offline files
        current_ts = self._simulated_base_time + (
            self._frame_count * self._ns_per_frame
        )
        self._frame_count += 1

        return True, frame, current_ts
