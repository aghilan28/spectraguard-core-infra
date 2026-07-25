"""Validation suite for RTSP network ingestion implementation."""

import cv2
import numpy as np
import unittest
from unittest.mock import patch, MagicMock
from src.spectraguard_core_infra.ingestion.enums import (
    SourceType,
    SourceState,
    IngestionErrorCode,
)
from src.spectraguard_core_infra.ingestion.exceptions import IngestionError
from src.spectraguard_core_infra.ingestion.models import SourceConfig
from src.spectraguard_core_infra.ingestion.readers.rtsp_reader import RTSPReader


class TestRTSPReader(unittest.TestCase):
    def setUp(self):
        self.config = SourceConfig(
            source_id="RTSP_CAM_1",
            source_type=SourceType.RTSP,
            uri="rtsp://admin:secret@192.168.1.100:554/stream1",
            max_reconnect_attempts=2,
        )
        self.dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    @patch("cv2.VideoCapture")
    def test_successful_connection_and_read(self, mock_cv2_capture):
        # Setup mock behavior for a healthy stream
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.read.return_value = (True, self.dummy_frame)
        mock_cv2_capture.return_value = mock_cap_instance

        reader = RTSPReader(self.config)
        self.assertEqual(reader.state, SourceState.INITIALIZED)

        reader.connect()
        self.assertEqual(reader.state, SourceState.STREAMING)
        # Use dynamic constant instead of hardcoded integer (which varies by cv2 build)
        mock_cv2_capture.assert_called_with(self.config.uri, cv2.CAP_FFMPEG)

        success, frame, ts = reader.read_frame()
        self.assertTrue(success)
        self.assertEqual(frame.shape, (480, 640, 3))
        self.assertGreater(ts, 0)

        reader.disconnect()
        self.assertEqual(reader.state, SourceState.STOPPED)
        mock_cap_instance.release.assert_called_once()

    @patch("cv2.VideoCapture")
    def test_connection_failure(self, mock_cv2_capture):
        # Setup mock behavior for unreachable stream
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = False
        mock_cv2_capture.return_value = mock_cap_instance

        reader = RTSPReader(self.config)

        with self.assertRaises(IngestionError) as context:
            reader.connect()

        self.assertEqual(context.exception.code, IngestionErrorCode.SOURCE_UNREACHABLE)
        self.assertEqual(reader.state, SourceState.FAILED)

    @patch("cv2.VideoCapture")
    def test_reconnection_policy_success(self, mock_cv2_capture):
        mock_cap_instance = MagicMock()
        # Initial connect succeeds
        mock_cap_instance.isOpened.return_value = True

        # First read fails (simulating network drop), subsequent reads succeed
        mock_cap_instance.read.side_effect = [(False, None), (True, self.dummy_frame)]
        mock_cv2_capture.return_value = mock_cap_instance

        reader = RTSPReader(self.config)
        reader.connect()

        # Should detect failure, auto-reconnect, and return the frame
        success, frame, ts = reader.read_frame()
        self.assertTrue(success)
        self.assertEqual(reader.state, SourceState.STREAMING)
        self.assertEqual(mock_cap_instance.read.call_count, 2)

    @patch("cv2.VideoCapture")
    @patch("time.sleep", return_value=None)  # Bypass sleep for fast testing
    def test_reconnection_policy_exhaustion(self, mock_sleep, mock_cv2_capture):
        mock_cap_instance = MagicMock()
        # Initial connect succeeds
        mock_cap_instance.isOpened.side_effect = [True, False, False, False]
        mock_cap_instance.read.return_value = (False, None)
        mock_cv2_capture.return_value = mock_cap_instance

        reader = RTSPReader(self.config)
        reader.connect()

        success, frame, ts = reader.read_frame()
        self.assertFalse(success)
        self.assertEqual(reader.state, SourceState.FAILED)

        # Original connect + max_reconnect_attempts (2) = 3 total connection attempts
        self.assertEqual(mock_cap_instance.isOpened.call_count, 3)


if __name__ == "__main__":
    unittest.main()
