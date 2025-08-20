import asyncio
import logging

import click
from nasdaq_protocols import soup
from nasdaq_protocols.common import utils


LOG = logging.getLogger('soup-tail')


async def _tail_soup(remote, user, passwd, session, sequence, client_heartbeat_interval, server_heartbeat_interval):
    closed = asyncio.Event()
    soup_session = None

    async def on_close():
        print('connection closed.')
        closed.set()

    async def on_msg(msg):
        if isinstance(msg, soup.Debug):
            print(msg.msg)
        else:
            print(f'{soup_session.sequence} : {bytes(msg.data)}')
        print()

    try:
        soup_session = await soup.connect_async(
            remote, user, passwd, session, sequence=sequence,
            on_msg_coro=on_msg,
            on_close_coro=on_close,
            client_heartbeat_interval=client_heartbeat_interval,
            server_heartbeat_interval=server_heartbeat_interval
        )
        LOG.info('connected')
        await closed.wait()
    except asyncio.CancelledError:
        if soup_session is not None:
            await soup_session.close()


@click.command()
@click.option('-h', '--host', required=True)
@click.option('-p', '--port', required=True)
@click.option('-U', '--user', required=True)
@click.option('-P', '--password', required=True)
@click.option('-S', '--session', default='', show_default=True)
@click.option('-s', '--sequence', default=1, show_default=True)
@click.option('-t', '--client-heartbeat-interval', default=10, show_default=True)
@click.option('-T', '--server-heartbeat-interval', default=10, show_default=True)
@click.option('-v', '--verbose', count=True)
def command(host, port, user, password, session, sequence,
            client_heartbeat_interval, server_heartbeat_interval, verbose):
    """ Simple command that tails soup messages"""
    utils.enable_logging_tools(verbose)
    asyncio.run(
        _tail_soup(
            (host, port), user, password, session, sequence, client_heartbeat_interval, server_heartbeat_interval
        )
    )
