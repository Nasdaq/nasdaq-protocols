import attrs
from nasdaq_protocols.soup import soup_app
from nasdaq_protocols.common import logable


__all__ = [
    'Message'
]
APP_NAME = 'ITCH'


@attrs.define
@logable
class Message(soup_app.SoupAppMessage, app_name=APP_NAME):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
