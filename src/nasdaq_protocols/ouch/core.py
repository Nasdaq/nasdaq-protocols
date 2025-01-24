from abc import ABC

import attrs
from nasdaq_protocols.common import Serializable, Byte, CommonMessage, logable


__all__ = [
    'OuchMessageId',
    'Message'
]
APP_NAME = 'OUCH'


@attrs.define(auto_attribs=True, hash=True)
class OuchMessageId(Serializable, ABC):
    indicator: int
    direction: str = 'outgoing'

    def to_bytes(self) -> tuple[int, bytes]:
        return Byte.to_bytes(self.indicator)

    @classmethod
    def from_bytes(cls, bytes_: bytes) -> tuple[int, 'OuchMessageId']:
        return 1, OuchMessageId(Byte.from_bytes(bytes_)[1])

    def __str__(self):
        return f'indicator={self.indicator}, direction={self.direction}'


@attrs.define
@logable
class Message(CommonMessage, msg_id_cls=OuchMessageId, app_name=APP_NAME):

    IncomingMsgClasses = []
    OutgoingMsgsClasses = []

    def __init_subclass__(cls, *args, **kwargs):
        cls.log.debug('ouch.core.Message subclassing %s, params = %s', cls.__name__, str(kwargs))

        if 'app_name' not in kwargs:
            kwargs['app_name'] = APP_NAME

        kwargs['msg_id_cls'] = OuchMessageId

        if all(k in kwargs for k in ['direction', 'indicator']):
            kwargs['msg_id'] = OuchMessageId(kwargs['indicator'], kwargs['direction'])
            container = cls.IncomingMsgClasses if kwargs['direction'] == 'incoming' else cls.OutgoingMsgsClasses
            container.append(cls)
        super().__init_subclass__(**kwargs)
