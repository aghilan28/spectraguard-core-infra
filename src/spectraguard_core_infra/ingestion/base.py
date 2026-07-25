"""Abstract contracts defining the Frame Source interface."""

from abc import ABC, abstractmethod
from typing import Tuple, Any, Optional
from .enums import SourceState
from .models import SourceConfig


class FrameSource(ABC):
    """
    Abstract Base Class enforcing the contract for all physical and virtual
    frame acquisition plugins (RTSP, USB, File).
    """

    def __init__(self, config: SourceConfig):
        """Initializes the source with strict configuration bounds."""
        if not config.is_valid:
            raise ValueError("Invalid SourceConfig provided to FrameSource.")
        self._config = config
        self._state = SourceState.INITIALIZED

    @property
    def config(self) -> SourceConfig:
        return self._config

    @property
    def state(self) -> SourceState:
        return self._state

    @abstractmethod
    def connect(self) -> None:
        """Establishes a connection to the underlying media stream."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Safely terminates the connection and frees hardware/network resources."""
        pass

    @abstractmethod
    def read_frame(self) -> Tuple[bool, Optional[Any], int]:
        """
        Acquires the next available frame from the stream.

        Returns:
            Tuple containing:
            - Success boolean flag
            - Optional frame payload (e.g., numpy array)
            - Timestamp in nanoseconds
        """
        pass
