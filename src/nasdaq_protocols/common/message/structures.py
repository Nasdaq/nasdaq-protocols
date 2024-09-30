"""
This module contains the structures used to represent the messages in the protocol.
"""
import inspect
import json
from enum import Enum
from itertools import chain
from collections import OrderedDict, defaultdict
from typing import Any, Type, ClassVar, Callable
import attrs

from nasdaq_protocols.common.utils import logable
from nasdaq_protocols.common.types import Serializable
from nasdaq_protocols.common.types import TypeDefinition
from .types import Short, Boolean


__all__ = [
    'DuplicateMessageException',
    'Field',
    'Record',
    'RecordWithPresentBit',
    'Array',
    'CommonMessage'
]


@attrs.define(auto_exc=True)
class DuplicateMessageException(Exception):
    """
    Exception raised when a message is already defined in the app.

    :param existing_msg: Already registered message with the same id.
    :param new_msg: New message that is being registered.
    """
    existing_msg: Any
    new_msg: Any


@attrs.define(auto_attribs=True)
class Field:
    """
    Represents a field in a record or message.

    :param name: Name of the field.

    """
    name: str
    type: Type[TypeDefinition] | TypeDefinition
    default_value: Any = None


@attrs.define(eq=False, hash=False)
class _Record(TypeDefinition):
    Fields: ClassVar[list[Field]]
    IndexedFields: ClassVar[dict[str, Field]]
    default_value: ClassVar[Any] = None

    values = attrs.field(type=dict[str, Any], default=attrs.Factory(lambda self: self.init_values(), takes_self=True))

    def __init_subclass__(cls):
        try:
            cls.IndexedFields = OrderedDict((f.name, f) for f in cls.Fields)
            cls.type_cls = cls
            cls.hint = cls.__name__
            cls.log.debug('Subclassed %s', cls.__name__)
        except AttributeError:
            pass

    def init_values(self):
        # if any field is a record, flatten it.
        # Does not support nested records.
        return {_.name: _.type() for _ in self.Fields if inspect.isclass(_.type) and issubclass(_.type, _Record)}

    def __attrs_post_init__(self):
        for field in self.Fields:
            try:
                if issubclass(field.type, _Record) and field.name not in self.values:
                    self.values[field.name] = field.type()
            except TypeError:
                pass

    @staticmethod
    def is_record(type_):
        return inspect.isclass(type_) and issubclass(type_, _Record)

    @classmethod
    def to_str(cls, record: Type['_Record']):
        return str(record)

    def __str__(self):
        return f"{{'{self.__class__.__name__}':{{{self.values}}}}}"

    def as_collection(self):
        return self.values

    @classmethod
    def from_str(cls, _str):
        raise NotImplementedError('this method is not available')

    def __getattr__(self, item: str):
        try:
            return self.get_field_value(item)
        except KeyError:
            return self.__dict__[item]

    def __setattr__(self, key, value):
        try:
            field = self.IndexedFields[key]
            if isinstance(value, Enum):
                value = value.value
            if not isinstance(value, field.type.type_cls):
                raise ValueError(f'type mismatch, {self.__class__.__name__}:{field.name},'
                                 f' expected type {field.type.hint}, received {type(value)}')
            self.values[key] = value
        except KeyError:
            self.__dict__[key] = value

    def get_field_value(self, key: str) -> Any:
        field = self.IndexedFields[key]
        try:
            return self.values[key]
        except KeyError:
            return field.type.default_value if field.default_value is None else field.default_value

    @staticmethod
    def get_value(any_: Any) -> dict[str, Any] | list[dict[str, Any]] | Any:
        if isinstance(any_, _Record):
            return {any_.__class__.__name__: _Record.get_value(any_.values)}
        if isinstance(any_, list):
            return [_Record.get_value(_) for _ in any_]
        if isinstance(any_, dict):
            return {k: _Record.get_value(v) for k, v in any_.items()}
        return any_


@attrs.define
class Record(_Record):
    """
    Represents a record in the message.
    """
    @classmethod
    def from_bytes(cls, bytes_: bytes) -> tuple[int, Any]:
        offset = 0
        values = {}
        for field in cls.Fields:
            offset1, value = field.type.from_bytes(bytes_[offset:])
            offset += offset1
            values[field.name] = value
        return offset, cls(values)

    @classmethod
    def to_bytes(cls, record: 'Record') -> tuple[int, bytes]:
        segments = list(zip(*(f.type.to_bytes(record.get_field_value(f.name)) for f in cls.Fields)))
        return sum(segments[0]), b''.join(segments[1])


@attrs.define
class RecordWithPresentBit(Record):
    """
    Represents a record with a present bit in the message.
    """
    @classmethod
    def from_bytes(cls, bytes_: bytes) -> tuple[int, Any]:
        offset, present = Boolean.from_bytes(bytes_)
        if not present:
            return 1, None
        offset1, value = super(RecordWithPresentBit, cls).from_bytes(bytes_[offset:])
        return offset+offset1, value

    @classmethod
    def to_bytes(cls, record: 'Record') -> tuple[int, bytes]:
        if record is None or len(record.values) == 0:
            return Boolean.to_bytes(False)
        offset, bytes_ = Boolean.to_bytes(True)
        offset1, bytes1_ = super(RecordWithPresentBit, cls).to_bytes(record)
        return offset+offset1, bytes_+bytes1_


@attrs.define
class Array(TypeDefinition):
    default_value: ClassVar[list[Any]] = []
    type_cls: ClassVar = list
    hint: ClassVar[str] = 'list'

    type = attrs.field(type=TypeDefinition)
    length_type = attrs.field(default=Short)
    packer = attrs.field(init=False, type=Callable[[Type[TypeDefinition]], tuple[int, bytes]])
    unpacker = attrs.field(init=False, type=Callable[[bytes], tuple[int, Any]])

    def __attrs_post_init__(self):
        if issubclass(self.type, RecordWithPresentBit):
            record_cls = super(RecordWithPresentBit, self.type)
            self.packer, self.unpacker = record_cls.to_bytes, record_cls.from_bytes
        else:
            self.packer, self.unpacker = self.type.to_bytes, self.type.from_bytes

    @classmethod
    def to_str(cls, _any: Any):
        raise NotImplementedError('this method is not available for array types')

    @classmethod
    def from_str(cls, _str: str):
        raise NotImplementedError('this method is not available for array types')

    def to_bytes(self, list_: list[Any]) -> tuple[int, bytes]:
        items = (self.packer(_) for _ in list_)
        segments = list(zip(*chain([self.length_type.to_bytes(len(list_))], items)))
        return sum(segments[0]), b''.join(segments[1])

    def from_bytes(self, bytes_: bytes) -> tuple[int, Any]:
        offset, len_ = self.length_type.from_bytes(bytes_)
        data = []
        for _ in range(len_):
            offset1, value = self.unpacker(bytes_[offset:])
            offset += offset1
            data.append(value)
        return offset, data


@attrs.define
@logable
class CommonMessage(Serializable):
    MsgIdToClsMap: ClassVar[dict] = defaultdict(dict)
    MsgNameToMsgMap: ClassVar[dict] = defaultdict(dict)
    MsgId: ClassVar[Serializable] = None
    MsgIdClass: ClassVar[Serializable] = None
    BodyRecord: ClassVar[Type[Record]] = None
    AppName: ClassVar[str] = None

    record = attrs.field(default=None)

    def __init_subclass__(cls, **kwargs):
        cls.log.debug('CommonMessage: subclassing %s, params = %s', cls.__name__, str(kwargs))
        cls.MsgIdClass = kwargs.get('msg_id_cls', cls.MsgIdClass)
        cls.AppName = kwargs.get('app_name', cls.AppName)
        cls.MsgId = kwargs.get('msg_id', cls.MsgId)

        if all(_ in kwargs for _ in ['app_name', 'msg_id_cls', 'msg_id']):
            if (cls.MsgId in CommonMessage.MsgIdToClsMap[cls.AppName] and
                    cls.MsgIdToClsMap[cls.AppName][cls.MsgId] != cls):
                raise DuplicateMessageException(
                    existing_msg=CommonMessage.MsgIdToClsMap[cls.AppName][cls.MsgId],
                    new_msg=cls
                )
            CommonMessage.MsgIdToClsMap[cls.AppName][cls.MsgId] = cls
            CommonMessage.MsgNameToMsgMap[cls.AppName][cls.__name__] = cls

    def __attrs_post_init__(self):
        if self.record is None:
            self.record = self.BodyRecord()  # pylint: disable=E1102

    def to_bytes(self) -> tuple[int, bytes]:
        cls = self.__class__
        bytes_ = cls.MsgId.to_bytes()[1] + cls.BodyRecord.to_bytes(self.record)[1]
        return len(bytes_), bytes_

    @classmethod
    def from_bytes(cls, bytes_: bytes) -> tuple[int, 'CommonMessage']:
        len_, msg_id = cls.MsgIdClass.from_bytes(bytes_)
        try:
            msg_cls = CommonMessage.MsgIdToClsMap[cls.AppName][msg_id]
        except KeyError:
            cls.log.error('Unknown message id %s', msg_id)
            raise
        msg_len, data = msg_cls.BodyRecord.from_bytes(bytes_[len_:])
        return len_ + msg_len, msg_cls(data)

    def __getattr__(self, item):
        try:
            _ = self.BodyRecord.IndexedFields[item]
            return getattr(self.record, item)
        except KeyError:
            return self.__dict__[item]

    def __setattr__(self, key, value):
        try:
            _ = self.BodyRecord.IndexedFields[key]
            setattr(self.record, key, value)
        except KeyError:
            self.__dict__[key] = value

    def __str__(self):
        data = {
            'message': f'{self.__class__.__name__}[{self.MsgId}]',
            'body': self.record.as_collection()
        }
        return json.dumps(data, indent=2)

    @classmethod
    def get_msg_classes(cls) -> list[Type['CommonMessage']]:
        return CommonMessage.MsgIdToClsMap[cls.AppName].values()

    @classmethod
    def get_msg_cls_by_name(cls, name: str):
        return CommonMessage.MsgNameToMsgMap[cls.AppName][name]

    @classmethod
    def get_msg_cls_by_indicator(cls, indicator: Any):
        return CommonMessage.MsgIdToClsMap[cls.AppName][indicator]
