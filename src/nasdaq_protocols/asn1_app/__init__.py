from typing import Callable
from nasdaq_protocols import soup

from .soup_session import (
    OnAns1CloseCoro,
    OnAsn1MessageCoro,
    Ans1SoupSessionId,
    Asn1SoupClientSession
)
from .codegen import generate_soup_app


__all__ = [
    'OnAns1CloseCoro',
    'OnAsn1MessageCoro',
    'Ans1SoupSessionId',
    'generate_soup_app',
    'connect_async_soup'
]


async def connect_async_soup(remote: tuple[str, int], user: str, passwd: str, session_id,  # pylint: disable=R0913
                             session_factory: Callable[[soup.SoupClientSession], Asn1SoupClientSession],
                             sequence: int = 0,
                             client_heartbeat_interval: int = 10,
                             server_heartbeat_interval: int = 10):
    """
    Connect to the Soup-Asn1 server.

    :param remote: tuple of host and port
    :param user: Username to login
    :param passwd:  Password to login
    :param session_id: Name of the session to join [Default=''] .
    :param session_factory: Factory to create a ClientSession.
    :param sequence: The sequence number. [Default=1]
    :param client_heartbeat_interval: seconds between client heartbeats.
    :param server_heartbeat_interval: seconds between server heartbeats.
    :return: ClientSession
    """

    # Create a soup session
    soup_session = await soup.connect_async(
        remote, user, passwd, session_id, sequence=sequence,
        client_heartbeat_interval=client_heartbeat_interval,
        server_heartbeat_interval=server_heartbeat_interval
    )

    # Create an asn1-soup-session (with the soup session created above)
    return session_factory(soup_session)