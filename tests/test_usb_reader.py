"""Validation suite for USB camera hardware ingestion implementation."""

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
from src.spectraguard_core_infra.ingestion.readers.usb_reader import USBReader


class TestUSBReader(unittest.TestCase):
    def setUp(self):
        self.config = SourceConfig(
            source_id="USB_CAM_0", source_type=SourceType.USB, uri="0", target_fps=30.0
        )
        self.dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    @patch("cv2.VideoCapture")
    def test_usb_connection_and_read(self, mock_cv2_capture):
        # Setup mock behavior for a healthy hardware stream
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.read.return_value = (True, self.dummy_frame)
        mock_cv2_capture.return_value = mock_cap_instance

        reader = USBReader(self.config)
        self.assertEqual(reader.state, SourceState.INITIALIZED)

        reader.connect()
        self.assertEqual(reader.state, SourceState.STREAMING)
        mock_cv2_capture.assert_called_with(0)

        success, frame, ts = reader.read_frame()
        self.assertTrue(success)
        self.assertEqual(frame.shape, (480, 640, 3))
        self.assertGreater(ts, 0)

        reader.disconnect()
        self.assertEqual(reader.state, SourceState.STOPPED)
        mock_cap_instance.release.assert_called_once()

    def test_invalid_device_index(self):
        # USB configuration requires an integer string representation
        bad_cfg = SourceConfig("BAD_USB", SourceType.USB, "not_an_int")
        reader = USBReader(bad_cfg)

        with self.assertRaises(IngestionError) as context:
            reader.connect()

        self.assertEqual(
            context.exception.code, IngestionErrorCode.INVALID_CONFIGURATION
        )
        self.assertEqual(reader.state, SourceState.FAILED)

    @patch("cv2.VideoCapture")
    def test_hardware_fault_handling(self, mock_cv2_capture):
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True

        # Simulate USB cable being pulled during streaming (read returns False)
        mock_cap_instance.read.return_value = (False, None)
        mock_cv2_capture.return_value = mock_cap_instance

        reader = USBReader(self.config)
        reader.connect()
        self.assertEqual(reader.state, SourceState.STREAMING)

        success, frame, ts = reader.read_frame()
        self.assertFalse(success)
        self.assertEqual(reader.state, SourceState.FAILED)


if __name__ == "__main__":
    unittest.main()
