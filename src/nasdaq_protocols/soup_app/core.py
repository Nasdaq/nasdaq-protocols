import attrs
from nasdaq_protocols.common import Serializable, Byte, CommonMessage, logable


__all__ = [
    'SoupAppMessageId',
    'SoupAppMessage'
]


@attrs.define(auto_attribs=True, hash=True)
class SoupAppMessageId(Serializable):
    indicator: int
    direction: str = 'outgoing'

    @classmethod
    def from_bytes(cls, bytes_: bytes) -> tuple[int, 'SoupAppMessageId']:
        return 1, cls(Byte.from_bytes(bytes_)[1])

    def to_bytes(self) -> tuple[int, bytes]:
        return Byte.to_bytes(self.indicator)

    def __str__(self):
        return f'indicator={self.indicator}, direction={self.direction}'


@attrs.define
@logable
class SoupAppMessage(CommonMessage):
    IncomingMsgClasses = []
    OutgoingMsgsClasses = []

    def __init_subclass__(cls, *args, **kwargs):
        cls.log.debug('%s subclassing %s, params = %s', cls.__mro__[1].__name__, cls.__name__, str(kwargs))

        app_name = kwargs.get('app_name')
        kwargs['app_name'] = app_name
        kwargs['msg_id_cls'] = SoupAppMessageId

        if 'indicator' in kwargs and 'direction' in kwargs:
            kwargs['msg_id'] = SoupAppMessageId(kwargs['indicator'], kwargs['direction'])

        super().__init_subclass__(**kwargs)
