"""Live RTSP network stream ingestion source."""

import cv2
import time
from typing import Tuple, Any, Optional
from ..base import FrameSource
from ..models import SourceConfig
from ..enums import SourceState, IngestionErrorCode
from ..exceptions import IngestionError


class RTSPReader(FrameSource):
    """Concrete FrameSource for ingesting live RTSP/network video streams."""

    def __init__(self, config: SourceConfig):
        super().__init__(config)
        self._capture: Optional[cv2.VideoCapture] = None
        self._reconnect_attempts = 0

    def connect(self) -> None:
        """Establishes a connection to the RTSP stream using FFMPEG backend."""
        self._state = SourceState.CONNECTING

        # Enforce FFMPEG backend for consistent RTSP handling across platforms
        self._capture = cv2.VideoCapture(self._config.uri, cv2.CAP_FFMPEG)

        if not self._capture.isOpened():
            self._state = SourceState.FAILED
            raise IngestionError(
                f"Failed to connect to RTSP stream: {self._config.uri}",
                IngestionErrorCode.SOURCE_UNREACHABLE,
            )

        self._state = SourceState.STREAMING
        self._reconnect_attempts = 0

    def disconnect(self) -> None:
        """Safely terminates the RTSP socket connection."""
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        self._state = SourceState.STOPPED

    def _attempt_reconnect(self) -> bool:
        """Executes the reconnection policy upon stream failure."""
        self._state = SourceState.RECONNECTING
        self.disconnect()

        while self._reconnect_attempts < self._config.max_reconnect_attempts:
            self._reconnect_attempts += 1
            try:
                self.connect()
                return True
            except IngestionError:
                # Basic backoff before retry (simulated network delay)
                time.sleep(1.0)

        self._state = SourceState.FAILED
        return False

    def read_frame(self) -> Tuple[bool, Optional[Any], int]:
        """
        Acquires the latest frame from the live stream buffer.
        Utilizes true wall-clock nanoseconds for live temporal tagging.

        Returns:
            Tuple: (Success, Frame Array, Timestamp ns)
        """
        if (
            self._state not in (SourceState.STREAMING, SourceState.RECONNECTING)
            or self._capture is None
        ):
            return False, None, 0

        success, frame = self._capture.read()

        if not success:
            # Network drop detected, trigger reconnection policy
            if self._attempt_reconnect():
                success, frame = self._capture.read()
                if not success:
                    return False, None, 0
            else:
                return False, None, 0

        # For live streams, use exact wall-clock time
        return True, frame, time.time_ns()
