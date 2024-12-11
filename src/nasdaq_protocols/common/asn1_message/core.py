import importlib.resources
from typing import Mapping, Any, Union, Tuple

import attr
import asn1tools
from nasdaq_protocols.common.utils import Printable
from nasdaq_protocols.common.utils import add_logger, kwargs_contains


@add_logger
class Asn1Spec:
    SpecMap = {}
    SpecProviderClass = {}

    @kwargs_contains(['spec_name'])
    def __init_subclass__(cls, **kwargs):
        Asn1Spec.SpecProviderClass[kwargs['spec_name']] = cls

    @staticmethod
    def spec(spec_name):
        if spec_name in Asn1Spec.SpecMap:
            return Asn1Spec.SpecMap[spec_name]

        if spec_name in Asn1Spec.SpecProviderClass:
            spec_dir = Asn1Spec.SpecProviderClass[spec_name].spec_dir()
            files = list(importlib.resources.files(spec_dir).iterdir())
            Asn1Spec.SpecMap[spec_name] = Asn1Spec.asn1_compile(files)

        try:
            return Asn1Spec.SpecMap[spec_name]
        except KeyError:
            Asn1Spec.Log(f'{spec_name} is not loaded')
            return None

    @staticmethod
    def asn1_compile(files):
        return asn1tools.compiler.compile_files(files)


@attr.s(auto_attribs=True)
class Asn1Type(Printable):
    TypeMap = {}
    Fields = []
    Hint = ''
    Type = ''

    _data: Union[Mapping[str, Any], Tuple[int, Any]]

    def __init_subclass__(cls, **kwargs):
        if 'type' in kwargs:
            Asn1Type.TypeMap[kwargs['type']] = cls
            cls.Type = kwargs['type']
        if 'hint' in kwargs:
            cls.Hint = kwargs['hint']
        Asn1Type.TypeMap[cls.__name__] = cls

    @classmethod
    def resolve_type(cls, type_name: str):
        return Asn1Type.TypeMap.get(type_name, None)

    @classmethod
    def hint(cls):
        return cls.Hint

    @classmethod
    def get_type(cls):
        return cls.Type

    def as_collection(self):
        return Asn1Type._json_compatible_collection(self._data)

    def __str__(self):
        return self.as_json_string(indent=4)

    @staticmethod
    def _json_compatible_collection(data):
        if isinstance(data, tuple):
            if isinstance(data[0], (bytearray, bytes)):
                return f'{data[0]}'
            return {data[0]: Asn1Type._json_compatible_collection(data[1])}
        if isinstance(data, bytes):
            return str(data)
        if isinstance(data, dict):
            return {k: Asn1Type._json_compatible_collection(v) for k, v in data.items()}
        if isinstance(data, list):
            return [Asn1Type._json_compatible_collection(_) for _ in data]
        return data


@attr.s(auto_attribs=True)
class Asn1Enum(Asn1Type, context='BASIC', type='ENUMERATED', hint='str'):
    pass


@attr.s(auto_attribs=True)
class Asn1Integer(Asn1Type, type='INTEGER', hint='int'):
    pass


@attr.s(auto_attribs=True)
class Asn1Real(Asn1Type, type='REAL', hint='float'):
    pass


@attr.s(auto_attribs=True)
class Asn1OctetString(Asn1Type, type='OCTET STRING', hint='bytes'):
    pass


@attr.s(auto_attribs=True)
class Asn1BitString(Asn1Type, type='BIT STRING', hint='bytes'):
    pass


@attr.s(auto_attribs=True)
class Asn1Boolean(Asn1Type, type='BOOLEAN', hint='bool'):
    pass


class Asn1Sequence(Asn1Type, type='SEQUENCE', hint='dict'):
    def get_attr(self, item):
        if item == '_data':
            return self.__dict__[item]

        item = item.strip('_')
        if item in self._data:
            return self.__class__.Fields[item](self._data[item])
        return None


class Asn1SequenceOf(Asn1Sequence, type='SEQUENCE OF', hint='dict'):
    pass


class Asn1Choice(Asn1Type, type='CHOICE', hint='tuple'):
    def get_attr(self, item):
        if item == '_data':
            return self.__dict__[item]

        item = item.strip('_')

        if item == self._data[0]:
            return self.__class__.Fields[item](self._data[1])
        return None

    def get_data(self):
        field_name = self._data[0]
        return self.__class__.Fields[field_name](self._data[1])


class Asn1Set(Asn1Sequence, type='SET', hint='dict'):
    pass


class Asn1SetOf(Asn1Sequence, type='SET OF', hint='dict'):
    pass
