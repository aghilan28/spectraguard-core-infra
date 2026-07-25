"""Validation suite for Shared Memory allocation constraints."""

import unittest
from src.spectraguard_core_infra.storage.shared_memory import SharedMemoryManager


class TestSharedMemoryManager(unittest.TestCase):
    def test_invalid_size_rejection(self):
        with self.assertRaises(ValueError):
            SharedMemoryManager(name="test_shm", size=0, create=True)

    def test_lifecycle_allocation_and_cleanup(self):
        # 1MB test allocation
        manager = SharedMemoryManager(
            name="sg_test_shm_1", size=1024 * 1024, create=True
        )
        manager.allocate()

        self.assertIsNotNone(manager.buffer)
        self.assertEqual(len(manager.buffer), 1024 * 1024)

        # Write/Read boundary test
        manager.buffer[0:4] = b"\xDE\xAD\xBE\xEF"
        self.assertEqual(bytes(manager.buffer[0:4]), b"\xDE\xAD\xBE\xEF")

        manager.cleanup()

        # Post-cleanup access must strictly raise
        with self.assertRaises(RuntimeError):
            _ = manager.buffer

    def test_attach_existing_memory(self):
        # Creator instantiation
        creator = SharedMemoryManager(name="sg_test_shm_2", size=1024, create=True)
        creator.allocate()
        creator.buffer[0:4] = b"\xAA\xBB\xCC\xDD"

        # Attacher instantiation
        attacher = SharedMemoryManager(name="sg_test_shm_2", size=1024, create=False)
        attacher.allocate()

        # Verify cross-process data visibility mapping
        self.assertEqual(bytes(attacher.buffer[0:4]), b"\xAA\xBB\xCC\xDD")

        # Safe cascading cleanup
        attacher.cleanup()
        creator.cleanup()


if __name__ == "__main__":
    unittest.main()
