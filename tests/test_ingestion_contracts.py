"""Validation suite for Ingestion Contracts and Source Abstractions."""

import unittest
from src.spectraguard_core_infra.ingestion.enums import (
    SourceState,
    SourceType,
    IngestionErrorCode,
)
from src.spectraguard_core_infra.ingestion.exceptions import IngestionError
from src.spectraguard_core_infra.ingestion.models import SourceConfig
from src.spectraguard_core_infra.ingestion.base import FrameSource


class DummySource(FrameSource):
    """Concrete implementation for testing abstract class enforcement."""

    def connect(self):
        self._state = SourceState.CONNECTING

    def disconnect(self):
        self._state = SourceState.STOPPED

    def read_frame(self):
        return True, b"frame_data", 123456789


class TestIngestionContracts(unittest.TestCase):
    def test_source_config_validation(self):
        # Valid Config
        valid_cfg = SourceConfig(
            source_id="CAM_01",
            source_type=SourceType.RTSP,
            uri="rtsp://localhost:8554/stream",
        )
        self.assertTrue(valid_cfg.is_valid)
        self.assertEqual(valid_cfg.target_fps, 30.0)

        # Invalid Config (Empty URI)
        invalid_cfg_uri = SourceConfig("CAM_02", SourceType.USB, "")
        self.assertFalse(invalid_cfg_uri.is_valid)

        # Invalid Config (Negative FPS)
        invalid_cfg_fps = SourceConfig(
            "CAM_03", SourceType.FILE, "file.mp4", target_fps=-10.0
        )
        self.assertFalse(invalid_cfg_fps.is_valid)

    def test_abstract_class_enforcement(self):
        # Prevent direct instantiation
        with self.assertRaises(TypeError):
            FrameSource(SourceConfig("CAM_01", SourceType.RTSP, "uri"))

    def test_concrete_implementation(self):
        cfg = SourceConfig("CAM_01", SourceType.SIMULATOR, "dummy://stream")
        source = DummySource(cfg)

        self.assertEqual(source.state, SourceState.INITIALIZED)
        self.assertEqual(source.config.source_id, "CAM_01")

        source.connect()
        self.assertEqual(source.state, SourceState.CONNECTING)

        success, frame, ts = source.read_frame()
        self.assertTrue(success)
        self.assertEqual(frame, b"frame_data")
        self.assertEqual(ts, 123456789)

    def test_exception_mapping(self):
        err = IngestionError("Stream not found", IngestionErrorCode.SOURCE_UNREACHABLE)
        self.assertEqual(err.code, IngestionErrorCode.SOURCE_UNREACHABLE)
        self.assertIn("ERR_INGEST_001", str(err))


if __name__ == "__main__":
    unittest.main()
