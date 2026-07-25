"""Domain-specific exception mapping for Ingestion processes."""

from .enums import IngestionErrorCode


class IngestionError(Exception):
    """Base exception for all ingestion pipeline failures."""

    def __init__(self, message: str, code: IngestionErrorCode):
        super().__init__(f"[{code.value}] {message}")
        self.code = code
        self.message = message
