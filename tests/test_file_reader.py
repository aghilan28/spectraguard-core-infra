"""Validation suite for Video File ingestion implementation."""

import os
import cv2
import time
import numpy as np
import unittest
from src.spectraguard_core_infra.ingestion.enums import (
    SourceType,
    SourceState,
    IngestionErrorCode,
)
from src.spectraguard_core_infra.ingestion.exceptions import IngestionError
from src.spectraguard_core_infra.ingestion.models import SourceConfig
from src.spectraguard_core_infra.ingestion.readers.file_reader import VideoFileReader


class TestVideoFileReader(unittest.TestCase):
    def setUp(self):
        # Generate a short synthetic video file for testing
        self.test_video_path = "test_ingest_vid.mp4"
        self.fps = 30.0
        self.frame_count = 10
        self.res = (640, 480)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(self.test_video_path, fourcc, self.fps, self.res)

        for i in range(self.frame_count):
            # Create dummy frames
            frame = np.ones((480, 640, 3), dtype=np.uint8) * (i * 20 % 255)
            out.write(frame)
        out.release()

        self.config = SourceConfig(
            source_id="FILE_CAM_1",
            source_type=SourceType.FILE,
            uri=self.test_video_path,
            target_fps=self.fps,
        )

    def tearDown(self):
        # Cleanup synthetic file
        if os.path.exists(self.test_video_path):
            try:
                os.remove(self.test_video_path)
            except PermissionError:
                time.sleep(0.1)  # Windows file handle delay
                if os.path.exists(self.test_video_path):
                    os.remove(self.test_video_path)

    def test_file_reader_lifecycle(self):
        reader = VideoFileReader(self.config)
        self.assertEqual(reader.state, SourceState.INITIALIZED)

        # Connect
        reader.connect()
        self.assertEqual(reader.state, SourceState.STREAMING)

        # Read frames
        success, frame, ts1 = reader.read_frame()
        self.assertTrue(success)
        self.assertEqual(frame.shape, (480, 640, 3))
        self.assertGreater(ts1, 0)

        success2, frame2, ts2 = reader.read_frame()
        self.assertTrue(success2)

        # Verify timestamp pacing simulation
        expected_diff = int(1e9 / self.fps)
        self.assertEqual(ts2 - ts1, expected_diff)

        # Disconnect
        reader.disconnect()
        self.assertEqual(reader.state, SourceState.STOPPED)

        # Read after disconnect should fail safely
        success3, frame3, ts3 = reader.read_frame()
        self.assertFalse(success3)

    def test_end_of_stream_handling(self):
        reader = VideoFileReader(self.config)
        reader.connect()

        frames_read = 0
        while True:
            success, _, _ = reader.read_frame()
            if not success:
                break
            frames_read += 1

        self.assertEqual(frames_read, self.frame_count)
        self.assertEqual(reader.state, SourceState.STOPPED)
        reader.disconnect()

    def test_invalid_file_handling(self):
        bad_cfg = SourceConfig("BAD", SourceType.FILE, "non_existent_file.mp4")
        reader = VideoFileReader(bad_cfg)

        with self.assertRaises(IngestionError) as context:
            reader.connect()

        self.assertEqual(context.exception.code, IngestionErrorCode.SOURCE_UNREACHABLE)
        self.assertEqual(reader.state, SourceState.FAILED)


if __name__ == "__main__":
    unittest.main()
