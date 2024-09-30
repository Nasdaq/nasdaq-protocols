import pytest

from nasdaq_protocols.itch import codegen
from .soup_client_app_tests import soup_clientapp_common_tests
from .testdata import *


APP_NAME = 'test'
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
                        server_heartbeat_interval: int = 10) -> ClientSession:
    if session_factory is None:
        def session_factory(x):
            return ClientSession(x, on_msg_coro=on_msg_coro, on_close_coro=on_close_coro)

    return await itch.connect_async(
        remote, user, passwd, session_id, sequence,
        session_factory, on_msg_coro, on_close_coro,
        client_heartbeat_interval, server_heartbeat_interval
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


def test__no_init_file__no_prefix__code_generated(codegen_invoker):
    prefix = ''
    expected_file_name = f'itch_{APP_NAME}.py'
    generated_files = codegen_invoker(
        codegen.generate,
        TEST_XML_ITCH_MESSAGE,
        APP_NAME,
        generate_init_file=False,
        prefix=prefix
    )

    assert len(generated_files) == 1
    assert expected_file_name in generated_files
    assert generated_files[expected_file_name].strip() == EXPECTED_GENERATED_CODE.strip()


def test__init_file__no_prefix__code_generated(codegen_invoker):
    prefix = ''
    expected_file_name = f'itch_{APP_NAME}.py'
    generated_files = codegen_invoker(
        codegen.generate,
        TEST_XML_ITCH_MESSAGE,
        APP_NAME,
        generate_init_file=True,
        prefix=prefix
    )

    assert len(generated_files) == 2

    assert expected_file_name in generated_files
    assert generated_files[expected_file_name].strip() == EXPECTED_GENERATED_CODE.strip()

    assert '__init__.py' in generated_files
    assert generated_files['__init__.py'].strip() == 'from .itch_test import *'


def test__init_file__with_prefix__code_generated(codegen_invoker):
    prefix = 'test'
    expected_file_name = f'test_itch_{APP_NAME}.py'
    generated_files = codegen_invoker(
        codegen.generate,
        TEST_XML_ITCH_MESSAGE,
        APP_NAME,
        generate_init_file=True,
        prefix=prefix
    )

    assert len(generated_files) == 2

    assert expected_file_name in generated_files
    assert generated_files[expected_file_name].strip() == EXPECTED_GENERATED_CODE.strip()

    assert '__init__.py' in generated_files
    assert generated_files['__init__.py'].strip() == 'from .test_itch_test import *'


def test__load_generated_code__code_loads_without_issue(load_generated_itch_code):
    assert load_generated_itch_code is not None


def test__tools_codegen__code_generated(tools_codegen_invoker):
    package = 'test'
    app_name = 'test'
    expected_file_name = f'itch_{app_name}_tools.py'
    generated_files = tools_codegen_invoker(
        codegen.generate_itch_tools,
        app_name,
        package
    )

    assert len(generated_files) == 1
    assert expected_file_name in generated_files


async def test__connect__using_generated_code(load_generated_itch_code, soup_clientapp_common_tests):
    module = load_generated_itch_code

    def msg_factory(i):
        msg = module.TestMessage1()
        msg.field1 = i
        msg.field2 = 'a'
        msg.field3 = 'ab'
        return msg

    await soup_clientapp_common_tests(
        module.connect_async,
        module.ClientSession,
        msg_factory,
    )