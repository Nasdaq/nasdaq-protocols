import asyncio
from itertools import count


async def tail_itch(remote,
                    user,
                    passwd,
                    session,
                    sequence,
                    itch_connector,
                    client_heartbeat_interval,
                    server_heartbeat_interval,
                    connect_timeout):
    closed = asyncio.Event()
    sequence_counter = count(1)

    async def on_close():
        print('Connection closed.')
        closed.set()

    async def on_msg(msg):
        print(next(sequence_counter), msg)
        print()

    itch_session = None
    try:
        itch_session = await itch_connector(
            remote, user, passwd, session, sequence,
            on_msg_coro=on_msg,
            on_close_coro=on_close,
            client_heartbeat_interval=client_heartbeat_interval,
            server_heartbeat_interval=server_heartbeat_interval,
            connect_timeout=connect_timeout
        )
        print(f'Connecting... to {remote}')
        await closed.wait()
    except asyncio.CancelledError:
        if itch_session is not None:
            await itch_session.close()
    except Exception as exc:  # pylint: disable=broad-except
        print(exc)
