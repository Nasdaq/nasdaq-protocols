import asyncio
from typing import Callable

from .session import *
from .types import *
from .core import *
from ._reader import FixMessageReader


async def connect_async(remote: tuple[str, int],
                        login_msg: Message,
                        session_fac: Callable[[], FixSession]):
    loop = asyncio.get_running_loop()

    _, session_1 = await loop.create_connection(session_fac, *remote)

    return await session_1.login(login_msg)
