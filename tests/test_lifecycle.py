"""Validation suite for end-to-end Frame Lifecycle operations."""

import unittest
from src.spectraguard_core_infra.transport.sync import TransportSync
from src.spectraguard_core_infra.transport.lifecycle import FrameLifecycleOrchestrator
from src.spectraguard_core_infra.storage.shared_memory import SharedMemoryManager
from src.spectraguard_core_infra.contracts.models import FrameIdentifier, FrameMetadata
from src.spectraguard_core_infra.contracts.enums import FrameStatus


class TestFrameLifecycle(unittest.TestCase):
    def test_end_to_end_lifecycle_flow(self):
        capacity = 2
        slot_size = 1024
        total_size = capacity * slot_size

        sync = TransportSync(capacity=capacity)
        shm_manager = SharedMemoryManager(
            name="sg_lifecycle_test_shm", size=total_size, create=True
        )
        shm_manager.allocate()

        try:
            orchestrator = FrameLifecycleOrchestrator(sync, shm_manager, slot_size)

            # 1. Acquire Writable Slot
            slot_idx, write_view = orchestrator.acquire_writable_slot()
            self.assertEqual(slot_idx, 0)

            test_payload = b"FRAME_PIXEL_STREAM_DATA_01"
            write_view[0 : len(test_payload)] = test_payload

            # Explicitly delete write view reference to release exported pointer
            del write_view

            # 2. Publish Frame
            ident = FrameIdentifier("CAM_01", "STREAM_A", 1, 123456789)
            meta = FrameMetadata(
                identifier=ident,
                resolution=(640, 480),
                channels=3,
                pixel_format="RGB888",
                size_bytes=len(test_payload),
                status=FrameStatus.READY,
                checksum="abc123hash",
                producer_id="PROD_1",
            )
            orchestrator.publish_frame(slot_idx, meta)

            # 3. Acquire Readable Slot
            read_slot_idx, read_view = orchestrator.acquire_readable_slot(timeout=1.0)
            self.assertEqual(read_slot_idx, 0)
            self.assertEqual(bytes(read_view[0 : len(test_payload)]), test_payload)

            # Explicitly delete read view reference
            del read_view

            # 4. Recycle Slot
            orchestrator.recycle_slot(read_slot_idx)

        finally:
            shm_manager.cleanup()


if __name__ == "__main__":
    unittest.main()
