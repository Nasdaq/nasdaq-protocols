import asyncio
import logging

import pytest

from nasdaq_protocols.common import *
from nasdaq_protocols import soup, ouch
from .mocks import *
from .soup_client_app_tests import soup_clientapp_common_tests


LOG = logging.getLogger(__name__)
LOGIN_REQUEST = soup.LoginRequest('test-u', 'test-p', '', '0')
LOGIN_ACCEPTED = soup.LoginAccepted('test', 1)
LOGIN_REJECTED = soup.LoginRejected(soup.LoginRejectReason.NOT_AUTHORIZED)


async def connect_to_mock_ouch_server(mock_server_session, session_factory=None) -> ouch.ClientSession:
    port, server_session = mock_server_session

    server_session.when(
        matches(LOGIN_REQUEST), 'match-login-request'
    ).do(
        send(LOGIN_ACCEPTED), 'send-login-accept'
    )

    LOG.debug('connecting to server...')
    client_session = await ouch.connect_async(
        ('127.0.0.1', port), 'test-u', 'test-p', '',
        session_factory=session_factory
    )
    assert client_session is not None
    LOG.debug('connected to server')
    return client_session


def un_sequenced(msg: Serializable):
    return soup.UnSequencedData(msg.to_bytes()[1])


def sequenced(msg: Serializable):
    return soup.SequencedData(msg.to_bytes()[1])


class TestEnterOrderMsg(ouch.Message, indicator=1, direction='incoming'):
    __test__ = False
    class BodyRecord(Record):
        Fields = [
            Field('orderToken', LongBE),
            Field('orderBookId', IntBE),
        ]

    @staticmethod
    def get(token: int, book: int):
        msg = TestEnterOrderMsg()
        msg.orderToken = token
        msg.orderBookId = book
        return msg


class TestEnterOrderMsgResponse(ouch.Message, indicator=2, direction='outgoing'):
    __test__ = False
    class BodyRecord(Record):
        Fields = [
            Field('status', ShortBE),
        ]

    @staticmethod
    def get(status):
        msg = TestEnterOrderMsgResponse()
        msg.status = status
        return msg


async def test__soup_clientapp_common_tests__all_basic_tests_pass(soup_clientapp_common_tests):
    await soup_clientapp_common_tests(
        ouch.connect_async,
        ouch.ClientSession,
        lambda x: TestEnterOrderMsgResponse.get(x)
    )


async def test__send_message__session_sends_message_to_server(mock_server_session):
    port, server_session = mock_server_session
    enter_order_1 = TestEnterOrderMsg.get(1, 1)
    received_messages = []

    server_session.when(
        matches(un_sequenced(enter_order_1)), 'match-enter-order-1'
    ).do(
        lambda _1, data: received_messages.append(data)
    )

    client_session = await connect_to_mock_ouch_server(mock_server_session)
    client_session.send_message(enter_order_1)
    for _ in range(100):
        if received_messages:
            break
        await asyncio.sleep(0.01)
    await client_session.close()

    assert len(received_messages) == 1
    assert received_messages[0] == un_sequenced(enter_order_1).to_bytes()[1]


async def test__close__logout_request_sent_to_server(mock_server_session):
    _, server_session = mock_server_session
    logout_received = asyncio.Event()
    server_session.when(matches(soup.LogoutRequest()), 'match-logout').do(lambda _1, _2: logout_received.set())

    client_session = await connect_to_mock_ouch_server(mock_server_session)
    await client_session.close()

    await asyncio.wait_for(logout_received.wait(), 1)
    assert client_session.closed is True


async def test__server_closes__slow_handler__all_sent_messages_delivered(mock_server_session):
    _, server_session = mock_server_session
    num_messages = 20
    received = []
    closed = asyncio.Event()

    async def slow_on_msg(msg):
        await asyncio.sleep(0.01)
        received.append(msg.status)

    async def on_close():
        closed.set()

    client_session = await connect_to_mock_ouch_server(
        mock_server_session,
        session_factory=lambda x: ouch.ClientSession(x, on_msg_coro=slow_on_msg, on_close_coro=on_close)
    )
    for i in range(num_messages):
        server_session.send(sequenced(TestEnterOrderMsgResponse.get(i)))
    server_session.close()

    await asyncio.wait_for(closed.wait(), 5)
    assert received == list(range(num_messages))
    assert client_session.closed is True


async def test__aliases_and_context_manager__work_like_originals(mock_server_session):
    _, server_session = mock_server_session
    enter_order = TestEnterOrderMsg.get(1, 1)
    server_session.when(
        matches(un_sequenced(enter_order)), 'match-enter-order'
    ).do(
        send(sequenced(TestEnterOrderMsgResponse.get(7)))
    )

    async with await connect_to_mock_ouch_server(mock_server_session) as client_session:
        client_session.send_msg(enter_order)
        reply = await asyncio.wait_for(client_session.receive_msg(), 1)
        assert reply.status == 7

    assert client_session.closed is True


def test__client_session__internal_state__not_a_constructor_argument():
    with pytest.raises(TypeError):
        ouch.ClientSession(None, None, None, True)
