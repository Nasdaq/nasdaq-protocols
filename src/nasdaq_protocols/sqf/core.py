import attrs
from nasdaq_protocols.soup_app import SoupAppMessage
from nasdaq_protocols.common import logable


__all__ = [
    'Message',
]
APP_NAME = 'SQF'


@attrs.define
@logable
class Message(SoupAppMessage, app_name=APP_NAME):

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(**kwargs)
