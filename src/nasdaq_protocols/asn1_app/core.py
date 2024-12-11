import importlib
import logging
from typing import ClassVar

import asn1tools
import attrs

from asn1tools import CompileError, DecodeError, ParseError
from nasdaq_protocols.common import Serializable, DuplicateMessageException

__all__ = [
    'Asn1Spec',
    'Asn1Message'
]
LOG = logging.getLogger(__name__)


class Asn1Spec:
    SpecMap = {}

    SpecName: str
    SpecPkgDir: str
    Spec: any

    def __init_subclass__(cls, **kwargs):
        try:
            cls.SpecName, cls.SpecPkgDir = kwargs['spec_name'], kwargs['spec_pkg_dir']
        except KeyError:
            raise AttributeError('Missing spec_name or spec_pkg_dir')

        if cls.SpecName in Asn1Spec.SpecMap:
            spec_name = cls.SpecName
            LOG.error(f'asn1 spec {spec_name} exists, existing spec = {Asn1Spec.SpecMap[spec_name]}')
            raise DuplicateMessageException(existing_msg=Asn1Spec.SpecMap[spec_name], new_msg=cls)

        try:
            cls.Spec = Asn1Spec._compile(cls.SpecPkgDir)
            Asn1Spec.SpecMap[cls.SpecName] = cls
        except (CompileError, ParseError) as error:
            LOG.error(f'Compile error - {cls.SpecName}, {error=}')
            raise error

    @classmethod
    def decode(cls, pdu_name: str, bytes_: bytes) -> tuple[int, dict[any, any]]:
        try:
            decoded, length = cls.Spec.decode_with_length(pdu_name, bytes_)
            return length, decoded
        except DecodeError as err:
            LOG.error(f'error while decoding asn1- {err=}')
            return 0, {}

    @staticmethod
    def _compile(spec_pkg_dir):
        files = list(
            filter(
                lambda x: x.suffix == '.asn1',
                importlib.resources.files(spec_pkg_dir).iterdir()
            )
        )
        return asn1tools.compiler.compile_files(files)


@attrs.define
class Asn1Message(Serializable):
    PduName: ClassVar[str]
    Spec: ClassVar[Asn1Spec]

    def __init_subclass__(cls, **kwargs):
        if all(_ in kwargs for _ in ['spec', 'pdu_name']):
            cls.PduName = kwargs['pdu_name']
            cls.Spec = kwargs['spec']
            LOG.info(f'subclassed Asn1Message, {cls.Spec=}, {cls.PduName=}')

    def to_bytes(self):
        raise NotImplementedError('Encoding asn1 message is not supported yet.')

    @classmethod
    def from_bytes(cls, bytes_: bytes):
        return cls.Spec.decode(cls.PduName, bytes_)
