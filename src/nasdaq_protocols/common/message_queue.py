import asyncio
from contextlib import asynccontextmanager
from itertools import count
from typing import Any, Callable, Awaitable

import attrs
from .utils import logable, stop_task, Validators
from .types import Stoppable, StateError, EndOfQueue


__all__ = [
    'DispatchableMessageQueue',
    'DispatcherCoro',
]


DispatcherCoro = Callable[[Any], Awaitable[None]]


@logable
@attrs.define(auto_attribs=True)
class DispatchableMessageQueue(Stoppable):
    """A message queue that dispatches messages to a coro."""

    session_id: Any = attrs.field(validator=Validators.not_none())
    on_msg_coro: DispatcherCoro = None
    _closed: bool = attrs.field(init=False, default=False)
    _msg_queue: asyncio.Queue = attrs.field(init=False, default=None)
    _recv_task: asyncio.Task = attrs.field(init=False, default=None)
    _dispatcher_task: asyncio.Task = attrs.field(init=False, default=None)

    def __attrs_post_init__(self):
        self._msg_queue = asyncio.Queue()
        self.start_dispatching(self.on_msg_coro)

    async def put(self, msg: Any):
        await self._msg_queue.put(msg)

    async def get(self):
        """get an entry from the queue.

        if the underlying queue contains entries, the first element is fetched and returned,
        if the queue contains no entries, a coro is awaited, which will wait until queue contains
        an entry.

        Raises:
            StateError - if the dispatcher is already in progress
            EndOfQueue - if queue is stopped the underlying queue contains no entries.
        """
        msg = self.get_nowait()
        return msg if msg else await self._blocking_read()

    def put_nowait(self, msg: Any):
        self._msg_queue.put_nowait(msg)

    def get_nowait(self):
        if self._dispatcher_task:
            raise StateError(f'{self.session_id}-dispatcher, Dispatcher is running, cannot use get_no_wait')
        try:
            return self._msg_queue.get_nowait()
        except asyncio.QueueEmpty:
            if self._closed:
                raise EndOfQueue()

    @asynccontextmanager
    async def pause_dispatching(self):
        if not self._dispatcher_task:
            raise StateError(f'Dispatcher is not running, cannot pause')
        self._dispatcher_task = await stop_task(self._dispatcher_task)
        try:
            self.log.debug('%s> queue dispatcher paused.', self.session_id)
            yield
        finally:
            self._dispatcher_task = asyncio.create_task(self._start_dispatching(), name=f'{self.session_id}-dispatcher')
            self.log.debug('%s> queue dispatcher resumed.', self.session_id)

    def start_dispatching(self, on_msg_coro: DispatcherCoro):
        if self._dispatcher_task:
            raise StateError(f'Dispatcher is already running, cannot start')
        if on_msg_coro:
            self.on_msg_coro = on_msg_coro
            self._dispatcher_task = asyncio.create_task(self._start_dispatching(), name=f'{self.session_id}-dispatcher')
            self.log.debug('%s> queue dispatcher started.', self.session_id)

    async def stop(self):
        if not self._closed:
            self._closed = True
            self._dispatcher_task = await stop_task(self._dispatcher_task)
            self._recv_task = await stop_task(self._recv_task)

    def is_stopped(self):
        return self._closed

    async def _start_dispatching(self):
        counter = count(1)
        while True:
            try:
                msg = await self._msg_queue.get()
                await self.on_msg_coro(msg)
                self.log.debug('%s> dispatched message %s', self.session_id, next(counter))
            except asyncio.CancelledError:
                break
            except Exception as exc:
                self.log.warning('%s> Exception when handling message, %s', self.session_id, exc)

    async def _blocking_read(self):
        self._recv_task = asyncio.create_task(self._msg_queue.get())
        try:
            return await self._recv_task
        except asyncio.CancelledError:
            raise EndOfQueue()  # pylint: disable=W0707
        finally:
            self._recv_task = await stop_task(self._recv_task)
