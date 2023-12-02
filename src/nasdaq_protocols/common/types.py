import abc


__all__ = [
    'Serializable'
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