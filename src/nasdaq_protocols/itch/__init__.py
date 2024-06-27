from typing import Callable
from nasdaq_protocols import soup

from .core import *
from .session import *
from .codegen import *


async def connect_async(remote: tuple[str, int], user: str, passwd: str, session_id,  # pylint: disable=R0913
                        sequence: int = 0,
                        session_factory: Callable[[soup.SoupClientSession], ItchClientSession] = None,
                        on_msg_coro: OnItchMessageCoro = None,
                        on_close_coro: OnItchCloseCoro = None,
                        client_heartbeat_interval: int = 10,
                        server_heartbeat_interval: int = 10):
    """
    Connect to the OUCH server.

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
    :return: SoupClientSession
    """

    # Create a soup session
    soup_session = await soup.connect_async(
        remote, user, passwd, session_id, sequence=sequence,
        client_heartbeat_interval=client_heartbeat_interval,
        server_heartbeat_interval=server_heartbeat_interval
    )

    # Create an itch session (with the soup session created above)
    if session_factory:
        return session_factory(soup_session)

    return ItchClientSession(soup_session, on_msg_coro=on_msg_coro, on_close_coro=on_close_coro)
