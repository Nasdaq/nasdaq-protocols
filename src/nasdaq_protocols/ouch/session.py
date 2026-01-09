from typing import Callable, Awaitable, Type

import attrs
from nasdaq_protocols import soup
from nasdaq_protocols.soup import soup_app
from .core import Message

__all__ = [
    'OnOuchMessageCoro',
    'OnOuchCloseCoro',
    'OuchSessionId',
    'ClientSession'
]

OnOuchMessageCoro = Callable[[Type[Message]], Awaitable[None]]
OnOuchCloseCoro = Callable[[], Awaitable[None]]


@attrs.define(auto_attribs=True)
class OuchSessionId(soup_app.SoupAppSessionId):
    soup_session_id: soup.SoupSessionId = None
    protocol_name: str = "ouch"


@attrs.define(auto_attribs=True)
class ClientSession(soup_app.SoupAppClientSession):

    def _create_session_id(self):
        return OuchSessionId(self.soup_session.session_id)

    def decode(self, bytes_: bytes):
        """
        Decode the given bytes into an ouch message.
        """
        return Message.from_bytes(bytes_)
