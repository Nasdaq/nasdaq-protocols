from typing import Callable, Awaitable, Type

import attrs
from nasdaq_protocols import soup
from nasdaq_protocols.soup_app.session import BaseClientSession, SessionId
from .core import Message

__all__ = [
    'OnItchMessageCoro',
    'OnItchCloseCoro',
    'ItchSessionId',
    'ClientSession'
]

OnItchMessageCoro = Callable[[Type[Message]], Awaitable[None]]
OnItchCloseCoro = Callable[[], Awaitable[None]]


@attrs.define(auto_attribs=True)
class ItchSessionId(SessionId):
    soup_session_id: soup.SoupSessionId = None
    protocol_name: str = "itch"


@attrs.define(auto_attribs=True)
class ClientSession(BaseClientSession):
    """ITCH protocol client session implementation."""

    def _create_session_id(self):
        return ItchSessionId(self.soup_session.session_id)

    def send_message(self, msg: Message):
        raise NotImplementedError("ITCH protocol does not support sending messages")

    @classmethod
    def decode(cls, bytes_: bytes):  # pylint: disable=W0221
        """
        Decode the given bytes into an ITCH message.
        """
        return Message.from_bytes(bytes_)
