"""Strict data structures for frame identification and telemetry."""

from dataclasses import dataclass
from typing import Tuple
from .enums import FrameStatus


@dataclass(frozen=True)
class FrameIdentifier:
    """Immutable deterministic identifier for a single hardware frame."""

    camera_id: str
    stream_id: str
    sequence_number: int
    timestamp_ns: int


@dataclass
class FrameMetadata:
    """Transport schema detailing the payload within a memory slot."""

    identifier: FrameIdentifier
    resolution: Tuple[int, int]
    channels: int
    pixel_format: str
    size_bytes: int
    status: FrameStatus
    checksum: str
    producer_id: str
