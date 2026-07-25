"""State enumerations for infrastructure components."""

from enum import IntEnum


class FrameStatus(IntEnum):
    """Lifecycle states of a frame slot within the transport layer."""

    EMPTY = 0  # Slot is unallocated/clean
    ACQUIRING = 1  # Producer is writing to the slot
    READY = 2  # Data is fully written and sealed
    CONSUMING = 3  # Consumer is actively reading the slot
    RELEASED = 4  # Consumer is done, pending recycle
    CORRUPT = 5  # Checksum failure or aborted write
