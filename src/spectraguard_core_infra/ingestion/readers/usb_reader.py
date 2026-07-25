"""Physical USB/Webcam ingestion source."""

import cv2
import time
from typing import Tuple, Any, Optional
from ..base import FrameSource
from ..models import SourceConfig
from ..enums import SourceState, IngestionErrorCode
from ..exceptions import IngestionError


class USBReader(FrameSource):
    """Concrete FrameSource for ingesting live USB camera streams."""

    def __init__(self, config: SourceConfig):
        super().__init__(config)
        self._capture: Optional[cv2.VideoCapture] = None

    def connect(self) -> None:
        """Opens the USB camera hardware device."""
        self._state = SourceState.CONNECTING

        try:
            # URI for USB is typically an integer index like "0" or "1"
            device_index = int(self._config.uri)
        except ValueError:
            self._state = SourceState.FAILED
            raise IngestionError(
                f"Invalid USB device index: '{self._config.uri}'. Must be an integer string.",
                IngestionErrorCode.INVALID_CONFIGURATION,
            )

        # Uses default backend (cv2.CAP_ANY) to maximize cross-platform hardware support
        self._capture = cv2.VideoCapture(device_index)

        if not self._capture.isOpened():
            self._state = SourceState.FAILED
            raise IngestionError(
                f"Failed to open USB camera at hardware index {device_index}",
                IngestionErrorCode.SOURCE_UNREACHABLE,
            )

        self._state = SourceState.STREAMING

    def disconnect(self) -> None:
        """Releases the cv2 video capture hardware resource."""
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        self._state = SourceState.STOPPED

    def read_frame(self) -> Tuple[bool, Optional[Any], int]:
        """
        Reads the next live frame directly from the USB buffer.

        Returns:
            Tuple: (Success, Frame Array, Timestamp ns)
        """
        if self._state != SourceState.STREAMING or self._capture is None:
            return False, None, 0

        success, frame = self._capture.read()

        if not success:
            # Hardware drop (e.g., USB cable pulled)
            self._state = SourceState.FAILED
            return False, None, 0

        return True, frame, time.time_ns()
