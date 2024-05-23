import asyncio
import logging
import pytest

from nasdaq_protocols.common import *
from nasdaq_protocols import soup, ouch
from .mocks import *


LOG = logging.getLogger(__name__)
LOGIN_REQUEST = soup.LoginRequest('test-u', 'test-p', '', '0')
LOGIN_ACCEPTED = soup.LoginAccepted('test', 1)
LOGIN_REJECTED = soup.LoginRejected(soup.LoginRejectReason.NOT_AUTHORIZED)


async def connect_to_mock_ouch_server(mock_server_session, session_factory=None) -> ouch.OuchClientSession:
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
    class BodyRecord(Record):
        Fields = [
            Field('status', ShortBE),
        ]

    @staticmethod
    def get(status):
        msg = TestEnterOrderMsgResponse()
        msg.status = status
        return msg


async def test__connect_async__invalid_credentials__ouch_session_is_not_created(mock_server_session):
    port, server_session = mock_server_session
    server_session.when(
        matches(LOGIN_REQUEST), 'match-login-request'
    ).do(
        send(LOGIN_REJECTED), 'send-login-reject'
    )

    with pytest.raises(ConnectionRefusedError):
        await ouch.connect_async(
            ('127.0.0.1', port), 'test-u', 'test-p', '',
        )


async def test__connect_async__valid_credentials__ouch_session_is_created(mock_server_session):
    client_session = await connect_to_mock_ouch_server(mock_server_session)

    await client_session.close()
    assert client_session.closed is True


async def test__ouch_client_session__no_handlers__able_to_receive_message(mock_server_session):
    port, server_session = mock_server_session
    enter_order = TestEnterOrderMsg.get(1, 1)
    enter_order_resp = TestEnterOrderMsgResponse.get(0)
    client_session = await connect_to_mock_ouch_server(mock_server_session)
    server_session.when(
        matches(un_sequenced(enter_order)), 'match-enter-order'
    ).do(
        send(sequenced(enter_order_resp)), 'send-enter-order-response'
    )
    client_session.send_message(enter_order)

    received_msg = await client_session.receive_message()
    assert received_msg == enter_order_resp

    await client_session.close()


async def test__ouch_client_session__on_msg_coro__coro_is_called(mock_server_session):
    port, server_session = mock_server_session
    received_msgs = asyncio.Queue()
    enter_order = TestEnterOrderMsg.get(1, 1)
    enter_order_resp = TestEnterOrderMsgResponse.get(0)

    async def on_msg(msg):
        received_msgs.put_nowait(msg == enter_order_resp)

    client_session = await connect_to_mock_ouch_server(
        mock_server_session,
        lambda x: ouch.OuchClientSession(x, on_msg_coro=on_msg)
    )

    server_session.when(
        matches(un_sequenced(enter_order)), 'match-enter-order'
    ).do(
        send(sequenced(enter_order_resp)), 'send-enter-order-response'
    )
    client_session.send_message(enter_order)

    assert (await received_msgs.get()) is True

    await client_session.close()


async def test__ouch_client_session__on_msg_coro__receive_message_throws_exception(mock_server_session):
    port, server_session = mock_server_session

    async def on_msg(_msg):
        ...

    client_session = await connect_to_mock_ouch_server(
        mock_server_session,
        lambda x: ouch.OuchClientSession(x, on_msg_coro=on_msg)
    )

    with pytest.raises(StateError):
        await client_session.receive_message()

    await client_session.close()


async def test__ouch_client_session__on_close_coro__coro_is_called(mock_server_session):
    close_called = asyncio.Queue()

    async def on_close():
        close_called.put_nowait(True)

    client_session = await connect_to_mock_ouch_server(
        mock_server_session,
        lambda x: ouch.OuchClientSession(x, on_close_coro=on_close)
    )

    await client_session.close()
    assert (await close_called.get()) is True