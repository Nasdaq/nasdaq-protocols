import pytest

from nasdaq_protocols.itch import codegen
from .soup_app_codegen_tests import soup_clientapp_codegen_tests
from .soup_client_app_tests import soup_clientapp_common_tests
from .testdata import *


EXPECTED_GENERATED_CODE = """
from enum import Enum
from typing import Callable, Awaitable, Type

from nasdaq_protocols.common import logable
from nasdaq_protocols.common.message import *
from nasdaq_protocols import soup, itch


__all__ = [
    'Message',
    'ClientSession',
    'connect_async',
    'TestMessage1',
    'TestMessage2',
]


@logable
class Message(itch.Message, app_name='test'):
    def __init_subclass__(cls, **kwargs):
        cls.log.debug('subclassing %s, params = %s', cls.__name__, str(kwargs))
        if 'indicator' not in kwargs:
            raise ValueError('expected "indicator" when subclassing test.Message')

        kwargs['app_name'] = 'test'
        super().__init_subclass__(**kwargs)


class ClientSession(itch.ClientSession):
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

    return await itch.connect_async(
        remote, user, passwd, session_id, sequence,
        session_factory, on_msg_coro, on_close_coro,
        client_heartbeat_interval, server_heartbeat_interval,
        connect_timeout=connect_timeout
    )


# Enums
# Records
# Messages
class TestMessage1(Message, indicator=1, direction='outgoing'):
    class BodyRecord(Record):
        Fields = [
            Field('field1', LongBE),
            Field('field2', CharIso8599),
            Field('field3', FixedIsoString(length=16)),
        ]

    field1: int
    field2: str
    field3: str


class TestMessage2(Message, indicator=2, direction='outgoing'):
    class BodyRecord(Record):
        Fields = [
            Field('field1_1', LongBE),
            Field('field2_1', CharIso8599),
            Field('field3_1', FixedIsoString(length=16)),
        ]

    field1_1: int
    field2_1: str
    field3_1: str
"""


@pytest.fixture(scope='session')
def load_generated_itch_code(code_loader):
    # other test cases will verify if the expected_generated_code
    # is valid or not.
    module = code_loader('test_itch', EXPECTED_GENERATED_CODE)
    yield module


@pytest.fixture(scope='session')
def msg_factory(load_generated_itch_code):
    module = load_generated_itch_code

    def _factory(i):
        msg = module.TestMessage1()
        msg.field1 = i
        msg.field2 = 'a'
        msg.field3 = 'ab'
        return msg
    yield _factory


async def test__itch__soup_clientapp_codegen_tests(load_generated_itch_code, soup_clientapp_codegen_tests):
    await soup_clientapp_codegen_tests(
        'itch',
        'test',
        codegen.generate,
        TEST_XML_ITCH_MESSAGE,
        EXPECTED_GENERATED_CODE,
        load_generated_itch_code,
    )


async def test__itch__soup_clientapp_common_tests__using_generated_code(load_generated_itch_code, msg_factory, soup_clientapp_common_tests):
    await soup_clientapp_common_tests(
        load_generated_itch_code.connect_async,
        load_generated_itch_code.ClientSession,
        msg_factory,
    )
