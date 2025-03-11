import asyncio
from typing import Callable, Type, Awaitable

import attrs
from nasdaq_protocols.common import DispatchableMessageQueue, logable
from nasdaq_protocols import soup
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
class SqfSessionId:
    soup_session_id: soup.SoupSessionId = None

    def __str__(self):
        if self.soup_session_id:
            return f'sqf-{self.soup_session_id}'
        return 'sqf-nosoup'


@attrs.define(auto_attribs=True)
@logable
class ClientSession:
    soup_session: soup.SoupClientSession
    on_msg_coro: OnSqfMessageCoro = None
    on_close_coro: OnSqfCloseCoro = None
    closed: bool = False
    _session_id: SqfSessionId = None
    _close_event: asyncio.Event = None
    _message_queue: DispatchableMessageQueue = None

    def __attrs_post_init__(self):
        self._session_id = SqfSessionId(self.soup_session.session_id)
        self._message_queue = DispatchableMessageQueue(self._session_id, self.on_msg_coro)
        self.soup_session.set_handlers(on_msg_coro=self._on_soup_message, on_close_coro=self._on_soup_close)
        self.soup_session.start_dispatching()

    async def receive_message(self):
        """
        Asynchronously receive a message from the Sqf session.

        This method blocks until a message is received by the session.
        """
        return await self._message_queue.get()

    def send_message(self, msg: Message):
        """
        Send a message to the Sqf Server.
        """
        self.soup_session.send_unseq_data(msg.to_bytes()[1])

    async def close(self):
        """
        Asynchronously close the Sqf session.
        """
        if self._close_event:
            self.log.debug('%s> closing in progress..', self._session_id)
            return
        self._close_event = asyncio.Event()
        self.soup_session.initiate_close()
        await self._close_event.wait()
        self.log.debug('%s> closed.', self._session_id)

    async def _on_soup_message(self, message: soup.SoupMessage):
        if isinstance(message, soup.SequencedData):
            self.log.debug('%s> incoming sequenced bytes_', self._session_id)
            msg = self.decode(message.data)
            await self._message_queue.put(msg[1])

    async def _on_soup_close(self):
        await self._message_queue.stop()
        if self.on_close_coro is not None:
            await self.on_close_coro()
        if self._close_event:
            self._close_event.set()
        self.closed = True

    def decode(self, bytes_: bytes):
        """
        Decode the given bytes into an itch message.
        """
        return Message.from_bytes(bytes_)
