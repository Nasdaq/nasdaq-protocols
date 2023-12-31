import abc
import asyncio
from typing import Any, Awaitable, Callable, ClassVar

import attrs
from nasdaq_protocols import common
from ._reader import SoupMessageReader
from .core import *


__all__ = [
    'OnSoupMsgCoro',
    'SoupSessionId',
    'SoupSession',
    'SoupClientSession',
    'SoupServerSession',
    'OnSoupMsgCoro'
]


OnSoupMsgCoro = Callable[[Any], Awaitable[None]]


@attrs.define(auto_attribs=True)
class SoupSessionId(common.SessionId):
    session_type: str = 'norole'
    user: str = 'nouser'
    session: str = 'nosession'

    def update(self,
               msg: LoginRequest | LoginAccepted,
               transport: asyncio.Transport | None = None):
        if transport:
            self.set_transport(transport)
        elif isinstance(msg, LoginRequest):
            self.user = msg.user
        elif isinstance(msg, LoginAccepted):
            self.session = msg.session_id

    def __str__(self):
        return f'{self.session_type}-{self.user}_{self.session}@{self.host}:{self.port}'


@attrs.define(auto_attribs=True)
@common.logable
class SoupSession(common.AsyncSession, abc.ABC):
    SessionType: ClassVar[str] = 'base'

    on_msg_coro: OnSoupMsgCoro = None
    on_close_coro: common.OnCloseCoro = None
    sequence: int = attrs.field(default=1, kw_only=True)
    client_heartbeat_interval: int = attrs.field(default=10, kw_only=True)
    server_heartbeat_interval: int = attrs.field(default=10, kw_only=True)
    session_id: SoupSessionId = attrs.Factory(SoupSessionId)
    reader_factory: common.ReaderFactory = attrs.field(init=False, default=SoupMessageReader)

    def __init_subclass__(cls, **kwargs):  # pylint: disable=arguments-renamed
        if 'session_type' in kwargs:
            cls.SessionType = kwargs['session_type']
        else:
            cls.SessionType = 'base'

    def __attrs_post_init__(self):
        self.session_id.session_type = self.SessionType
        super().__attrs_post_init__()

    def send_msg(self, msg: SoupMessage):
        bytes_ = msg.to_bytes()
        self._transport.write(bytes_)
        self.log.debug('%s> sent %s', self.session_id, str(bytes_))

        if not msg.is_heartbeat() and self._local_hb_monitor:
            self._local_hb_monitor.ping()
        if isinstance(msg, SequencedData):
            self.log.debug('%s> sent sequenced message, seq = %d', self.session_id, self.sequence)
            self.sequence += 1

    def send_debug(self, text: str):
        self.send_msg(Debug(text))

    async def logout(self):
        self.log.debug('%s> logging out', self.session_id)
        self.send_msg(LogoutRequest())
        await self.close()


@attrs.define(auto_attribs=True)
@common.logable
class SoupClientSession(SoupSession, session_type='client'):
    dispatch_on_connect: bool = False

    async def login(self, msg: LoginRequest):
        self.log.debug('%s> logging in', self.session_id)
        self.send_msg(msg)

        reply = await self.receive_msg()
        if not isinstance(reply, LoginAccepted):
            self.log.error('%s> Login rejected, %s', self.session_id, str(reply))
            await self.close()
            raise ConnectionRefusedError(str(reply))

        self.session_id.update(reply)
        self.sequence = reply.sequence
        self.log.debug('%s> session established, sequence = %d', self.session_id, self.sequence)
        self.start_heartbeats(self.client_heartbeat_interval, self.server_heartbeat_interval)
        self.start_dispatching()

    async def send_heartbeat(self):
        self.send_msg(ClientHeartbeat())

    def send_unseq_data(self, data: bytes):
        self.send_msg(UnSequencedData(data))


@attrs.define(auto_attribs=True)
@common.logable
class SoupServerSession(SoupSession, session_type='server'):
    on_msg_coro: OnSoupMsgCoro = attrs.field(init=False)
    _logged_in: bool = attrs.field(init=False, default=False)

    def __attrs_post_init__(self):
        self.on_msg_coro = self._on_msg
        self.on_close_coro = self.close
        super().__attrs_post_init__()

    @abc.abstractmethod
    async def on_login(self, msg: LoginRequest) -> LoginAccepted | LoginRejected:
        pass

    @abc.abstractmethod
    async def on_unsequenced(self, msg: UnSequencedData) -> None:
        pass

    def send_seq_msg(self, data: bytes):
        if not isinstance(data, SequencedData):
            data = SequencedData(data)
        self.send_msg(data)

    def end_session(self):
        self.send_msg(EndOfSession())

    async def on_debug(self, msg: Debug) -> None:
        self.log.info('%s> ++ client debug : %s', msg)

    async def send_heartbeat(self):
        self.send_msg(ServerHeartbeat())

    async def _on_msg(self, msg: SoupMessage) -> None:
        if isinstance(msg, LoginRequest):
            self.session_id.update(msg)
            await self._handle_login(msg)
        elif isinstance(msg, UnSequencedData):
            await self.on_unsequenced(msg)
        elif isinstance(msg, Debug):
            await self.on_debug(msg)

    async def _handle_login(self, msg: LoginRequest) -> None:
        if self._logged_in:
            self.log.error('Login received for already logged in session.')
            raise common.StateError('Login received for already logged in session.')

        reply = await self.on_login(msg)
        self.send_msg(reply)

        if isinstance(reply, LoginAccepted):
            self.session_id.update(reply)
            self._logged_in = True
            self.start_heartbeats(self.client_heartbeat_interval, self.server_heartbeat_interval)
        else:
            await self.close()


