import abc
import pprint
from collections import OrderedDict, defaultdict
from enum import Enum
from typing import ClassVar, Any, Type, TypeVar, Union

import attrs

from nasdaq_protocols.common.utils import logable
from nasdaq_protocols.common.types import Serializable, TypeDefinition


__all__ = [
    'SEPARATOR',
    'SOH',
    'FixSerializable',
    'MessageSegments',
    'Field',
    'DataSegment',
    'GroupContainer',
    'Group',
    'Message',
    'Entry'
]
SEPARATOR = b'='
SOH = b'\x01'
BEGIN_STRING_FIELD = 8
BODY_LEN_FIELD = 9
CHECKSUM_FIELD = 10
MSG_TYPE_FIELD = 35
HEART_BEAT_MSG = '0'
LOGIN_MSG = 'A'
LOGOUT_MSG = '5'


class FixSerializable(Serializable):
    @classmethod
    @abc.abstractmethod
    def from_value(cls, value: Any) -> Type['FixSerializable']:
        ...

    @abc.abstractmethod
    def as_collection(self):
        ...


class MessageSegments(Enum):
    HEADER = 'Header'
    BODY = 'Body'
    TRAILER = 'Trailer'


@logable
class Field(FixSerializable):
    Tag: ClassVar[int]
    Name: ClassVar[str]
    FieldType: ClassVar[TypeDefinition]
    Values: ClassVar[dict[str, Any]]

    Def = {}

    @classmethod
    def __init_subclass__(cls, **kwargs):
        cls.log.debug(f'{cls.__name__} subclassed from Field')
        cls.Tag = int(kwargs['Tag'])
        cls.Name = kwargs['Name']
        cls.FieldType = kwargs['Type']
        Field.Def[int(cls.Tag)] = cls
        Field.Def[cls.Name] = cls

    def __init__(self, value):
        self.value = value

    def to_bytes(self) -> tuple[int, bytes]:
        tag_key_value = f'{self.Tag}='.encode('ascii') + self.FieldType.to_bytes(self.value)[1]
        return len(tag_key_value), tag_key_value

    @classmethod
    def from_bytes(cls, bytes_: bytes) -> tuple[int, 'Field']:
        value_start = bytes_.find(SEPARATOR)
        value_end = bytes_.find(SOH)
        total_bytes_to_deserialize = value_end + 1

        if value_start == -1:
            raise ValueError(f'Invalid value format for field {cls.Tag}, got {bytes_}')
        if value_end == -1:
            value_end = len(bytes_)
            total_bytes_to_deserialize = value_end

        _len, value = cls.FieldType.from_bytes(bytes_[(value_start + 1):value_end])
        return total_bytes_to_deserialize, cls(value)

    def as_collection(self):
        return self.value

    @classmethod
    def default_value(cls):
        return cls.FieldType.default_value

    @staticmethod
    def get_tag(key: str) -> int:
        return Field.Def[key].Tag

    @staticmethod
    def key_to_tag(func):
        def inner(self, key, *args, **kwargs):
            if not isinstance(key, int):
                key = int(key) if key.isdecimal() else Field.get_tag(key)
            return func(self, key, *args, **kwargs)
        return inner

    @classmethod
    def from_value(cls, value: Any) -> 'Field':
        if isinstance(value, cls):
            return value
        if isinstance(value, cls.FieldType.type_cls):
            return cls(value)
        raise TypeError(
            f'Field {cls.Name} expects "{cls.FieldType.hint}" type, but "{type(value)}" given'
        )

    @staticmethod
    def from_tag_value(tag_or_name: int | str, value: Any) -> 'Field':
        return Field.Def[tag_or_name].from_value(value)

    def __index__(self):
        return self.value

    def __hash__(self):
        return hash(self.value)

    def __len__(self):
        return len(self.value)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.value == other.value
        if isinstance(self.value, other.__class__):
            return self.value == other
        return False

    def __repr__(self):
        return f'{self.Name}[{self.Tag}]: {self}'

    def __str__(self):
        if isinstance(self.value, str):
            return f"'{self.value}'"
        return f'{self.value}'


@attrs.define(eq=False)
@logable
class DataSegment(FixSerializable):
    IndexedEntries: ClassVar[dict[Any, Type[FixSerializable]]]
    Required: ClassVar[list[int]]
    Entries: ClassVar[Any]
    GroupNameToFieldNameMapping: ClassVar[dict[str, int]]
    TagNameMapping: ClassVar[dict[int | str, str]]

    values = attrs.field(type=dict[int, FixSerializable], default=attrs.Factory(OrderedDict))

    @classmethod
    def __init_subclass__(cls, **_kwargs):
        cls.log.debug('%s subclassed from DataSegment', cls.__name__)
        cls.IndexedEntries = OrderedDict()
        cls.Required = []
        cls.GroupNameToFieldNameMapping = {}
        cls.TagNameMapping = {}
        try:
            for entry in cls.Entries:
                if issubclass(entry.entry_def, Field) or issubclass(entry.entry_def, GroupContainer):
                    cls.log.debug(f'....indexed {entry.entry_def.Tag}')
                    cls.IndexedEntries[entry.entry_def.Tag] = entry.entry_def
                    cls.IndexedEntries[entry.entry_def.Name] = entry.entry_def
                    cls.TagNameMapping[entry.entry_def.Tag] = entry.entry_def.Name
                    cls.TagNameMapping[entry.entry_def.Name] = entry.entry_def.Tag
                    if issubclass(entry.entry_def, GroupContainer):
                        cls.GroupNameToFieldNameMapping[entry.entry_def.__name__] = entry.entry_def.Tag
                        cls.TagNameMapping[entry.entry_def.Tag] = entry.entry_def.__name__
                        cls.TagNameMapping[entry.entry_def.__name__] = entry.entry_def.Tag
                    if entry.required:
                        cls.Required.append(entry.entry_def.Tag)
        except AttributeError:
            # Intermediate subclasses will not have Entries
            pass

    def to_bytes(self) -> tuple[int, bytes]:
        bytes_ = SOH.join([_.to_bytes()[1] for _ in self.values.values()])
        return len(bytes_), bytes_

    def as_collection(self):
        return {k: v.as_collection() for k, v in self.values.items()}

    @classmethod
    def from_bytes(cls, bytes_: bytes) -> tuple[int, Union[type['DataSegment'], 'DataSegment']]:
        deserialized = OrderedDict()
        count_deserialized = 0
        while len(bytes_) != 0:
            tag_pos = bytes_.find(SEPARATOR)
            tag = int(bytes_[0:tag_pos].decode('ascii'))

            if tag in deserialized:
                # tags cannot repeat in a group/container
                break

            try:
                field_length, field = cls.IndexedEntries[tag].from_bytes(bytes_)
                deserialized[tag] = field
                bytes_ = bytes_[field_length:]
                count_deserialized += field_length
            except KeyError:
                # Tags not present in this DataSegment indicates end of this Container
                break
        return count_deserialized, cls(deserialized)

    @classmethod
    def from_value(cls, value: Union[dict, 'DataSegment']) -> Union[type['DataSegment'], 'DataSegment']:
        value = value.values if isinstance(value, cls) else value

        if isinstance(value, dict):
            data_container = cls()
            for key, value_ in value.items():
                data_container[key] = value_
            return data_container
        raise TypeError(f'Expected type {cls} or dict.')

    @Field.key_to_tag
    def __setitem__(self, key: str | int, value):
        self.values[key] = self.__class__.IndexedEntries[key].from_value(value)

    @Field.key_to_tag
    def __getitem__(self, key: str | int):
        if key not in self.IndexedEntries:
            return self.__dict__[key]

        try:
            return self.values[key]
        except KeyError:
            field = self.IndexedEntries[key]
            return field.default_value() if issubclass(field, Field) else None

    def __getattr__(self, key: str):
        key = self.GroupNameToFieldNameMapping[key] if key in self.GroupNameToFieldNameMapping else key

        if key not in self.IndexedEntries:
            # This is not a fix field.
            return self.__dict__[key]

        return self.__getitem__(key)

    def __setattr__(self, key: str, value):
        if key not in self.IndexedEntries:
            # # This is not a fix field.
            self.__dict__[key] = value
            return

        key = self.GroupNameToFieldNameMapping[key] if key in self.GroupNameToFieldNameMapping else key
        self.__setitem__(key, value)

    def __len__(self):
        return len(self.values)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.values == other.values

    @Field.key_to_tag
    def __contains__(self, item: int | str):
        return item in self.values

    @classmethod
    def contains(cls, tag_or_name):
        return tag_or_name in cls.IndexedEntries or tag_or_name in cls.GroupNameToFieldNameMapping

    def validate(self):
        missing_fields = [field for field in self.Required if field not in self.values]
        if missing_fields:
            raise ValueError(f'{[self.TagNameMapping[field] for field in missing_fields]} mandatory fields missing')


@attrs.define
class Group(DataSegment):
    def to_bytes(self) -> tuple[int, bytes]:
        # The order of the fields in the groups should be as per definition
        bytes_ = SOH.join(
            [self.values[_.entry_def.Tag].to_bytes()[1]
             for _ in self.Entries
             if _.entry_def.Tag in self.values]
        )
        return len(bytes_), bytes_


GroupItem = TypeVar('GroupItem', bound=Group)


@logable
class GroupContainer(FixSerializable):
    CountCls: ClassVar[type[Field]]
    GroupCls: ClassVar[type[Group]]
    Tag: ClassVar[int]
    Name: ClassVar[str]

    @classmethod
    def __init_subclass__(cls, **kwargs):
        cls.log.debug('%s subclassed from GroupContainer', cls.__name__)
        cls.CountCls = kwargs['CountCls']
        cls.GroupCls = kwargs['GroupCls']
        cls.Name = cls.CountCls.Name
        cls.Tag = cls.CountCls.Tag

    def __init__(self, values: list[Group] | None = None, count: int = 0):
        if values is None:
            values = [self.GroupCls() for _ in range(count)]

        if not all((isinstance(group, self.GroupCls) for group in values)):
            self.log.error("%s instance creation failed, group class not matching, expected group class = %s",
                           self.__class__.__name__, self.GroupCls)
            raise TypeError(f'Group class mismatch, expected {self.GroupCls}')

        self.groups = values

    def to_bytes(self) -> tuple[int, bytes]:
        count_field = self.CountCls.from_value(len(self.groups))
        bytes_ = SOH.join(
            (
                count_field.to_bytes()[1],
                *(_.to_bytes()[1] for _ in self.groups)
            )
        )
        return len(bytes_), bytes_

    @classmethod
    def from_bytes(cls, bytes_: bytes) -> tuple[int, Union[type['GroupContainer'], 'GroupContainer']]:
        # Deserialize count field
        end, count = cls.CountCls.from_bytes(bytes_)

        deserialized = []
        count_deserialized = end

        cls.log.debug('%s> unpacking groups, contains %s group(s)', cls.Name, count.value)
        bytes_ = bytes_[end:]
        while len(bytes_) != 0 and len(deserialized) < count.value:
            end, group = cls.GroupCls.from_bytes(bytes_)
            bytes_ = bytes_[end:]
            deserialized.append(group)
            count_deserialized += end

        if len(deserialized) != count.value:
            raise ValueError(f'Expected {count.value} groups, got {len(deserialized)}')

        return count_deserialized, cls(deserialized)

    @classmethod
    def from_value(cls, value: list[dict[Any, Any] | GroupItem]) -> 'GroupContainer':
        return cls([cls.GroupCls.from_value(_) for _ in value])

    def as_collection(self):
        return [group.as_collection() for group in self.groups]

    def validate(self):
        for group in self.groups:
            group.validate()

    def __len__(self):
        return len(self.groups)

    def __getitem__(self, idx) -> GroupItem:
        return self.groups[idx]

    def __setitem__(self, key, value):
        self.groups[key] = value

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.groups == other.groups
        return False


class Message(FixSerializable):
    MsgIdToClsMap: ClassVar[dict] = defaultdict(dict)
    MsgNameToMsgMap: ClassVar[dict] = defaultdict(dict)
    Type: ClassVar[int]
    Name: ClassVar[str]
    Category: ClassVar[str]
    SegmentCls: ClassVar[dict[MessageSegments, type[DataSegment]]]
    AppName: ClassVar[str]

    Def = {}
    MandatoryFields = [
        'Name',
        'Type',
        'Category',
        'HeaderCls',
        'TrailerCls',
        'BodyCls',
    ]

    @classmethod
    def __init_subclass__(cls, **kwargs):
        for field in cls.MandatoryFields:
            if field not in kwargs:
                return
        app_name = kwargs.get('app_name', 'fix')
        cls.AppName = app_name
        cls.Name = kwargs['Name']
        cls.Type = kwargs['Type']
        cls.Category = kwargs['Category']
        cls.SegmentCls = {
            MessageSegments.HEADER: kwargs['HeaderCls'],
            MessageSegments.BODY: kwargs['BodyCls'],
            MessageSegments.TRAILER: kwargs['TrailerCls']
        }
        Message.Def[cls.Name] = cls
        Message.Def[cls.Type] = cls

    def __init__(self, data: dict[MessageSegments, Any] = None):
        self.data = {}
        data = data or {}

        for segment in MessageSegments:
            value = data.get(segment, self.SegmentCls[segment]())
            if not isinstance(value, self.SegmentCls[segment]):
                value = self.SegmentCls[segment].from_value(value)
            self.data[segment] = value

    @classmethod
    def from_value(cls, value: dict[MessageSegments, DataSegment]) -> Union[type['Message'], 'Message']:
        return cls(value)

    def to_bytes(self) -> tuple[int, bytes]:
        all_bytes = [_.to_bytes()[1] for _ in self.data.values()]
        bytes_ = SOH.join([_ for _ in all_bytes if len(_) > 0])
        if not bytes_.endswith(SOH):
            bytes_ += SOH
        return len(bytes_), bytes_

    def is_heartbeat(self):
        return self.Type == HEART_BEAT_MSG

    def is_logout(self):
        return self.Type == LOGOUT_MSG

    def as_collection(self):
        return {segment.value: self.data[segment].as_collection() for segment in MessageSegments}

    def __str__(self):
        return pprint.pformat(self.as_collection(), sort_dicts=False, indent=2)

    def __repr__(self):
        return str(self)

    def __getattr__(self, name):
        if name in ['Header', 'Body', 'Trailer']:
            return self.data[MessageSegments(name)]
        if self.SegmentCls[MessageSegments.BODY].contains(name):
            return self.data[MessageSegments.BODY].__getattr__(name)
        return self.__dict__[name]

    def __setattr__(self, key, value):
        if key in ['Header', 'Body', 'Trailer']:
            self.data[MessageSegments(key)] = value
        elif self.SegmentCls[MessageSegments.BODY].contains(key):
            self.data[MessageSegments.BODY].__setattr__(key, value)
        else:
            self.__dict__[key] = value

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.data == other.data
        return False

    @classmethod
    def from_bytes(cls, bytes_: bytes) -> tuple[int, Union[type['Message'], 'Message']]:
        if cls == Message:
            # Find the right subclass and dispatch the call.
            # this same function will be called but int the context of the right
            # subclass.
            return Message.Def[Message.get_msg_type(bytes_)].from_bytes(bytes_)

        total_bytes_deserialized = 0
        data = {}
        for segment in MessageSegments:
            end, deserialized = cls.SegmentCls[segment].from_bytes(bytes_)
            total_bytes_deserialized += end
            data[segment] = deserialized
            bytes_ = bytes_[end:]

        return total_bytes_deserialized, cls(data)

    @staticmethod
    def get_msg_type(bytes_: bytes) -> str:
        start = bytes_.find(b'35=') + 2
        end = bytes_.find(SOH, start)
        return bytes_[start+1:end].decode('ascii')

    def validate(self, segments: list[MessageSegments] | None = None):
        if segments is None:
            segments = MessageSegments

        for segment in segments:
            self.data[segment].validate()


@attrs.define(auto_attribs=True)
class Entry:
    entry_def: Any
    required: bool
