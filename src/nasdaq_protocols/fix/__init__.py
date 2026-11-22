import asyncio
from typing import Callable

from .session import *
from .types import *
from .core import *
from ._reader import FixMessageReader


async def connect_async(remote: tuple[str, int],
                        login_msg: Message,
                        session_fac: Callable[[], FixSession],
                        *,
                        connect_timeout: float | None = None) -> FixSession:
    """
    Connect to the FIX server and login.

    :param remote: tuple of host and port
    :param login_msg: The application Logon message.
    :param session_fac: Factory to create the FixSession, e.g. `Fix44Session` or
                        `lambda: Fix44Session(on_msg_coro=..., expected_seq_num=...)`.
    :param connect_timeout: seconds to wait for connection, None to wait forever.
    :return: FixSession
    :raises ConnectionError: If the connection could not be established within the timeout.
    :raises ConnectionRefusedError: If the server rejects the login.
    """
    loop = asyncio.get_running_loop()

    try:
        _, session_1 = await asyncio.wait_for(
            loop.create_connection(session_fac, *remote),
            timeout=connect_timeout
        )
    except asyncio.TimeoutError:
        raise ConnectionError(f'Unable to connect to {remote}')  # pylint: disable=W0707

    return await session_1.login(login_msg)
