"""Immutable configuration models for frame sources."""

from dataclasses import dataclass
from .enums import SourceType


@dataclass(frozen=True)
class SourceConfig:
    """Strict configuration constraints for initiating a frame source connection."""

    source_id: str
    source_type: SourceType
    uri: str
    target_fps: float = 30.0
    timeout_seconds: float = 5.0
    max_reconnect_attempts: int = 3

    @property
    def is_valid(self) -> bool:
        """Validates that critical connection parameters meet operational boundaries."""
        if not self.source_id or not self.uri:
            return False
        if self.target_fps <= 0.0 or self.timeout_seconds <= 0.0:
            return False
        if self.max_reconnect_attempts < 0:
            return False
        return True
