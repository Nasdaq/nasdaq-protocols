import abc
from typing import Generic, TypeVar, Type


__all__ = [
    'Serializable',
    'Stoppable',
    'StateError',
    'EndOfQueue'
]
T = TypeVar('T')


class Serializable(abc.ABC, Generic[T]):
    """Abstract Base class for serializable objects."""

    @abc.abstractmethod
    def to_bytes(self) -> tuple[int, bytes]:
        """pack the object to binary format."""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def from_bytes(cls, bytes_: bytes) -> tuple[int, Type[T]]:
        """unpack the object from binary format."""
        raise NotImplementedError


class Stoppable(abc.ABC):
    @abc.abstractmethod
    async def stop(self):
        raise NotImplementedError

    @abc.abstractmethod
    def is_stopped(self):
        raise NotImplementedError


class StateError(RuntimeError):
    """Raised when an operation is attempted in an invalid state."""


class EndOfQueue(EOFError):
    """Raised when the end of the queue is reached."""
