import importlib.resources
import logging

import attr
import asn1tools
from asn1tools import CompileError

from nasdaq_protocols.common import DuplicateMessageException


__all__ = [
    'Asn1Spec',
    'Asn1Type',
    'Asn1Enum',
    'Asn1Integer',
    'Asn1Real',
    'Asn1OctetString',
    'Asn1BitString',
    'Asn1Boolean',
    'Asn1Sequence',
    'Asn1SequenceOf',
    'Asn1Choice',
    'Asn1Set',
    'Asn1SetOf',
    'Asn1NumericString',
    'Asn1VisibleString',
    'Ans1GraphicString',
    'Ans1PrintableString'
]
LOG = logging.getLogger(__name__)


class Asn1Spec:
    SpecMap = {}

    SpecName: str
    SpecPkgDir: str
    Spec: any

    def __init_subclass__(cls, **kwargs):
        final_class = False
        try:
            cls.SpecName, cls.SpecPkgDir = kwargs['spec_name'], kwargs['spec_pkg_dir']
            final_class = True
        except KeyError:
            ...

        if final_class:
            if cls.SpecName in Asn1Spec.SpecMap:
                spec_name = cls.SpecName
                LOG.error(f'asn1 spec {spec_name} exists, existing spec = {Asn1Spec.SpecMap[spec_name]}')
                raise DuplicateMessageException(
                    existing_msg=Asn1Spec.SpecMap[spec_name],
                    new_msg=cls
                )

            try:
                cls.Spec = Asn1Spec._compile(cls.SpecPkgDir)
                Asn1Spec.SpecMap[cls.SpecName] = cls
            except CompileError as compile_error:
                LOG.error(f'Compile error - {cls.SpecName}, {compile_error=}')
                raise compile_error
            except Exception as e:
                LOG.error(f'Error - {cls.SpecName}, {e=}')
                raise e

    @classmethod
    def decode(cls, pdu_name: str, bytes_: bytes) -> tuple[int, 'Asn1Type']:
        try:
            decoded, length = cls.Spec.decode_with_length(pdu_name, bytes_)
            return length, Asn1Type.resolve_type(pdu_name)(decoded)
        except KeyError:
            LOG.error(f'pdu {pdu_name} does not exist')
            raise KeyError

    @staticmethod
    def _compile(spec_pkg_dir):
        files = list(
            filter(
                lambda x: x.suffix == '.asn1',
                importlib.resources.files(spec_pkg_dir).iterdir()
            )
        )
        return asn1tools.compiler.compile_files(files)


@attr.s(auto_attribs=True)
class Asn1Type:
    TypeMap = {}
    Fields = []
    Hint = ''
    Type = ''

    data: any

    def __init_subclass__(cls, **kwargs):
        if 'type' in kwargs:
            Asn1Type.TypeMap[kwargs['type']] = cls
            cls.Type = kwargs['type']
        if 'hint' in kwargs:
            cls.Hint = kwargs['hint']
        Asn1Type.TypeMap[cls.__name__] = cls

    def __getattr__(self, item):
        try:
            return self.__dict__[item]
        except KeyError:
            if self.Type is 'CHOICE' and item == self.data[0]:
                # choice is represented as a tuple
                return self.Fields[item](self.data[1])
            if self.Type is 'SEQUENCE' and item in self.data:
                # sequence is represented as a dict
                return self.Fields[item](self.data[item])
            return None

    @classmethod
    def resolve_type(cls, type_name: str):
        return cls.TypeMap[type_name]

    def as_collection(self):
        return Asn1Type._json_compatible_collection(self._data)

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
    def __contains__(self, item):
        return item in self.data

    def __getattr__(self, item):
        if item.strip('_') in self.data:
            return self.__class__.Fields[item](self.data[item])

        return self.__dict__[item]


class Asn1SequenceOf(Asn1Sequence, type='SEQUENCE OF', hint='list'):
    pass


class Asn1Choice(Asn1Type, type='CHOICE', hint='tuple'):
    def __contains__(self, item):
        return self.data[0] == item

    def __getattr__(self, item):
        if item.strip('_') == self.data[0]:
            return self.__class__.Fields[item](self.data[1])

        return self.__dict__[item]


class Asn1Set(Asn1Sequence, type='SET', hint='dict'):
    pass


class Asn1SetOf(Asn1Sequence, type='SET OF', hint='list'):
    pass


class Asn1NumericString(Asn1Type, type='NumericString', hint='str'):
    pass


class Ans1PrintableString(Asn1Type, type='PrintableString', hint='str'):
    pass


class Asn1VisibleString(Asn1Type, type='VisibleString', hint='str'):
    pass


class Ans1GraphicString(Asn1Type, type='GraphicString', hint='str'):
    pass