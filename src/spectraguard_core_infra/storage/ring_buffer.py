"""Deterministic tracking engine for shared circular allocations."""

from ..contracts.constants import SystemLimits


class RingBufferIndexTracker:
    """Manages slot sequence math and ownership bounds for a ring buffer."""

    def __init__(self, capacity: int):
        if capacity <= 0 or capacity > SystemLimits.MAX_RING_BUFFER_SLOTS:
            raise ValueError(
                f"Capacity must be between 1 and {SystemLimits.MAX_RING_BUFFER_SLOTS}"
            )

        self.capacity = capacity
        self.write_index = 0
        self.read_index = 0
        self.size = 0

    def acquire_next_write_slot(self) -> int:
        """Calculates and reserves the next slot sequence index for writing.

        If the buffer is fully packed, it forces the oldest unread index forward,
        implementing a deterministic lossy overwrite contract.
        """
        target_slot = self.write_index
        self.write_index = (self.write_index + 1) % self.capacity

        if self.size == self.capacity:
            # Buffer overrun context: Advance read cursor to slide the window forward
            self.read_index = (self.read_index + 1) % self.capacity
        else:
            self.size += 1

        return target_slot

    def acquire_next_read_slot(self) -> int:
        """Fetches the current readable slot index sequence position.

        Returns -1 if there are no unconsumed indices currently registered.
        """
        if self.size == 0:
            return -1

        target_slot = self.read_index
        self.read_index = (self.read_index + 1) % self.capacity
        self.size -= 1
        return target_slot

    def reset(self) -> None:
        """Forces immediate structural index convergence."""
        self.write_index = 0
        self.read_index = 0
        self.size = 0
