from typing import Callable, Type, Awaitable, ClassVar

import attrs
from nasdaq_protocols import soup
from nasdaq_protocols.soup import soup_app

from .core import Asn1Message


__all__ = [
    'OnAsn1MessageCoro',
    'OnAsn1CloseCoro',
    'Asn1SoupSessionId',
    'Asn1SoupClientSession'
]
OnAsn1MessageCoro = Callable[[Type[Asn1Message]], Awaitable[None]]
OnAsn1CloseCoro = Callable[[], Awaitable[None]]


@attrs.define(auto_attribs=True)
class Asn1SoupSessionId(soup_app.SoupAppSessionId):
    soup_session_id: soup.SoupSessionId = None
    protocol_name: str = 'asn1'


@attrs.define(auto_attribs=True)
class Asn1SoupClientSession(soup_app.SoupAppClientSession):
    """ Soup client session that can read messages from soup server.

    Currently, only one pdu is supported.
    """
    Asn1Message: ClassVar[Asn1Message]

    def __init_subclass__(cls, **kwargs):
        if 'asn1_message' not in kwargs:
            raise AttributeError("Missing 'asn1_message' attribute")
        cls.Asn1Message = kwargs.pop('asn1_message')
        super().__init_subclass__(**kwargs)

    def _create_session_id(self):
        return Asn1SoupSessionId(self.soup_session.session_id)

    @classmethod
    def decode(cls, bytes_: bytes):  # pylint: disable=arguments-differ
        """
        Decode the given bytes into an asn1 message.
        """
        return cls.Asn1Message.from_bytes(bytes_)

