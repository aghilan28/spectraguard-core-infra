"""Validation testing architecture for Ring Buffer Core sequence logic."""

import unittest
from src.spectraguard_core_infra.storage.ring_buffer import RingBufferIndexTracker


class TestRingBufferCore(unittest.TestCase):
    def test_initial_bounds(self):
        tracker = RingBufferIndexTracker(capacity=4)
        self.assertEqual(tracker.capacity, 4)
        self.assertEqual(tracker.size, 0)

    def test_invalid_capacity_rejection(self):
        with self.assertRaises(ValueError):
            RingBufferIndexTracker(capacity=0)
        with self.assertRaises(ValueError):
            RingBufferIndexTracker(capacity=9999)

    def test_sequential_write_read_math(self):
        tracker = RingBufferIndexTracker(capacity=3)

        # Verify monotonically increasing tracking sequence coordinates
        self.assertEqual(tracker.acquire_next_write_slot(), 0)
        self.assertEqual(tracker.acquire_next_write_slot(), 1)
        self.assertEqual(tracker.size, 2)

        # Verify read convergence match
        self.assertEqual(tracker.acquire_next_read_slot(), 0)
        self.assertEqual(tracker.acquire_next_read_slot(), 1)
        self.assertEqual(tracker.size, 0)

    def test_empty_buffer_read_protection(self):
        tracker = RingBufferIndexTracker(capacity=3)
        self.assertEqual(tracker.acquire_next_read_slot(), -1)

    def test_wrap_around_and_overrun_contract(self):
        tracker = RingBufferIndexTracker(capacity=3)

        # Completely pack the circular slots
        self.assertEqual(tracker.acquire_next_write_slot(), 0)
        self.assertEqual(tracker.acquire_next_write_slot(), 1)
        self.assertEqual(tracker.acquire_next_write_slot(), 2)
        self.assertEqual(tracker.size, 3)

        # Force an explicit overrun execution -> index must wrap cleanly to 0
        # and push the read pointer forward to 1
        self.assertEqual(tracker.acquire_next_write_slot(), 0)
        self.assertEqual(tracker.size, 3)
        self.assertEqual(tracker.acquire_next_read_slot(), 1)


if __name__ == "__main__":
    unittest.main()
