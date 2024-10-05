import asyncio

import pytest

from nasdaq_protocols import common
from nasdaq_protocols import soup
from nasdaq_protocols.soup import LoginRequest, LoginAccepted, LoginRejected


class SoupServerTestSession(soup.SoupServerSession, session_type='server'):
    async def on_login(self, msg: LoginRequest) -> LoginAccepted | LoginRejected:
        if msg.user == 'test-u' and msg.password == 'test-p':
            return LoginAccepted('session', int(msg.sequence))
        else:
            return LoginRejected(soup.LoginRejectReason.NOT_AUTHORIZED)

    async def on_debug(self, msg: soup.Debug) -> None:
        self.send_msg(soup.SequencedData(f'{msg.msg}-ack'.encode('ascii')))

    async def on_unsequenced(self, msg: soup.UnSequencedData):
        reply = msg.data.decode('ascii') + '-ack'
        self.send_msg(soup.SequencedData(reply.encode('ascii')))

    def generate_load(self, number_of_messages):
        for i in range(number_of_messages):
            self.send_msg(soup.SequencedData(f'msg-{i}'.encode('ascii')))
        self.send_msg(soup.UnSequencedData('end'.encode('ascii')))


@pytest.fixture(scope='function')
async def soup_server_session(unused_tcp_port):
    session = SoupServerTestSession()
    server, serving_task = await common.start_server(('127.0.0.1', unused_tcp_port), lambda: session)
    yield unused_tcp_port, session

    retry = 0
    while not session.is_closed() and retry < 5:
        await asyncio.sleep(0.001)

    assert session.is_closed()

    await common.stop_task(serving_task)


@pytest.mark.asyncio
async def test__soup_session__invalid_credentials__login_rejected(soup_server_session):
    port, server_session = soup_server_session

    with pytest.raises(ConnectionRefusedError):
        client_session = await soup.connect_async(
            ('', port),
            'nouser',
            'nopwd',
            'session'
        )
        assert client_session is None


@pytest.mark.asyncio
async def test__soup_session__valid_credentials__login_accepted(soup_server_session):
    port, server_session = soup_server_session

    client_session = await soup.connect_async(
        ('', port),
        'test-u',
        'test-p',
        'session'
    )
    assert client_session is not None

    client_session.logout()


@pytest.mark.asyncio
async def test__soup_session__able_to_communicate(soup_server_session):
    port, server_session = soup_server_session

    client_session = await soup.connect_async(
        ('', port),
        'test-u',
        'test-p',
        'session'
    )
    assert client_session is not None

    for i in range(1, 10):
        test_data = f'hello-{i}'.encode()
        client_session.send_msg(soup.UnSequencedData(test_data))
        reply = await client_session.receive_msg()
        assert isinstance(reply, soup.SequencedData)
        assert reply.data == test_data + b'-ack'

    client_session.logout()


@pytest.mark.asyncio
async def test__soup_session__sending_debug_from_client(soup_server_session):
    port, server_session = soup_server_session

    client_session = await soup.connect_async(
        ('', port),
        'test-u',
        'test-p',
        'session'
    )
    assert client_session is not None

    test_data = 'sending debug msg'
    client_session.send_debug(test_data)
    reply = await client_session.receive_msg()
    assert isinstance(reply, soup.SequencedData)
    assert reply.data == f'{test_data}-ack'.encode('ascii')

    client_session.logout()


@pytest.mark.asyncio
async def test__soup_session__with_dispatcher__dispatcher_invoked(soup_server_session):
    port, server_session = soup_server_session

    closed = asyncio.Event()

    async def on_msg(msg):
        if msg.data == b'end':
            server_session.end_session()

    async def on_close():
        closed.set()

    client_session = await soup.connect_async(
        ('', port),
        'test-u',
        'test-p',
        'session',
        on_msg_coro=on_msg,
        on_close_coro=on_close
    )
    assert client_session is not None

    server_session.generate_load(100)

    await asyncio.wait_for(closed.wait(), 1)


def test__soup_session__session_with_no_session_type():
    class BaseSessionType(soup.SoupSession):
        pass

    assert BaseSessionType.SessionType is 'base'
