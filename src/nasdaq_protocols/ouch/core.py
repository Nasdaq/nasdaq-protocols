import attrs
from nasdaq_protocols.common import Serializable, Byte, CommonMessage, logable


__all__ = [
    'OuchMessageId',
    'Message'
]
DEFAULT_DIRECTION = 'outgoing'
PROTOCOL = 'OUCH'


@attrs.define(auto_attribs=True, hash=True)
class OuchMessageId(Serializable):
    indicator: int
    direction: str = DEFAULT_DIRECTION

    @classmethod
    def from_bytes(cls, bytes_: bytes) -> tuple[int, 'OuchMessageId']:
        return 1, OuchMessageId(Byte.from_bytes(bytes_)[1], DEFAULT_DIRECTION)

    def to_bytes(self) -> tuple[int, bytes]:
        return Byte.to_bytes(self.indicator)


@attrs.define
@logable
class Message(CommonMessage, msg_id_cls=OuchMessageId, protocol=PROTOCOL):

    IncomingMsgClasses = []
    OutgoingMsgsClasses = []

    def __init_subclass__(cls, indicator, direction, **kwargs):  # pylint: disable=unexpected-special-method-signature
        msg_id = OuchMessageId(indicator, direction)
        if direction == 'incoming':
            Message.IncomingMsgClasses.append(cls)
        elif direction == 'outgoing':
            Message.OutgoingMsgsClasses.append(cls)
        cls.log.debug(f'{cls.__name__} subclassed from ouch.core.message')
        super().__init_subclass__(msg_id_cls=OuchMessageId, protocol=PROTOCOL, msg_id=msg_id)
