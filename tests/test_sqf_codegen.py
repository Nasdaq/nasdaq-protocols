import pytest
from nasdaq_protocols.sqf import codegen
from .soup_app_codegen_tests import soup_clientapp_codegen_tests
from .soup_client_app_tests import soup_clientapp_common_tests
from .testdata import *


EXPECTED_GENERATED_CODE = """
import asyncio
from enum import Enum
from typing import Callable, Awaitable, Type

import click
from nasdaq_protocols.common import utils
from nasdaq_protocols.common import logable
from nasdaq_protocols.common.message import *
from nasdaq_protocols import soup, sqf


__all__ = [
    'Message',
    'ClientSession',
    'connect_async',
    'tail_messages',
    'Quote',
    'QuoteMessage',
]


@logable
class Message(sqf.Message, app_name='test'):
    def __init_subclass__(cls, **kwargs):
        cls.log.debug('subclassing %s, params = %s', cls.__name__, str(kwargs))
        if 'indicator' not in kwargs:
            raise ValueError('expected "indicator" when subclassing test.Message')

        kwargs['app_name'] = 'test'
        super().__init_subclass__(**kwargs)


class ClientSession(sqf.ClientSession):
    @classmethod
    def decode(cls, bytes_: bytes) -> [int, Message]:
        return Message.from_bytes(bytes_)


async def connect_async(remote: tuple[str, int], user: str, passwd: str, session_id,
                        sequence: int = 0,
                        session_factory: Callable[[soup.SoupClientSession], ClientSession] = None,
                        on_msg_coro: Callable[[Type[Message]], Awaitable[None]] = None,
                        on_close_coro: Callable[[], Awaitable[None]] = None,
                        client_heartbeat_interval: int = 10,
                        server_heartbeat_interval: int = 10,
                        connect_timeout: int = 5) -> ClientSession:
    if session_factory is None:
        def session_factory(x):
            return ClientSession(x, on_msg_coro=on_msg_coro, on_close_coro=on_close_coro)

    return await sqf.connect_async(
        remote, user, passwd, session_id, sequence,
        session_factory, on_msg_coro, on_close_coro,
        client_heartbeat_interval, server_heartbeat_interval,
        connect_timeout=connect_timeout
    )


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
def tail_messages(host, port, user, password, session, sequence,
                  client_heartbeat_interval, server_heartbeat_interval, verbose):
    utils.enable_logging_tools(verbose)
    asyncio.run(
        soup.tail_soup_app(
            (host, port), user, password, session, sequence, connect_async, client_heartbeat_interval, server_heartbeat_interval
        )
    )


# Enums
# Records
class Quote(Record):
    Fields = [
        Field('instrumentId', UnsignedLong),
        Field('bidPrice', UnsignedLong),
        Field('askPrice', UnsignedLong),
        Field('bidQuantity', UnsignedLong),
        Field('askQuantity', UnsignedLong),
    ]

    instrumentId: int
    bidPrice: int
    askPrice: int
    bidQuantity: int
    askQuantity: int


# Messages
class QuoteMessage(Message, indicator=1, direction='incoming'):
    class BodyRecord(Record):
        Fields = [
            Field('timestamp', UnsignedLong),
            Field('someInfo', FixedIsoString(length=32)),
            Field('quotes', Array(Quote, UnsignedShortBE)),
        ]

    timestamp: int
    someInfo: str
    quotes: list[Quote]
"""


@pytest.fixture(scope='session')
def load_generated_sqf_code(code_loader):
    return code_loader('test_sqf', EXPECTED_GENERATED_CODE)


@pytest.fixture(scope='session')
def msg_factory(load_generated_sqf_code):
    module = load_generated_sqf_code

    def _factory(key):
        quotes = []
        for i in range(1, 2):
            quote = module.Quote()
            quote.instrumentId = i
            quote.bidPrice = i * 100
            quote.askPrice = i * 1000
            quote.bidQuantity = i * 10
            quote.askQuantity = i * 100
            quotes.append(quote)

        msg = module.QuoteMessage()
        msg.timestamp = key
        msg.someInfo = 'a' * 32
        msg.quotes = quotes
        return msg
    return _factory


async def test__sqf__soup_clientapp_codegen_tests(load_generated_sqf_code, soup_clientapp_codegen_tests):
    await soup_clientapp_codegen_tests(
        'sqf',
        'test',
        codegen.generate,
        TEST_SQF_MESSAGES,
        EXPECTED_GENERATED_CODE,
        load_generated_sqf_code,
    )


async def test__sqf__soup_clientapp_common_tests__using_generated_code(load_generated_sqf_code, msg_factory, soup_clientapp_common_tests):
    await soup_clientapp_common_tests(
        load_generated_sqf_code.connect_async,
        load_generated_sqf_code.ClientSession,
        msg_factory,
    )
