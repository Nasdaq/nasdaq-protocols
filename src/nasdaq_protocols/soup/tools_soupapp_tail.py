import asyncio


__all__ = [
    'tail_soup_app'
]


async def tail_soup_app(remote,
                        user,
                        passwd,
                        session,
                        sequence,
                        app_connector,
                        client_heartbeat_interval,
                        server_heartbeat_interval):
    closed = asyncio.Event()
    app_session = None

    async def on_close():
        print('connection closed.')
        closed.set()

    async def on_msg(msg):
        print(f'{app_session.soup_session.sequence} : {msg}')
        print()

    try:
        app_session = await app_connector(
            remote, user, passwd, session, sequence,
            on_msg_coro=on_msg,
            on_close_coro=on_close,
            client_heartbeat_interval=client_heartbeat_interval,
            server_heartbeat_interval=server_heartbeat_interval
        )
        print('connected')
        await closed.wait()
    except asyncio.CancelledError:
        if app_session is not None:
            await app_session.close()
