"""Producer bounds and slot ownership assignment."""

from .sync import TransportSync


class FrameProducer:
    """Producer interface establishing write ownership of buffer slots."""

    def __init__(self, sync_context: TransportSync):
        self.sync_context = sync_context

    def acquire_write_slot(self) -> int:
        """
        Claims exclusive ownership of the next available slot index.
        Executes under a strict process lock and broadcasts availability to waiting consumers.
        If the buffer is full, it enforces the deterministic overwrite contract natively.
        """
        with self.sync_context.lock:
            slot_index = self.sync_context.tracker.acquire_next_write_slot()
            # Signal any sleeping consumers that a new frame has been locked into the timeline
            self.sync_context.not_empty.notify()
            return slot_index
