"""Consumer bounds and block-waiting execution."""

from .sync import TransportSync


class FrameConsumer:
    """Consumer interface establishing read ownership of populated slots."""

    def __init__(self, sync_context: TransportSync):
        self.sync_context = sync_context

    def acquire_read_slot(self, timeout: float = None) -> int:
        """
        Blocks until a slot is available, then claims exclusive read ownership.

        Args:
            timeout: Maximum seconds to block waiting for a frame.

        Returns:
            The index of the acquired slot, or -1 if the wait timed out.
        """
        with self.sync_context.not_empty:
            # If no unread frames exist, relinquish lock and sleep until signaled
            if self.sync_context.tracker.size == 0:
                if not self.sync_context.not_empty.wait(timeout):
                    return -1  # ERR_SYNC_TIMEOUT representation for tracking logic

            return self.sync_context.tracker.acquire_next_read_slot()
