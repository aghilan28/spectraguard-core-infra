"""Validation suite for concurrent Producer/Consumer signaling and ownership."""

import unittest
import threading
import time
from src.spectraguard_core_infra.transport.sync import TransportSync
from src.spectraguard_core_infra.transport.producer import FrameProducer
from src.spectraguard_core_infra.transport.consumer import FrameConsumer


class TestProducerConsumerSync(unittest.TestCase):
    def test_sequential_ownership_handshake(self):
        sync = TransportSync(capacity=3)
        producer = FrameProducer(sync)
        consumer = FrameConsumer(sync)

        # Verify producer sequential tracking
        self.assertEqual(producer.acquire_write_slot(), 0)
        self.assertEqual(producer.acquire_write_slot(), 1)

        # Verify consumer successfully claims the sequence
        self.assertEqual(consumer.acquire_read_slot(timeout=0.1), 0)
        self.assertEqual(consumer.acquire_read_slot(timeout=0.1), 1)

        # Verify consumer times out cleanly when starved
        self.assertEqual(consumer.acquire_read_slot(timeout=0.1), -1)

    def test_concurrent_blocking_and_signaling(self):
        sync = TransportSync(capacity=5)
        producer = FrameProducer(sync)
        consumer = FrameConsumer(sync)

        results = []

        def consume_task():
            for _ in range(5):
                results.append(consumer.acquire_read_slot(timeout=2.0))

        # Launch consumer thread (will immediately block on empty buffer)
        thread = threading.Thread(target=consume_task)
        thread.start()

        # Staggered producer injections to verify wake-up hooks
        for _ in range(5):
            time.sleep(0.01)
            producer.acquire_write_slot()

        thread.join(timeout=3.0)

        # Verify consumer woke up and collected in exact sequence
        self.assertEqual(results, [0, 1, 2, 3, 4])


if __name__ == "__main__":
    unittest.main()
