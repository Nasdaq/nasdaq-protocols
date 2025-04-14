from typing import Callable
from nasdaq_protocols import soup

from .core import (
    Message
)
from .session import (
    OnSqfMessageCoro,
    OnSqfCloseCoro,
    SqfSessionId,
    ClientSession
)


__all__ = [
    'Message',
    'OnSqfMessageCoro',
    'OnSqfCloseCoro',
    'SqfSessionId',
    'ClientSession',
    'connect_async'
]


async def connect_async(remote: tuple[str, int], user: str, passwd: str, session_id,  # pylint: disable=R0913
                        sequence: int = 0,
                        session_factory: Callable[[soup.SoupClientSession], ClientSession] = None,
                        on_msg_coro: OnSqfMessageCoro = None,
                        on_close_coro: OnSqfCloseCoro = None,
                        client_heartbeat_interval: int = 10,
                        server_heartbeat_interval: int = 10,
                        connect_timeout: int = 5) -> ClientSession:
    """
    Connect to the sqf server.

    :param remote: tuple of host and port
    :param user: Username to login
    :param passwd:  Password to login
    :param session_id: Name of the session to join [Default=''] .
    :param sequence: The sequence number. [Default=1]
    :param session_factory: Factory to create a SoupClientSession.
    :param on_msg_coro: callback, message from server.
    :param on_close_coro: callback, connection closed .
    :param client_heartbeat_interval: seconds between client heartbeats.
    :param server_heartbeat_interval: seconds between server heartbeats.
    :param connect_timeout: seconds to wait for connection.
    :return: SoupClientSession
    """

    # Create a soup session
    soup_session = await soup.connect_async(
        remote, user, passwd, session_id, sequence=sequence,
        client_heartbeat_interval=client_heartbeat_interval,
        server_heartbeat_interval=server_heartbeat_interval,
        connect_timeout=connect_timeout
    )

    # Create an sqf session (with the soup session created above)
    if session_factory:
        return session_factory(soup_session)

    return ClientSession(soup_session, on_msg_coro=on_msg_coro, on_close_coro=on_close_coro)
