"""Validation suite for shared infrastructure contracts."""

import unittest
from src.spectraguard_core_infra.contracts import (
    ErrorCode,
    TransportProtocol,
    FrameStatus,
    FrameIdentifier,
    FrameMetadata,
)


class TestSharedContracts(unittest.TestCase):
    def test_error_codes(self):
        self.assertEqual(ErrorCode.SUCCESS, 0)
        self.assertEqual(ErrorCode.ERR_BUFFER_FULL, 101)

    def test_transport_protocols(self):
        self.assertEqual(TransportProtocol.SHARED_MEMORY_POSIX, "shm_posix")

    def test_frame_status_enum(self):
        self.assertEqual(FrameStatus.EMPTY.value, 0)
        self.assertEqual(FrameStatus.READY.value, 2)

    def test_frame_identifier_immutability(self):
        ident = FrameIdentifier(
            camera_id="CAM_01",
            stream_id="STR_A",
            sequence_number=1001,
            timestamp_ns=1627890123456789,
        )
        self.assertEqual(ident.sequence_number, 1001)

        # Frozen dataclass should raise exception on mutation attempt
        with self.assertRaises(Exception):
            ident.sequence_number = 1002

    def test_frame_metadata_schema(self):
        ident = FrameIdentifier("CAM_01", "STR_A", 1, 0)
        meta = FrameMetadata(
            identifier=ident,
            resolution=(1920, 1080),
            channels=3,
            pixel_format="RGB888",
            size_bytes=6220800,
            status=FrameStatus.ACQUIRING,
            checksum="dummy_hash",
            producer_id="PROD_001",
        )
        self.assertEqual(meta.status, FrameStatus.ACQUIRING)
        self.assertEqual(meta.size_bytes, 6220800)


if __name__ == "__main__":
    unittest.main()
