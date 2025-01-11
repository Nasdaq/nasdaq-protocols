import attrs
from nasdaq_protocols.common import Serializable, Byte, CommonMessage, logable


__all__ = [
    'SqfMessageId',
    'Message'
]
APP_NAME = 'SQF'


@attrs.define(auto_attribs=True, hash=True)
class SqfMessageId(Serializable):
    indicator: int
    direction: str = attrs.field(default="", eq=False, hash=False)

    @classmethod
    def from_bytes(cls, bytes_: bytes) -> tuple[int, 'SqfMessageId']:
        return 1, SqfMessageId(Byte.from_bytes(bytes_)[1])

    def to_bytes(self) -> tuple[int, bytes]:
        return Byte.to_bytes(self.indicator)

    def __str__(self):
        return f'indicator={self.indicator}'


@attrs.define
@logable
class Message(CommonMessage, msg_id_cls=SqfMessageId, app_name=APP_NAME):

    IncomingMsgClasses = []
    OutgoingMsgsClasses = []

    def __init_subclass__(cls, *args, **kwargs):
        cls.log.debug('Sqf.core.Message subclassing %s, params = %s', cls.__name__, str(kwargs))

        if 'app_name' not in kwargs:
            kwargs['app_name'] = APP_NAME

        kwargs['msg_id_cls'] = SqfMessageId

        if all(k in kwargs for k in ['direction', 'indicator']):
            kwargs['msg_id'] = SqfMessageId(kwargs['indicator'], kwargs['direction'])
            if kwargs['direction'] == 'incoming':
                Message.IncomingMsgClasses.append(cls)
            elif kwargs['direction'] == 'outgoing':
                Message.OutgoingMsgsClasses.append(cls)
        super().__init_subclass__(**kwargs)
