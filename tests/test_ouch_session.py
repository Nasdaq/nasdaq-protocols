import logging

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
    await client_session.close()

    assert len(received_messages) == 1
    assert received_messages[0] == un_sequenced(enter_order_1).to_bytes()[1]
