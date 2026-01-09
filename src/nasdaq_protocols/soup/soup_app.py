import asyncio
from typing import Callable, Type, Awaitable, Generic, TypeVar

import attrs

from nasdaq_protocols.common import (
    Serializable,
    Byte,
    CommonMessage,
    logable,
    DispatchableMessageQueue,
)
from nasdaq_protocols import soup


M = TypeVar('M')


__all__ = [
    'SoupAppMessageId',
    'SoupAppMessage',
    'SoupAppSessionId',
    'SoupAppClientSession',
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


class SoupAppSessionId:
    """Base class for protocol-specific session IDs."""
    soup_session_id: soup.SoupSessionId = None
    protocol_name: str = "generic"

    def __str__(self):
        if self.soup_session_id:
            return f'{self.protocol_name}-{self.soup_session_id}'
        return f'{self.protocol_name}-nosoup'


@attrs.define(auto_attribs=True)
@logable
class SoupAppClientSession(Generic[M]):
    """Base client session class with common functionality for all protocol implementations."""
    soup_session: soup.SoupClientSession
    on_msg_coro: Callable[[Type[M]], Awaitable[None]] = None
    on_close_coro: Callable[[], Awaitable[None]] = None
    closed: bool = False
    _session_id: SoupAppSessionId = None
    _close_event: asyncio.Event = None
    _message_queue: DispatchableMessageQueue = None

    def __attrs_post_init__(self):
        self._session_id = self._create_session_id()
        self._message_queue = DispatchableMessageQueue(self._session_id, self.on_msg_coro)
        self.soup_session.set_handlers(on_msg_coro=self._on_soup_message, on_close_coro=self._on_soup_close)
        self.soup_session.start_dispatching()

    def _create_session_id(self):
        """Create a protocol-specific session ID. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement _create_session_id")

    async def receive_message(self):
        """
        Asynchronously receive a message from the session.

        This method blocks until a message is received by the session.
        """
        return await self._message_queue.get()

    def send_message(self, msg: M):
        """
        Send a message to the server.
        Not implemented in all protocols (e.g., ITCH is read-only).
        """
        self.soup_session.send_unseq_data(msg.to_bytes()[1])

    async def close(self):
        """
        Asynchronously close the session.
        """
        if self._close_event or self.closed:
            self.log.debug('%s> closing in progress..', self._session_id)
            return
        self._close_event = asyncio.Event()
        self.soup_session.initiate_close()
        await self._close_event.wait()
        self.log.debug('%s> closed.', self._session_id)

    async def _on_soup_message(self, message: soup.SoupMessage):
        if isinstance(message, soup.SequencedData):
            self.log.debug('%s> incoming sequenced bytes_', self._session_id)
            decoded = self.decode(message.data)
            await self._message_queue.put(decoded[1])

    async def _on_soup_close(self):
        await self._message_queue.stop()
        if self.on_close_coro is not None:
            await self.on_close_coro()
        if self._close_event:
            self._close_event.set()
        self.closed = True

    def decode(self, bytes_: bytes):
        """
        Decode the given bytes into a protocol-specific message.
        Subclasses should implement their own decode logic if needed.
        """
        raise NotImplementedError("Subclasses must implement decode")
