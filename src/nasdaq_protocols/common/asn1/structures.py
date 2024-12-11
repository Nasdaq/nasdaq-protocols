import logging
from typing import ClassVar

import attrs

from .types import Asn1Spec
from .. import Serializable


__all__ = ['Asn1Message']
LOG = logging.getLogger(__name__)


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