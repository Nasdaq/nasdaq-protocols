"""
nasdaq_protocols.soup.session contains implementation of the soup session.
"""
import abc
import asyncio
from typing import Any, Awaitable, Callable, ClassVar

import attrs
from nasdaq_protocols import common
from ._reader import SoupMessageReader
from .core import (
    SoupMessage,
    LoginRequest,
    LoginAccepted,
    LoginRejected,
    SequencedData,
    UnSequencedData,
    Debug,
    ClientHeartbeat,
    ServerHeartbeat,
    EndOfSession,
    LogoutRequest
)

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
    """
    Identifier for a soup session.

    :param session_type: The type of the session, either 'client' or 'server'.
    :param user: The username.
    :param session: The session id.
    """
    session_type: str = 'norole'
    user: str = 'nouser'
    session: str = 'nosession'

    def update(self,
               msg: LoginRequest | LoginAccepted,
               transport: asyncio.Transport | None = None):
        """
        Update the session id with the more information as and when it is available.

        :param msg: LoginRequest or LoginAccepted message.
        :param transport: asyncio.Transport object.
        :return: self
        """
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
    """
    Base class for SoupBinTCP[server, client] session.

    :param on_msg_coro: Coroutine to be called when a message is received.
    :param on_close_coro: Coroutine to be called when the session is closed.
    :param sequence: The sequence number. [Default=1]
    :param client_heartbeat_interval: The client heartbeat interval in seconds. [Default=10]
    :param server_heartbeat_interval: The server heartbeat interval in seconds. [Default=10]
    :param session_id: The session id.
    """

    SessionType: ClassVar[str] = None

    on_msg_coro: OnSoupMsgCoro = None
    on_close_coro: common.OnCloseCoro = None
    sequence: int = attrs.field(default=1, kw_only=True)
    client_heartbeat_interval: int = attrs.field(default=10, kw_only=True)
    server_heartbeat_interval: int = attrs.field(default=10, kw_only=True)
    session_id: SoupSessionId = attrs.Factory(SoupSessionId)
    reader_factory: common.ReaderFactory = attrs.field(init=False, default=SoupMessageReader)

    def __init_subclass__(cls, **kwargs):  # pylint: disable=arguments-renamed
        if cls.SessionType:
            return
        if 'session_type' in kwargs:
            cls.SessionType = kwargs['session_type']
        else:
            cls.log.info('Setting base')
            cls.SessionType = 'base'

    def __attrs_post_init__(self):
        self.session_id.session_type = self.SessionType
        super().__attrs_post_init__()

    def send_msg(self, msg: SoupMessage) -> None:
        """
        Send a soup message to the server.

        :param msg: SoupMessage object.
        """
        _, bytes_ = msg.to_bytes()
        self._transport.write(bytes_)
        self.log.debug('%s> sent %s', self.session_id, str(bytes_))

        if not msg.is_heartbeat() and self._local_hb_monitor:
            self._local_hb_monitor.ping()
        if isinstance(msg, SequencedData):
            self.log.debug('%s> sent sequenced message, seq = %d', self.session_id, self.sequence)
            self.sequence += 1

    def send_debug(self, text: str) -> None:
        """
        Send a debug message to the peer.

        :param text: debug text
        """
        self.send_msg(Debug(text))

    def logout(self) -> None:
        """
        Logout.

        The session is closed after sending the logout request.
        :return:
        """
        self.log.debug('%s> logging out', self.session_id)
        self.send_msg(LogoutRequest())
        self.initiate_close()


@attrs.define(auto_attribs=True)
@common.logable
class SoupClientSession(SoupSession, session_type='client'):
    """
    SoupBinTCP client session.

    Upon successful connecting to the soup server, the client session is instantiated.
    """
    dispatch_on_connect: bool = False

    async def login(self, msg: LoginRequest):
        """
        Login to the soup server.

        This is supposed to be the first message to be sent to server upon connection successful.

        :param msg: LoginRequest message.
        :return: self
        :raises ConnectionRefusedError: If the server rejects the login request.
        """
        self.log.debug('%s> logging in', self.session_id)
        self.session_id.update(msg)
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
        return self

    async def send_heartbeat(self):
        """
        Send heartbeat to the server.

        :meta private:
        """
        self.send_msg(ClientHeartbeat())

    def send_unseq_data(self, data: bytes):
        """
        Send unsequenced data to the server.
        :param data: application payload
        """
        self.send_msg(UnSequencedData(data))


@attrs.define(auto_attribs=True)
@common.logable
class SoupServerSession(SoupSession, session_type='server'):
    """
    Base class for all soup server sessions.

    Any class that implements a soup server session must inherit from this class.
    and implement the following methods:

    - on_login
    - on_unsequenced

    """
    on_msg_coro: OnSoupMsgCoro = attrs.field(init=False)
    _logged_in: bool = attrs.field(init=False, default=False)

    def __attrs_post_init__(self):
        self.on_msg_coro = self._on_msg
        self.on_close_coro = self.close
        super().__attrs_post_init__()

    @abc.abstractmethod
    async def on_login(self, msg: LoginRequest) -> LoginAccepted | LoginRejected:
        """
        Handle the login request from the client.

        :param msg: LoginRequest message.
        :return: LoginAccepted or LoginRejected message.
        """

    @abc.abstractmethod
    async def on_unsequenced(self, msg: UnSequencedData) -> None:
        """
        Handle the unsequenced data from the client.

        :param msg: UnSequencedData message.
        """

    def send_seq_msg(self, data: bytes | SequencedData) -> None:
        """
        Send sequenced data to the client.

        :param data: application payload
        """
        if not isinstance(data, SequencedData):
            data = SequencedData(data)
        self.send_msg(data)

    def end_session(self):
        """
        End the session.
        """
        self.send_msg(EndOfSession())
        self.initiate_close()

    async def on_debug(self, msg: Debug) -> None:
        self.log.info('%s> ++ client debug : %s', self.session_id, msg)

    async def send_heartbeat(self):
        """
        Send heartbeat to the client.

        This is called automatically by the session when the heartbeat interval expires.
        :meta private:
        """
        self.send_msg(ServerHeartbeat())

    async def _on_msg(self, msg: SoupMessage) -> None:
        if isinstance(msg, LoginRequest):
            self.session_id.update(msg)
            await self._handle_login(msg)
        elif isinstance(msg, UnSequencedData):
            await self.on_unsequenced(msg)
        elif isinstance(msg, Debug):
            await self.on_debug(msg)
        elif isinstance(msg, LogoutRequest):
            self.log.debug('%s> client logged out', self.session_id)
            await self.close()

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
