"""Shared Memory allocation and lifecycle management."""

import logging
from multiprocessing.shared_memory import SharedMemory
from typing import Optional

from ..contracts.constants import SystemLimits

logger = logging.getLogger(__name__)


class SharedMemoryManager:
    """Manages the allocation, mapping, and cleanup of shared memory blocks."""

    def __init__(self, name: str, size: int, create: bool = False):
        if (
            size <= 0
            or size
            > SystemLimits.MAX_FRAME_SIZE_BYTES * SystemLimits.MAX_RING_BUFFER_SLOTS
        ):
            raise ValueError(f"Invalid allocation size: {size}")

        self.name = name
        self.size = size
        self.is_creator = create
        self._shm: Optional[SharedMemory] = None

    def allocate(self) -> None:
        """Allocates or attaches to the shared memory block."""
        try:
            self._shm = SharedMemory(
                name=self.name, create=self.is_creator, size=self.size
            )
            logger.debug(
                f"Successfully mapped shared memory: {self.name} (size: {self.size})"
            )
        except FileExistsError:
            raise RuntimeError(f"Shared memory block '{self.name}' already exists.")
        except FileNotFoundError:
            raise RuntimeError(
                f"Shared memory block '{self.name}' not found for attachment."
            )

    @property
    def buffer(self) -> memoryview:
        """Exposes the underlying memoryview for zero-copy read/write operations."""
        if self._shm is None:
            raise RuntimeError("Shared memory is not allocated.")
        return self._shm.buf

    def cleanup(self) -> None:
        """Safely detaches and optionally unlinks the shared memory block."""
        if self._shm is not None:
            self._shm.close()
            if self.is_creator:
                try:
                    self._shm.unlink()
                except FileNotFoundError:
                    pass  # Already unlinked safely
            self._shm = None
