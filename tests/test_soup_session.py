import attrs
import pytest
import logging
from unittest.mock import MagicMock

from nasdaq_protocols import soup
from .mocks import mock_server_session


logger = logging.getLogger(__name__)


@attrs.define(slots=False, auto_attribs=True)
class MockServerSession(soup.SoupServerSession, session_type='mock_server'):
    on_login_mock: MagicMock = None
    on_unsequenced_mock: MagicMock = None

    async def on_login(self, msg: soup.LoginRequest) -> soup.LoginAccepted | soup.LoginRejected:
        if self.on_login_mock:
            return self.on_login_mock(msg)

    async def on_unsequenced(self, msg: soup.UnSequencedData) -> None:
        if self.on_unsequenced_mock:
            return self.on_unsequenced_mock(msg)


def match_soup_msg_type(type_):
    def match(data):
        soup_message = soup.SoupMessage.from_bytes(data)
        return isinstance(soup_message, type_)
    return match


@pytest.mark.asyncio
async def test_server_rejected_login(mock_server_session):
    port, server_session = mock_server_session

    server_session.when(match_soup_msg_type(soup.LoginRequest))\
        .do(lambda x: server_session.send(soup.LoginRejected(soup.LoginRejectReason.NOT_AUTHORIZED)))


    with pytest.raises(ConnectionRefusedError):
        logger.info('going to connect')
        client_session = await soup.connect_async(
            ('127.0.0.1', port),
            'test-u',
            'test-password',
            'session'
        )
        assert client_session is None
