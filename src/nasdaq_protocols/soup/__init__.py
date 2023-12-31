import asyncio
from typing import Callable
from nasdaq_protocols import common
from .core import *
from .session import *


async def connect_async(remote: tuple[str, int],
                        user: str,
                        passwd: str,
                        session_id: str = '',
                        sequence: int = 0,
                        on_msg_coro: OnSoupMsgCoro = None,
                        on_close_coro: common.OnCloseCoro = None,
                        session_factory: Callable[[], SoupClientSession] = None,
                        client_heartbeat_interval: int = 10,
                        server_heartbeat_interval: int = 10):
    loop = asyncio.get_running_loop()

    def default_session_factory():
        return SoupClientSession(
            on_msg_coro=on_msg_coro,
            on_close_coro=on_close_coro,
            client_heartbeat_interval=client_heartbeat_interval,
            server_heartbeat_interval=server_heartbeat_interval
        )

    _, soup_session = await loop.create_connection(
        session_factory if session_factory else default_session_factory,
        *remote
    )

    login_request = LoginRequest(user, passwd, session_id, str(sequence))

    try:
        return await soup_session.login(login_request)
    except common.EndOfQueue as exc:
        # if a connection is abruptly closed, the incoming message queue will be closed
        raise ConnectionRefusedError("Connection closed by peer.") from exc
