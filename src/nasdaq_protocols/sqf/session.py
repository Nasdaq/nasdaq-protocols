from typing import Callable, Awaitable, Type

import attrs
from nasdaq_protocols import soup
from nasdaq_protocols.soup import soup_app
from .core import Message

__all__ = [
    'OnSqfMessageCoro',
    'OnSqfCloseCoro',
    'SqfSessionId',
    'ClientSession'
]

OnSqfMessageCoro = Callable[[Type[Message]], Awaitable[None]]
OnSqfCloseCoro = Callable[[], Awaitable[None]]


@attrs.define(auto_attribs=True)
class SqfSessionId(soup_app.SoupAppSessionId):
    soup_session_id: soup.SoupSessionId = None
    protocol_name: str = "sqf"


@attrs.define(auto_attribs=True)
class ClientSession(soup_app.SoupAppClientSession):

    def _create_session_id(self):
        return SqfSessionId(self.soup_session.session_id)

    def decode(self, bytes_: bytes):
        """
        Decode the given bytes into a sqf message.
        """
        return Message.from_bytes(bytes_)
