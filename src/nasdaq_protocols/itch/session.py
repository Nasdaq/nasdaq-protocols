import asyncio
from typing import Callable, Type, Awaitable

import attrs
from nasdaq_protocols.common import DispatchableMessageQueue, logable
from nasdaq_protocols import soup
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
class ItchSessionId:
    soup_session_id: soup.SoupSessionId = None

    def __str__(self):
        if self.soup_session_id:
            return f'itch-{self.soup_session_id}'
        return 'itch-nosoup'


@attrs.define(auto_attribs=True)
@logable
class ClientSession:
    soup_session: soup.SoupClientSession
    on_msg_coro: OnItchMessageCoro = None
    on_close_coro: OnItchCloseCoro = None
    closed: bool = False
    _session_id: ItchSessionId = None
    _close_event: asyncio.Event = None
    _message_queue: DispatchableMessageQueue = None

    def __attrs_post_init__(self):
        self._session_id = ItchSessionId(self.soup_session.session_id)
        self._message_queue = DispatchableMessageQueue(self._session_id, self.on_msg_coro)
        self.soup_session.set_handlers(on_msg_coro=self._on_soup_message, on_close_coro=self._on_soup_close)
        self.soup_session.start_dispatching()

    async def receive_message(self):
        """
        Asynchronously receive a message from the itch session.

        This method blocks until a message is received by the session.
        """
        return await self._message_queue.get()

    async def close(self):
        """
        Asynchronously close the itch session.
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
            await self._message_queue.put(
                self.decode(message.data)[1]
            )

    async def _on_soup_close(self):
        await self._message_queue.stop()
        if self.on_close_coro is not None:
            await self.on_close_coro()
        if self._close_event:
            self._close_event.set()
        self.closed = True

    @classmethod
    def decode(cls, bytes_: bytes):
        """
        Decode the given bytes into an itch message.
        """
        return Message.from_bytes(bytes_)
