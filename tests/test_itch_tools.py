import asyncio
import pytest

from nasdaq_protocols import soup
from nasdaq_protocols.common import stop_task
from nasdaq_protocols.itch import codegen
from nasdaq_protocols.itch.tools import tail_itch
from nasdaq_protocols.soup import LoginRejectReason
from .testdata import *
from .mocks import *


APP_NAME = 'test_itch_tools'
LOGIN_REQUEST = soup.LoginRequest('test-u', 'test-p', '', '1')
LOGIN_REJECTED = soup.LoginRejected(LoginRejectReason.NOT_AUTHORIZED)
LOGIN_ACCEPTED = soup.LoginAccepted('test', 1)
LOGOUT_REQUEST = soup.EndOfSession()


@pytest.fixture(scope='function')
def load_itch_definitions(code_loader, codegen_invoker):
    def generator(app_name):
        generated_file_name = f'itch_{app_name}.py'
        generated_files = codegen_invoker(
            codegen.generate,
            TEST_XML_ITCH_MESSAGE,
            app_name,
            generate_init_file=False,
            prefix=''
        )

        module_ = code_loader(app_name, generated_files[generated_file_name])
        assert module_ is not None
        return module_
    yield generator


@pytest.fixture(scope='function')
def load_itch_tools(code_loader, load_itch_definitions, tools_codegen_invoker):
    def generator(app_name):
        definitions = load_itch_definitions(app_name)
        generated_file_name = f'itch_{app_name}_tools.py'
        generated_files = tools_codegen_invoker(
            codegen.generate_itch_tools,
            app_name,
            app_name
        )

        tools = code_loader(f'{app_name}_tools', generated_files[generated_file_name])
        assert tools is not None
        return definitions, tools,
    yield generator


def get_message_feed(module):
    message1 = module.TestMessage1()
    message1.field1 = 1
    message1.field2 = '2'
    message1.field3 = '3'

    message2 = module.TestMessage2()
    message2.field1_1 = 4
    message2.field2_1 = '5'
    message2.field3_1 = '6'
    return [message1, message2]


async def test__itch_tools__tail_itch(mock_server_session, load_itch_tools):
    definitions, tools = load_itch_tools('test__itch_tools__tail_itch')
    message_feed = get_message_feed(definitions)
    port, server_session = mock_server_session

    # setup login
    session = server_session.when(
        matches(LOGIN_REQUEST), 'match-login-request'
    ).do(
        send(LOGIN_ACCEPTED), 'send-login-accept'
    )
    # send itch feeds
    for msg in message_feed:
        session.do(
            send(soup.SequencedData(msg.to_bytes()[1])), 'send-test-message'
        )

    # start tailing
    tailer = asyncio.create_task(tail_itch(
        ('127.0.0.1', port), 'test-u', 'test-p', '', 1,
        definitions.connect_async, 10, 10
    ))
    assert not tailer.done()

    # give some time for tail
    await asyncio.sleep(1)
    assert not tailer.done()

    # logout
    server_session.send(LOGOUT_REQUEST)

    # wait for tailer to finish
    await asyncio.wait_for(tailer, timeout=5)
    assert tailer.done()


async def test__itch_tools__tail_itch__login_failed(mock_server_session, load_itch_tools):
    definitions, tools = load_itch_tools('test__itch_tools__tail_itch__login_failed')
    port, server_session = mock_server_session

    # setup login
    server_session.when(
        matches(LOGIN_REQUEST), 'match-login-request'
    ).do(
        send(LOGIN_REJECTED), 'send-login-reject'
    )

    # start tailing
    tailer = asyncio.create_task(tail_itch(
        ('127.0.0.1', port), 'test-u', 'test-p', '', 1,
        definitions.connect_async, 10, 10
    ))
    # give some time for tail
    await asyncio.sleep(1)
    assert tailer.done()


async def test__itch_tools__tail_itch__wrong_server(load_itch_tools):
    definitions, tools = load_itch_tools('test__itch_tools__tail_itch__wrong_server')

    # start tailing
    tailer = asyncio.create_task(tail_itch(
        ('no.such.host', 15000), 'test-u', 'test-p', '', 1,
        definitions.connect_async, 10, 10
    ))
    # give some time for tail
    await asyncio.sleep(1)
    assert tailer.done()


@pytest.mark.xfail(reason='https://github.com/Nasdaq/nasdaq-protocols/issues/21')
async def test__itch_tools__tail_itch__ctrl_c(mock_server_session, load_itch_tools):
    definitions, tools = load_itch_tools('test__itch_tools__tail_itch__ctrl_c')
    port, server_session = mock_server_session

    # setup login
    session = server_session.when(
        matches(LOGIN_REQUEST), 'match-login-request'
    ).do(
        send(LOGIN_ACCEPTED), 'send-login-accept'
    )

    # start tailing
    tailer = asyncio.create_task(tail_itch(
        ('127.0.0.1', port), 'test-u', 'test-p', '', 1,
        definitions.connect_async, 10, 10
    ))
    # give some time for tail
    await asyncio.sleep(1)
    assert not tailer.done()

    await stop_task(tailer)
    assert tailer.done()

