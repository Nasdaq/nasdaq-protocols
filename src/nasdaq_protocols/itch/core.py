import attrs
from nasdaq_protocols.common import Serializable, Byte, CommonMessage, logable


__all__ = [
    'ItchMessageId',
    'Message'
]
PROTOCOL = 'ITCH'


@attrs.define(auto_attribs=True, hash=True)
class ItchMessageId(Serializable):
    indicator: int

    @classmethod
    def from_bytes(cls, bytes_: bytes) -> tuple[int, 'ItchMessageId']:
        return 1, ItchMessageId(Byte.from_bytes(bytes_)[1])

    def to_bytes(self) -> tuple[int, bytes]:
        return Byte.to_bytes(self.indicator)


@attrs.define
@logable
class Message(CommonMessage, msg_id_cls=ItchMessageId, protocol=PROTOCOL):
    def __init_subclass__(cls, *args, **kwargs):
        if 'indicator' not in kwargs:
            raise ValueError('indicator is required when subclassing (itch) Message')
        cls.log.debug(f'{cls.__name__} subclassed from ouch.core.message')
        super().__init_subclass__(
            msg_id_cls=ItchMessageId,
            protocol=kwargs.get('protocol', PROTOCOL),
            msg_id=ItchMessageId(kwargs['indicator'])
        )
