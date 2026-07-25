"""Cross-process synchronization and state lock management."""

import multiprocessing as mp
from ..storage.ring_buffer import RingBufferIndexTracker


class TransportSync:
    """Manages structural locking and conditional signaling for shared memory buffers."""

    def __init__(self, capacity: int):
        self.tracker = RingBufferIndexTracker(capacity)
        # We utilize standard OS-backed multiprocessing locks and conditions
        self.lock = mp.Lock()
        self.not_empty = mp.Condition(self.lock)
