"""
The SoupBinTCP protocol is a simple, lightweight, and fast protocol that
provides reliable, ordered, and error-checked delivery of messages between
client and server. It is designed for high-performance market data and order
entry applications. The protocol is based on the TCP/IP protocol suite and
uses TCP as its transport protocol.

This module provides a SoupBinTCP client implementation that can be used to
connect to the SoupBinTCP servers.

Though SoupBinTCP is meant for latency sensitive applications, there are
numerous times when the client application is not latency sensitive and
would like to talk to the soup server, Say in testing or writing a monitoring tool.

In such cases, the client application can use the SoupBinTCP client provided by this module.
"""
import asyncio
from typing import Callable

from nasdaq_protocols import common
from .core import (
    InvalidSoupMessage,
    LoginRejectReason,
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
from .session import (
    OnSoupMsgCoro,
    SoupSessionId,
    SoupSession,
    SoupClientSession,
    SoupServerSession, SoupClientSessionSync
)


__all__ = [
    'InvalidSoupMessage',
    'LoginRejectReason',
    'SoupMessage',
    'LoginRequest',
    'LoginAccepted',
    'LoginRejected',
    'SequencedData',
    'UnSequencedData',
    'Debug',
    'ClientHeartbeat',
    'ServerHeartbeat',
    'EndOfSession',
    'LogoutRequest',
    'OnSoupMsgCoro',
    'SoupSessionId',
    'SoupSession',
    'SoupClientSession',
    'SoupServerSession',
    'SoupClientSessionSync',
    'connect_async',
    'connect'
]


async def connect_async(remote: tuple[str, int],  # pylint: disable=too-many-arguments, too-many-locals
                        user: str,
                        passwd: str,
                        session_id: str = '',
                        sequence: int = 1,
                        on_msg_coro: OnSoupMsgCoro = None,
                        on_close_coro: common.OnCloseCoro = None,
                        session_factory: Callable[[], SoupClientSession] = None,
                        client_heartbeat_interval: int = 10,
                        server_heartbeat_interval: int = 10,
                        connect_timeout: int = 5) -> SoupClientSession:
    """
    Connect asynchronously to the SoupBinTCP server and login.

    Using `:param sequence` the client can specify the sequence number of the next
    message it expects to receive. The server will then send all messages with sequence
    numbers greater than the specified sequence number.

    To connect to the start of the stream, specify sequence=1, which is the default.
    To connect to the end of the stream, specify sequence=0, new messages will be received.
    To connect to a specific message, specify the sequence number of the message.

    :param remote: tuple of host and port
    :param user: Username to login
    :param passwd:  Password to login
    :param session_id: Name of the session to join [Default=''] .
    :param sequence: The sequence number. [Default=1]
    :param on_msg_coro: callback, message from server.
    :param on_close_coro: callback, connection closed .
    :param session_factory: Factory to create a SoupClientSession.
    :param client_heartbeat_interval: seconds between client heartbeats.
    :param server_heartbeat_interval: seconds between server heartbeats.
    :param connect_timeout: seconds to wait for connection.
    :return: SoupClientSession
    """
    loop = asyncio.get_running_loop()

    def default_session_factory():
        return SoupClientSession(
            on_msg_coro=on_msg_coro,
            on_close_coro=on_close_coro,
            client_heartbeat_interval=client_heartbeat_interval,
            server_heartbeat_interval=server_heartbeat_interval
        )

    try:
        _, soup_session = await asyncio.wait_for(
            loop.create_connection(
                session_factory if session_factory else default_session_factory,
                *remote
            ),
            timeout=connect_timeout
        )
    except asyncio.TimeoutError:
        raise ConnectionError(f'Unable to connect to {remote}')

    try:
        login_request = LoginRequest(user, passwd, session_id, str(sequence))
        return await soup_session.login(login_request)
    except common.EndOfQueue as exc:
        # if a connection is abruptly closed, the incoming message queue will be closed
        raise ConnectionRefusedError("Connection closed by peer.") from exc


def connect(remote: tuple[str, int],
            user: str,
            passwd: str,
            session_id: str = '',
            sequence: int = 1,
            client_heartbeat_interval: int = 10,
            server_heartbeat_interval: int = 10) -> SoupClientSessionSync:
    """
    Connect to the SoupBinTCP server and login.

    Using `:param sequence` the client can specify the sequence number of the next
    message it expects to receive. The server will then send all messages with sequence
    numbers greater than the specified sequence number.

    To connect to the start of the stream, specify sequence=1, which is the default.
    To connect to the end of the stream, specify sequence=0, new messages will be received.
    To connect to a specific message, specify the sequence number of the message.

    NOTE: This is experimental and should be used with caution.

    :param remote: tuple of host and port
    :param user: Username to login
    :param passwd:  Password to login
    :param session_id: Name of the session to join [Default=''] .
    :param sequence: The sequence number. [Default=1]
    :param client_heartbeat_interval: seconds between client heartbeats.
    :param server_heartbeat_interval: seconds between server heartbeats.
    :return: SoupClientSessionSync
    """
    sync_executor = common.SyncExecutor(f'soup-connect-{user}')
    try:
        async_session = sync_executor.execute(
            connect_async(
                remote,
                user,
                passwd,
                session_id,
                sequence,
                client_heartbeat_interval=client_heartbeat_interval,
                server_heartbeat_interval=server_heartbeat_interval
            )
        )
        return SoupClientSessionSync(async_session, sync_executor)
    except Exception as exc:
        sync_executor.stop()
        raise exc
