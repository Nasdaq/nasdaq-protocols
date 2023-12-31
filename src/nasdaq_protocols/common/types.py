import abc


__all__ = [
    'Serializable',
    'Stoppable',
    'StateError',
    'EndOfQueue'
]


class Serializable(abc.ABC):
    """Abstract Base class for serializable objects."""

    @abc.abstractmethod
    def to_bytes(self):
        """pack the object to binary format."""
        pass

    @classmethod
    @abc.abstractmethod
    def from_bytes(cls, bytes_: bytes):
        """unpack the object from binary format."""
        pass


class Stoppable(abc.ABC):
    @abc.abstractmethod
    async def stop(self):
        pass

    @abc.abstractmethod
    def is_stopped(self):
        pass

class StateError(RuntimeError):
    pass

class EndOfQueue(EOFError):
    pass