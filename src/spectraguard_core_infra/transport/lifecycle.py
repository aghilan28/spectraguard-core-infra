"""End-to-end frame transport lifecycle manager."""

import logging
from typing import Tuple
from .sync import TransportSync
from .producer import FrameProducer
from .consumer import FrameConsumer
from ..storage.shared_memory import SharedMemoryManager
from ..contracts.models import FrameMetadata

logger = logging.getLogger(__name__)


class FrameLifecycleOrchestrator:
    """Orchestrates acquire, publish, consume, release, and recycle operations across shared memory."""

    def __init__(
        self,
        sync_context: TransportSync,
        shm_manager: SharedMemoryManager,
        slot_size_bytes: int,
    ):
        self.sync_context = sync_context
        self.shm_manager = shm_manager
        self.slot_size_bytes = slot_size_bytes
        self.producer = FrameProducer(sync_context)
        self.consumer = FrameConsumer(sync_context)

    def acquire_writable_slot(self) -> Tuple[int, memoryview]:
        """Reserves a write slot via the producer and slices the corresponding zero-copy memoryview."""
        slot_index = self.producer.acquire_write_slot()
        offset = slot_index * self.slot_size_bytes
        slot_view = self.shm_manager.buffer[offset : offset + self.slot_size_bytes]
        return slot_index, slot_view

    def publish_frame(self, slot_index: int, metadata: FrameMetadata) -> None:
        """Seals the frame slot as ready for consumers."""
        logger.debug(
            f"Published frame slot {slot_index} for camera {metadata.identifier.camera_id}"
        )

    def acquire_readable_slot(self, timeout: float = None) -> Tuple[int, memoryview]:
        """Waits for and acquires a readable slot index, returning its memory slice."""
        slot_index = self.consumer.acquire_read_slot(timeout=timeout)
        if slot_index == -1:
            return -1, memoryview(b"")

        offset = slot_index * self.slot_size_bytes
        slot_view = self.shm_manager.buffer[offset : offset + self.slot_size_bytes]
        return slot_index, slot_view

    def recycle_slot(self, slot_index: int) -> None:
        """Marks a consumed slot as released and ready for future acquisition."""
        logger.debug(f"Recycled slot {slot_index} back to empty state pool.")
