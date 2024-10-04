import abc
import asyncio
from typing import Any, Callable, Coroutine, Generic, Type, TypeVar
from itertools import count

import attrs
from .types import Stoppable, Serializable, StateError
from .utils import logable, stop_task, Validators
from .message_queue import DispatchableMessageQueue


__all__ = [
    'HeartbeatMonitor',
    'Reader',
    'AsyncSession',
    'OnMonitorNoActivityCoro',
    'OnMsgCoro',
    'OnCloseCoro',
    'ReaderFactory',
    'SessionId'
]
T = TypeVar('T')

OnMonitorNoActivityCoro = Callable[[], Coroutine]
OnMsgCoro = Callable[[Any], Coroutine]
OnCloseCoro = Callable[[], Coroutine]
ReaderFactory = Callable[[Any, OnMsgCoro, OnCloseCoro], 'Reader']


@logable
@attrs.define(auto_attribs=True)
class HeartbeatMonitor(Stoppable):
    """
    Monitor that trips the `on_no_activity_coro` if no activity is detected.

    Currently, activity is externally signalled by calling the `ping` method.

    :param session_id: The session id.
    :param interval: interval in seconds at which the monitor checks for activity.
    :param on_no_activity_coro: coroutine to be called when no activity is detected.
    :param stop_when_no_activity: If True, the monitor stops when no activity is detected.
    :param tolerate_missed_heartbeats: number of missed heartbeats to tolerate.
    """
    session_id: Any = attrs.field(validator=Validators.not_none())
    interval: float = attrs.field(validator=Validators.not_none())
    on_no_activity_coro: OnMonitorNoActivityCoro = attrs.field(validator=Validators.not_none())
    stop_when_no_activity: bool = attrs.field(kw_only=True, default=True)
    tolerate_missed_heartbeats: int = attrs.field(kw_only=True, default=1)
    name: str = attrs.field(kw_only=True, default='monitor')
    _pinged: bool = attrs.field(init=False, default=True)
    _monitor_task: asyncio.Task | None = attrs.field(init=False, default=None)

    def __attrs_post_init__(self):
        self._monitor_task = asyncio.create_task(self._start_monitor(), name=f'{self.session_id}-{self.name}')
        self.log.debug('%s> %s started.', self.session_id, self.name)

    def ping(self) -> None:
        """Ping the monitor."""
        self._pinged = True

    def is_running(self) -> bool:
        """Returns True if the monitor is running."""
        return self._monitor_task is not None and not self._monitor_task.done()

    async def stop(self) -> None:
        """Stop the monitor."""
        self._monitor_task = await stop_task(self._monitor_task)

    def is_stopped(self) -> bool:
        return not self.is_running()

    async def _start_monitor(self):
        missed_heartbeats = count(1)
        try:
            while True:
                await asyncio.sleep(self.interval)

                if self._pinged:
                    self.log.debug('%s> %s pinged.', self.session_id, self.name)
                    self._pinged = False
                    missed_heartbeats = count(1)
                    continue

                if next(missed_heartbeats) >= self.tolerate_missed_heartbeats:
                    self.log.debug('%s> %s no activity detected.', self.session_id, self.name)
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

    :param session_id: The session id.
    :param on_msg_coro: coroutine to be called for every message parsed.
    :param on_close_coro: coroutine to be called when the reader detects end of session.
    """
    session_id: Any = attrs.field(validator=Validators.not_none())
    on_msg_coro: OnMsgCoro = attrs.field(validator=Validators.not_none())
    on_close_coro: OnCloseCoro = attrs.field(validator=Validators.not_none())

    @abc.abstractmethod
    async def on_data(self, data: bytes):
        """Called when data is received from the transport."""


@attrs.define(auto_attribs=True)
class SessionId:
    """
    A basic session id.
    """
    host: str = 'nohost'
    port: int = 0

    def set_transport(self, transport: asyncio.Transport) -> None:
        """Once the transport is available, the host and port are updated."""
        self.host, self.port = transport.get_extra_info('peername')


@logable
@attrs.define(auto_attribs=True)
class AsyncSession(asyncio.Protocol, abc.ABC, Generic[T]):
    """
    Abstract base class for async sessions.

    Once the transport is available, the session creates a new reader using the
    `reader_factory` and starts parsing the incoming bytes.

    By default, the session starts in a dispatching mode, meaning the incoming messages
    are dispatched to the `on_msg_coro`. This can be changed by setting `dispatch_on_connect=False`.

    :param session_id: The session id.
    :param reader_factory: A callable that returns a reader.
    :param on_msg_coro: coroutine to be called when a message is received.
    :param on_close_coro: coroutine to be called when the session is closed.
    :param dispatch_on_connect: If True, the session starts with dispatching once connected.
    """
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
    _local_hb_monitor: HeartbeatMonitor = attrs.field(init=False, default=None)
    _remote_hb_monitor: HeartbeatMonitor = attrs.field(init=False, default=None)
    _msg_queue: DispatchableMessageQueue = attrs.field(init=False, default=None)

    def __attrs_post_init__(self):
        # By default do not dispatch messages
        self._msg_queue = DispatchableMessageQueue(self.session_id)

    async def receive_msg(self) -> Type[T]:
        """
        Receive a message from the peer. This is a blocking call.
        This call blocks until a new message is available.

        If the session is dispatching messages, then this call raises an exception.

        :return Any: The message received.
        """
        return await self._msg_queue.get()

    def receive_msg_nowait(self) -> Type[T] | None:
        """
        Receive a message from the peer. This is a non-blocking call.

        :return Any: The message received.
        """
        return self._msg_queue.get_nowait()

    def is_active(self) -> bool:
        """Returns True if the session is not closed or in closing state."""
        return not (self._closed or self._closing_task)

    def is_closed(self) -> bool:
        """
        Returns True if the session is closed.
        :return:
        """
        return self._closed

    def initiate_close(self) -> None:
        """
        Initiate close of the session.
        An asynchronous task is created which will close the session and all its
        associates.

        Poll `is_closed` to check if the session is closed or use the
        `on_close_coro` callback to be notified when the session is closed.
        """
        if self._closed or self._closing_task:
            return
        self._closing_task = asyncio.create_task(self.close(), name=f'asyncsession-close:{self.session_id}')

    async def close(self):
        """
        Close the session, the session cannot be used after this call.
        """
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
        - if the local heartbeat timer expires, then `send_heartbeat` is called.
        """
        self._local_hb_monitor = HeartbeatMonitor(
            f'{self.session_id}-local-monitor',
            local_hb_interval,
            self.send_heartbeat,
            stop_when_no_activity=False
        )
        self._remote_hb_monitor = HeartbeatMonitor(
            f'{self.session_id}-remote-monitor', remote_hb_interval, self.close
        )
        self.log.debug('%s> started heartbeats', self.session_id)

    def set_handlers(self, on_msg_coro: OnMsgCoro = None, on_close_coro: OnCloseCoro = None):
        if on_msg_coro:
            if self._msg_queue.is_dispatching():
                raise StateError('Dispatcher already active, cannot set on_msg handler')
            self.on_msg_coro = on_msg_coro
        if on_close_coro:
            self.on_close_coro = on_close_coro
            if self._closing_task is not None or self._closed:
                raise StateError("Session already closed, cannot set close handler")

    def start_dispatching(self):
        """
        By default, the session starts with dispatching switched-on.

        If, the session is created with dispatching-off, then at any point in time
        during the lifetime of this session, dispatching can be switched-on by calling
        this method.
        """
        if self.on_msg_coro:
            self._msg_queue.start_dispatching(self.on_msg_coro)
            self.log.debug('%s> started dispatching', self.session_id)

    # asyncio.Protocol overloads.
    def connection_made(self, transport: asyncio.Transport):
        """
        :meta private:
        """
        self.log.debug('%s> connected', self.session_id)
        self._transport = transport
        self.session_id.set_transport(self._transport)
        self._reader = self.reader_factory(self.session_id, self._msg_queue.put, self.close)
        if self.dispatch_on_connect:
            self.start_dispatching()

    def data_received(self, data):
        """
        :meta private:
        """
        if self._remote_hb_monitor:
            self._remote_hb_monitor.ping()
        self._reader_task = asyncio.create_task(self._reader.on_data(data),
                                                name=f'asyncsession-ondata:{self.session_id}')

    def connection_lost(self, exc):
        """
        :meta private:
        """
        self.log.debug('%s> connection lost', self.session_id)
        self.initiate_close()

    @abc.abstractmethod
    def send_msg(self, msg: Serializable[T]) -> None:
        """
        Send a message to the peer.
        :param msg: Any message that is serializable.
        """

    @abc.abstractmethod
    async def send_heartbeat(self):
        """
        Callback to send a heartbeat to the peer.
        :meta private:
        """
