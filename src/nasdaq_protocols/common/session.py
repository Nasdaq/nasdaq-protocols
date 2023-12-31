import abc
import asyncio
from typing import Any, Callable, Coroutine
from itertools import count

import attrs
from .types import Stoppable, Serializable
from .utils import logable, stop_task, Validators
from .message_queue import DispatchableMessageQueue


__all__ = [
    'HearbeatMonitor',
    'Reader',
    'AsyncSession',
    'OnMonitorNoActivityCoro',
    'OnMsgCoro',
    'OnCloseCoro',
    'ReaderFactory',
    'SessionId'
]


OnMonitorNoActivityCoro = Callable[[], Coroutine]
OnMsgCoro = Callable[[Any], Coroutine]
OnCloseCoro = Callable[[], Coroutine]
ReaderFactory = Callable[[Any, OnMsgCoro, OnCloseCoro], 'Reader']


@logable
@attrs.define(auto_attribs=True)
class HearbeatMonitor(Stoppable):
    """
    Monitors for no activity for configured interval.
    Activity is reported to this monitor by calling ping()
    """
    session_id: Any = attrs.field(validator=Validators.not_none())
    interval: float = attrs.field(validator=Validators.not_none())
    on_no_activity_coro: OnMonitorNoActivityCoro = attrs.field(validator=Validators.not_none())
    stop_when_no_activity: bool = attrs.field(kw_only=True, default=True)
    tolerate_missed_heartbeats: int = attrs.field(kw_only=True, default=1)
    _pinged: bool = attrs.field(init=False, default=True)
    _monitor_task: asyncio.Task | None = attrs.field(init=False, default=None)

    def __attrs_post_init__(self):
        self._monitor_task = asyncio.create_task(self._start_monitor(), name=f'{self.session_id}-monitor')
        self.log.debug('%s> monitor started.', self.session_id)

    def ping(self):
        self._pinged = True

    def is_running(self):
        return self._monitor_task is not None and not self._monitor_task.done()

    async def stop(self):
        self._monitor_task = await stop_task(self._monitor_task)

    def is_stopped(self):
        return self._monitor_task is None

    async def _start_monitor(self):
        missed_heartbeats = count(1)
        try:
            while True:
                await asyncio.sleep(self.interval)

                if self._pinged:
                    self._pinged = False
                    missed_heartbeats = count(1)
                    continue

                if next(missed_heartbeats) >= self.tolerate_missed_heartbeats:
                    await self.on_no_activity_coro()
                    if self.stop_when_no_activity:
                        break
        except asyncio.CancelledError:
            pass
        finally:
            self._monitor_task = None


@attrs.define(auto_attribs=True)
class Reader(Stoppable):
    """Abstract Base class for readers.

    A reader is responsible for parsing the received data from the transport
    and dispatching it to the on_msg_coro.

    If the reader detects an end of session, then it signals the on_close_coro.
    """
    session_id: Any = attrs.field(validator=Validators.not_none())
    on_msg_coro: OnMsgCoro = attrs.field(validator=Validators.not_none())
    on_close_coro: OnCloseCoro = attrs.field(validator=Validators.not_none())

    @abc.abstractmethod
    async def on_data(self, data: bytes):
        pass


@attrs.define(auto_attribs=True)
class SessionId:
    host: str = 'nohost'
    port: int = 0

    def set_transport(self, transport: asyncio.Transport):
        self.host, self.port = transport.get_extra_info('peername')


@logable
@attrs.define(auto_attribs=True)
class AsyncSession(asyncio.Protocol, abc.ABC):
    """Abstract base class for async sessions."""

    session_id: SessionId = attrs.field(kw_only=True, validator=Validators.not_none())
    reader_factory: ReaderFactory = attrs.field(kw_only=True, validator=Validators.not_none())
    on_msg_coro: OnMsgCoro = attrs.field(kw_only=True, default=None)
    on_close_coro: OnCloseCoro = attrs.field(kw_only=True, default=None)
    dispatch_on_connect: bool = attrs.field(kw_only=True, default=True)
    _reader: Reader = attrs.field(init=False, default=None)
    _transport: asyncio.Transport = attrs.field(init=False, default=None)
    _closed: bool = attrs.field(init=False, default=False)
    _closing_task: asyncio.Task = attrs.field(init=False, default=None)
    _reader_task: asyncio.Task = attrs.field(init=False, default=None)
    _local_hb_monitor: HearbeatMonitor = attrs.field(init=False, default=None)
    _remote_hb_monitor: HearbeatMonitor = attrs.field(init=False, default=None)
    _msg_queue: DispatchableMessageQueue = attrs.field(init=False, default=None)


    def __attrs_post_init__(self):
        # By default do not dispatch messages
        self._msg_queue = DispatchableMessageQueue(self.session_id)

    async def receive_msg(self):
        """Receive a message from the peer. This is a blocking call."""
        return await self._msg_queue.get()

    def receive_msg_nowait(self):
        """Receive a message from the peer. This is a non-blocking call."""
        return self._msg_queue.get_nowait()

    def is_active(self) -> bool:
        """Returns True if the session is not closed or in closing state."""
        return not (self._closed or self._closing_task)

    def is_closed(self) -> bool:
        return self._closed

    def initiate_close(self):
        """Initiate close of the session."""
        if self._closed or self._closing_task:
            return
        self._closing_task = asyncio.create_task(self.close(), name=f'asyncsession-close:{self.session_id}')

    async def close(self):
        """Close the session, the session cannot be used after this call."""
        if not self._closed:
            self._closed = True
            await stop_task([
                self._msg_queue,
                self._local_hb_monitor,
                self._remote_hb_monitor,
                self._reader,
                self._reader_task
            ])
            if self._transport:
                self._transport.close()
            if self.on_close_coro:
                await self.on_close_coro()

    def start_heartbeats(self, local_hb_interval: int | float, remote_hb_interval: int | float):
        """Starts the heartbeats for the session.

        - if the remote failed heartbeats, then the session is closed.
        - if the local failed heartbeats, then `send_heartbeat` is called.
        """
        self._local_hb_monitor = HearbeatMonitor(
            self.session_id, local_hb_interval, self.send_heartbeat, stop_when_no_activity=False
        )
        self._remote_hb_monitor = HearbeatMonitor(self.session_id, remote_hb_interval, self.close)
        self.log.debug('%s> started heartbeats', self.session_id)

    def start_dispatching(self):
        """
        By default, the session starts with dispatching switched-off.

        Once application level login/handshake is established, this method
        can be called to dispatch messages to the on_msg_coro.
        """
        self._msg_queue.start_dispatching(self.on_msg_coro)
        self.log.debug('%s> started dispatching', self.session_id)

    # asyncio.Protocol overloads.
    def connection_made(self, transport: asyncio.Transport):
        self.log.debug('%s> connected', self.session_id)
        self._transport = transport
        self.session_id.set_transport(self._transport)
        self._reader = self.reader_factory(self.session_id, self._msg_queue.put, self.close)
        if self.dispatch_on_connect:
            self.start_dispatching()

    def data_received(self, data):
        if self._remote_hb_monitor:
            self._remote_hb_monitor.ping()
        self._reader_task = asyncio.create_task(self._reader.on_data(data),
                                                name=f'asyncsession-ondata:{self.session_id}')

    def connection_lost(self, exc):
        self.log.debug('%s> connection lost', self.session_id)
        self.initiate_close()

    @abc.abstractmethod
    def send_msg(self, msg: Serializable):
        pass

    @abc.abstractmethod
    async def send_heartbeat(self):
        pass
