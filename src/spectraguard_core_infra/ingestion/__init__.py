"""Live Frame Ingestion Pipeline abstractions and contracts."""

from .enums import SourceState, SourceType, IngestionErrorCode
from .exceptions import IngestionError
from .models import SourceConfig
from .base import FrameSource
from .readers.file_reader import VideoFileReader
from .readers.rtsp_reader import RTSPReader
from .readers.usb_reader import USBReader
from .scheduler import FrameScheduler
from .supervisor import IngestionSupervisor

__all__ = [
    "SourceState",
    "SourceType",
    "IngestionErrorCode",
    "IngestionError",
    "SourceConfig",
    "FrameSource",
    "VideoFileReader",
    "RTSPReader",
    "USBReader",
    "FrameScheduler",
    "IngestionSupervisor",
]
