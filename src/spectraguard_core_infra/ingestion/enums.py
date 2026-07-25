"""Enumerated types for ingestion source states, types, and errors."""

from enum import Enum


class SourceState(Enum):
    """Lifecycle states of a frame ingestion source."""

    INITIALIZED = "INITIALIZED"
    CONNECTING = "CONNECTING"
    STREAMING = "STREAMING"
    RECONNECTING = "RECONNECTING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


class SourceType(Enum):
    """Supported physical and virtual frame stream origins."""

    RTSP = "RTSP"
    USB = "USB"
    FILE = "FILE"
    SIMULATOR = "SIMULATOR"


class IngestionErrorCode(Enum):
    """Domain-specific error mappings for the ingestion subsystem."""

    SOURCE_UNREACHABLE = "ERR_INGEST_001"
    AUTHENTICATION_FAILED = "ERR_INGEST_002"
    FRAME_DECODE_ERROR = "ERR_INGEST_003"
    HARDWARE_FAULT = "ERR_INGEST_004"
    INVALID_CONFIGURATION = "ERR_INGEST_005"
