import asyncio
import logging

import attrs
import pytest

from nasdaq_protocols import soup
from nasdaq_protocols.soup import LoginRequest, LoginAccepted, LoginRejected, UnSequencedData
from tests.mocks import matches, send

LOG = logging.getLogger(__name__)


@attrs.define(auto_attribs=True)
class SampleTestSourServerSession(soup.SoupServerSession):
    output_sent: list[soup.SoupMessage] = attrs.field(factory=list)

    async def on_login(self, msg: LoginRequest) -> LoginAccepted | LoginRejected:
        return LoginAccepted('session', 1)

    async def on_unsequenced(self, msg: UnSequencedData) -> None:
        if msg.data == b'case1':
            self.send_seq_msg(msg.data)
        else:
            self.send_seq_msg(
                soup.SequencedData(b'case2')
            )

    def send_msg(self, msg):
        self.output_sent.append(msg)


def configure_login_accept(server_session):
    server_session.when(
        matches(soup.LoginRequest('test-u', 'test-p', 'session', '1')), 'login-request-match',
    ).do(
        send(LoginAccepted('session', 1)), 'login-accepted'
    )
    return server_session


async def test__soup_session__invalid_credentials__login_rejected(mock_server_session):
    port, server_session = mock_server_session

    server_session.when(
        matches(LoginRequest('nouser', 'nopwd', 'session', '1')), 'login-request-match',
    ).do(
        send(LoginRejected(soup.LoginRejectReason.NOT_AUTHORIZED)), 'login-rejected'
    )

    with pytest.raises(ConnectionRefusedError):
        client_session = await soup.connect_async(
            ('127.0.0.1', port),
            'nouser',
            'nopwd',
            'session'
        )
        assert client_session is None


async def test__soup_session__valid_credentials__login_accepted(mock_server_session):
    port, server_session = mock_server_session
    server_session = configure_login_accept(server_session)

    client_session = await soup.connect_async(
        ('127.0.0.1', port),
        'test-u',
        'test-p',
        'session'
    )
    assert client_session is not None

    client_session.logout()


async def test__soup_session__able_to_communicate(mock_server_session):
    port, server_session = mock_server_session
    server_session = configure_login_accept(server_session)

    client_session = await soup.connect_async(
        ('127.0.0.1', port),
        'test-u',
        'test-p',
        'session'
    )
    assert client_session is not None

    for i in range(1, 10):
        server_session.when(
            matches(soup.UnSequencedData(f'hello-{i}'.encode())),
            f'sequenced-data-{i}'
        ).do(
            send(soup.SequencedData(f'hello-{i}-ack'.encode()))
        )

    for i in range(1, 10):
        test_data = f'hello-{i}'.encode()
        client_session.send_msg(soup.UnSequencedData(test_data))
        reply = await client_session.receive_msg()
        assert isinstance(reply, soup.SequencedData)
        assert reply.data == test_data + b'-ack'

    client_session.logout()


async def test__soup_session__sending_debug_from_client(mock_server_session):
    port, server_session = mock_server_session
    server_session = configure_login_accept(server_session)

    client_session = await soup.connect_async(
        ('127.0.0.1', port),
        'test-u',
        'test-p',
        'session'
    )
    assert client_session is not None
    test_data = 'sending debug msg'

    server_session.when(
        matches(soup.Debug(test_data)), 'debug-msg'
    ).do(
        send(soup.SequencedData(f'{test_data}-ack'.encode()))
    )

    client_session.send_debug(test_data)
    reply = await client_session.receive_msg()
    assert isinstance(reply, soup.SequencedData)
    assert reply.data == f'{test_data}-ack'.encode('ascii')

    client_session.logout()


async def test__soup_session__with_dispatcher__dispatcher_invoked(mock_server_session):
    port, server_session = mock_server_session
    closed = asyncio.Event()
    server_session = configure_login_accept(server_session)
    received_messages = asyncio.Queue()
    burst_chunk = 10

    async def on_msg(msg):
        await received_messages.put(msg)

    async def on_close():
        closed.set()

    # method to generate load
    def generate_load(number_of_messages):
        def action(session, _data):
            for i in range(number_of_messages):
                session.send(soup.SequencedData(f'msg-{i}'.encode('ascii')))
        return action

    client_session = await soup.connect_async(
        ('127.0.0.1', port),
        'test-u',
        'test-p',
        'session',
        on_msg_coro=on_msg,
        on_close_coro=on_close
    )
    assert client_session is not None

    # arm mocks
    server_session.when(
        matches(soup.Debug('start-burst-traffic')), 'start-burst-traffic'
    ).do(
        generate_load(burst_chunk)
    )
    server_session.when(
        matches(soup.Debug('end')), 'end'
    ).do(
        send(soup.EndOfSession())
    )

    for i in range(1, 5):
        # start burst traffic
        client_session.send_debug('start-burst-traffic')
        for _ in range(burst_chunk):
            msg = await received_messages.get()
            assert isinstance(msg, soup.SequencedData)

    # end burst traffic
    client_session.send_debug('end')
    await asyncio.wait_for(closed.wait(), 1)
    assert client_session.is_closed()


def test__soup_session__session_with_no_session_type():
    class BaseSessionType(soup.SoupSession):
        pass

    assert BaseSessionType.SessionType is 'base'


async def test__soup_session__login_message_server_session():
    server_session = SampleTestSourServerSession()
    assert server_session is not None

    await server_session.on_msg_coro(
        soup.LoginRequest('test-u', 'test-p', 'session', '1')
    )
    assert len(server_session.output_sent) == 1
    assert isinstance(server_session.output_sent[0], LoginAccepted)


async def test__soup_session__unsequenced_msg__server_session():
    server_session = SampleTestSourServerSession()

    await server_session.on_msg_coro(
        soup.UnSequencedData(b'case1')
    )
    assert len(server_session.output_sent) == 1
    assert isinstance(server_session.output_sent[0], soup.SequencedData)

    await server_session.on_msg_coro(
        soup.UnSequencedData(b'case2')
    )
    assert len(server_session.output_sent) == 2
    assert isinstance(server_session.output_sent[1], soup.SequencedData)


async def test__soup_session__send_debug():
    server_session = SampleTestSourServerSession()
    await server_session.on_msg_coro(
        soup.Debug('hello')
    )
    assert len(server_session.output_sent) == 0


async def test__soup_session__send_heartbeat():
    server_session = SampleTestSourServerSession()
    await server_session.send_heartbeat()
    assert len(server_session.output_sent) == 1
    assert isinstance(server_session.output_sent[0], soup.ServerHeartbeat)


async def test__soup_session__end_session():
    server_session = SampleTestSourServerSession()
    server_session.end_session()
    assert len(server_session.output_sent) == 1
    assert isinstance(server_session.output_sent[0], soup.EndOfSession)


async def test__soup_session__send_logout():
    server_session = SampleTestSourServerSession()
    assert not server_session.is_closed()

    await server_session.on_msg_coro(
        soup.LogoutRequest()
    )
    assert len(server_session.output_sent) == 0
    assert server_session.is_closed()