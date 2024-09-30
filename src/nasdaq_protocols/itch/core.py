import attrs
from nasdaq_protocols.common import Serializable, Byte, CommonMessage, logable


__all__ = [
    'ItchMessageId',
    'Message'
]
APP_NAME = 'ITCH'


@attrs.define(auto_attribs=True, hash=True)
class ItchMessageId(Serializable):
    indicator: int

    @classmethod
    def from_bytes(cls, bytes_: bytes) -> tuple[int, 'ItchMessageId']:
        return 1, ItchMessageId(Byte.from_bytes(bytes_)[1])

    def to_bytes(self) -> tuple[int, bytes]:
        return Byte.to_bytes(self.indicator)

    def __str__(self):
        return f'indicator={self.indicator}'


@attrs.define
@logable
class Message(CommonMessage, msg_id_cls=ItchMessageId, app_name=APP_NAME):
    def __init_subclass__(cls, *args, **kwargs):
        cls.log.debug('itch.core.Message subclassing %s, params = %s', cls.__name__, str(kwargs))

        if 'app_name' not in kwargs:
            kwargs['app_name'] = APP_NAME

        kwargs['msg_id_cls'] = ItchMessageId

        if 'indicator' in kwargs:
            kwargs['msg_id'] = ItchMessageId(kwargs['indicator'])

        super().__init_subclass__(**kwargs)
