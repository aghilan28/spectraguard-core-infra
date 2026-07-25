"""System constants, error codes, and transport protocol identifiers."""


class ErrorCode:
    """Standardized infrastructure error codes."""

    SUCCESS = 0
    ERR_SHM_ALLOC_FAILED = 100
    ERR_BUFFER_FULL = 101
    ERR_BUFFER_EMPTY = 102
    ERR_FRAME_DROPPED = 103
    ERR_CORRUPT_METADATA = 104
    ERR_SYNC_TIMEOUT = 105
    ERR_INVALID_STATE_TRANSITION = 106


class TransportProtocol:
    """Identifiers for underlying transport layers."""

    SHARED_MEMORY_POSIX = "shm_posix"
    SHARED_MEMORY_SYSV = "shm_sysv"
    MMAP_FILE = "mmap_file"


class SystemLimits:
    """Hard boundaries for infrastructure allocations."""

    # 4K resolution (3840x2160) * 3 channels (RGB) = 24,883,200 bytes, rounded up for padding
    MAX_FRAME_SIZE_BYTES = 33177600
    MAX_RING_BUFFER_SLOTS = 1024
    DEFAULT_SHM_PREFIX = "sg_frame_buf_"
