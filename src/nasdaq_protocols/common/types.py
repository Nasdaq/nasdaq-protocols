import abc
from typing import Generic, TypeVar, Type, Callable, Any


__all__ = [
    'Serializable',
    'Stoppable',
    'StateError',
    'EndOfQueue',
    'TypeDefinition'
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


class TypeDefinition:
    """
    Class to hold all type definitions

    :param to_str: Function to convert value to string
    :type to_str: Callable[[Any], str]
    :return: str

    :param from_str: Function to convert string to value
    :type from_str: Callable[[str], Any]
    :return: Any

    :param to_bytes: Function to convert value to bytes
    :type to_bytes: Callable[[Any], bytes]
    :return: Tuple[int, bytes]

    :param from_bytes: Function to convert bytes to value
    :type from_bytes: Callable[[bytes], Tuple[int, Any]]
    :return: Tuple[int, Any]
    """
    to_str: Callable[[Any], str]
    from_str: Callable[[str], Any]
    to_bytes: Callable[[Any], tuple[int, bytes]]
    from_bytes: Callable[[bytes], tuple[int, Any]]
    hint: 'str'
    type_cls: Type
    default_value: Any

    Definitions = {}

    @staticmethod
    def add_type(type_id):
        def _wrapper(target):
            TypeDefinition.Definitions[type_id] = target
            return target
        return _wrapper
