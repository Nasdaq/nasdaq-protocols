import asyncio
import logging

import attrs
import pytest

from nasdaq_protocols import soup, common
from nasdaq_protocols.common import StateError
from .mocks import *


LOG = logging.getLogger(__name__)
LOGIN_REQUEST = soup.LoginRequest('test-u', 'test-p', '', '0')
LOGIN_ACCEPTED = soup.LoginAccepted('test', 1)
LOGIN_REJECTED = soup.LoginRejected(soup.LoginRejectReason.NOT_AUTHORIZED)
SOUP_TESTS = []


@attrs.define
class TestParams:
    port: int
    server_session: MockServerSession
    connector: callable
    session_factory: callable
    in_msg_factory: callable
    out_msg_factory: callable


def test_params(*args, **kwargs):
    for arg in args:
        if arg not in kwargs:
            raise ValueError(f'Argument {arg} is required')
    if len(args) == 1:
        return kwargs[args[0]]
    return [kwargs[arg] for arg in args]


def sequenced(msg: common.Serializable):
    return soup.SequencedData(msg.to_bytes()[1])


def soup_test(target):
    SOUP_TESTS.append(target)
    return target


async def connect_to_soup_server(port, server_session, connector, session_factory=None):
    server_session.when(
        matches(LOGIN_REQUEST), 'match-login-request'
    ).do(
        send(LOGIN_ACCEPTED), 'send-login-accept'
    )

    LOG.debug('connecting to server...')
    client_session = await connector(
        remote=('127.0.0.1', port),
        user='test-u',
        passwd='test-p',
        session_id='',
        session_factory=session_factory
    )
    assert client_session is not None
    LOG.debug('connected to server')
    return client_session


@soup_test
async def connect_async__invalid_credentials__session_is_not_created(params: TestParams):
    params.server_session.when(
        matches(LOGIN_REQUEST), 'match-login-request'
    ).do(
        send(LOGIN_REJECTED), 'send-login-reject'
    )

    with pytest.raises(ConnectionRefusedError):
        await params.connector(
            remote=('127.0.0.1', params.port),
            user='test-u',
            passwd='test-p',
            session_id='',
        )


@soup_test
async def connect_async__valid_credentials__session_is_created(params: TestParams):
    client_session = await connect_to_soup_server(params.port, params.server_session, params.connector)

    await client_session.close()
    assert client_session.closed is True


@soup_test
async def client_session__no_handlers__able_to_receive_message(params: TestParams):
    input_messages = [params.in_msg_factory(i) for i in range(10)]
    expected_messages = [params.out_msg_factory(i) for i in range(10)]

    client_session = await connect_to_soup_server(params.port, params.server_session, params.connector)

    for i, msg in enumerate(input_messages):
        params.server_session.send(sequenced(msg))

    for id_ in range(len(expected_messages)):
        received_msg = await client_session.receive_message()
        assert received_msg == expected_messages[id_], f'expected {expected_messages[id_]}, got {received_msg}'

    LOG.info("closing session")
    await client_session.close()


@soup_test
async def client_session__on_msg_coro__coro_is_called(params: TestParams):
    input_messages = [params.in_msg_factory(i) for i in range(1)]
    expected_messages = [params.out_msg_factory(i) for i in range(1)]
    closed = asyncio.Event()
    all_messages_received = asyncio.Event()

    async def on_msg(msg):
        assert msg == expected_messages.pop(0)
        if len(expected_messages) == 0:
            all_messages_received.set()

    async def on_close():
        closed.set()

    client_session = await connect_to_soup_server(
        params.port,
        params.server_session,
        params.connector,
        session_factory=lambda x: params.session_factory(x, on_msg_coro=on_msg, on_close_coro=on_close)
    )

    for msg in input_messages:
        params.server_session.send(sequenced(msg))

    await asyncio.wait_for(all_messages_received.wait(), 5)
    params.server_session.close()

    await asyncio.wait_for(closed.wait(), 5)
    assert client_session.closed is True


@soup_test
async def client_session__on_msg_coro__receive_message_throws_exception(params: TestParams):
    async def on_msg(_msg):
        ...

    client_session = await connect_to_soup_server(
        params.port,
        params.server_session,
        params.connector,
        session_factory=lambda x: params.session_factory(x, on_msg_coro=on_msg)
    )

    with pytest.raises(StateError):
        await client_session.receive_message()

    await client_session.close()


@soup_test
async def client_session__on_close_coro__coro_is_called(params: TestParams):
    close_called = asyncio.Queue()

    async def on_close():
        close_called.put_nowait(True)

    client_session = await connect_to_soup_server(
        params.port,
        params.server_session,
        params.connector,
        session_factory=lambda x: params.session_factory(x, on_close_coro=on_close)
    )

    await client_session.close()

    closed = await asyncio.wait_for(close_called.get(), 5)
    assert closed is True
    assert client_session.closed is True


@soup_test
async def client_session__server_closed__session_is_closed(params: TestParams):
    close_called = asyncio.Event()

    async def on_close():
        close_called.set()

    client_session = await connect_to_soup_server(
        params.port,
        params.server_session,
        params.connector,
        session_factory=lambda x: params.session_factory(x, on_close_coro=on_close)
    )

    params.server_session.close()

    closed = await asyncio.wait_for(close_called.wait(), 5)
    assert closed is True
    assert client_session.closed is True


@soup_test
async def client_session__attempting_to_double_close__session_is_closed(params: TestParams):
    close_called = asyncio.Event()
    can_complete_close = asyncio.Event()

    async def on_close():
        close_called.set()
        await can_complete_close.wait()

    client_session = await connect_to_soup_server(
        params.port,
        params.server_session,
        params.connector,
        session_factory=lambda x: params.session_factory(x, on_close_coro=on_close)
    )

    closing_task = asyncio.create_task(client_session.close())

    # make sure client is blocked in on_close
    # basically, client is in closing state
    await close_called.wait()

    # try to close again
    # this is the actual test, this should not block
    await client_session.close()

    # unblock the client and wait for the first close to finish
    can_complete_close.set()
    await closing_task

    assert client_session.closed is True

@soup_test
async def client_session__closing_an_closed_session__close_coro_is_not_called_again(params: TestParams):
    close_called = asyncio.Event()

    async def on_close():
        assert not close_called.is_set(), 'close coro called twice'
        close_called.set()

    client_session = await connect_to_soup_server(
        params.port,
        params.server_session,
        params.connector,
        session_factory=lambda x: params.session_factory(x, on_close_coro=on_close)
    )

    await client_session.close()
    assert client_session.closed is True

    await client_session.close()
    assert client_session.closed is True


@pytest.fixture(scope='function', params=SOUP_TESTS)
async def soup_clientapp_common_tests(request, mock_server_session):
    port, server_session = mock_server_session

    async def _test(connector, session_factory, msg_factory, out_msg_factory=None):
        # every test is executed here.
        await request.param(
            params=TestParams(
                port=port,
                server_session=server_session,
                connector=connector,
                session_factory=session_factory,
                in_msg_factory=msg_factory,
                out_msg_factory=out_msg_factory or msg_factory
            )
        )

    yield _test

