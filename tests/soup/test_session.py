import attrs
import pytest
import logging
from unittest.mock import MagicMock

from nasdaq_protocols.soup import *
from nasdaq_protocols.common import *


logger = logging.getLogger(__name__)


@attrs.define(slots=False, auto_attribs=True)
class MockServerSession(SoupServerSession, session_type='mock_server'):
    on_login_mock: MagicMock = None
    on_unsequenced_mock: MagicMock = None

    async def on_login(self, msg: LoginRequest) -> LoginAccepted | LoginRejected:
        if self.on_login_mock:
            return self.on_login_mock(msg)

    async def on_unsequenced(self, msg: UnSequencedData) -> None:
        if self.on_unsequenced_mock:
            return self.on_unsequenced_mock(msg)


@pytest.fixture(scope='function')
async def mock_server_session(unused_tcp_port) -> MockServerSession:
    session_ = MockServerSession()
    server, serving_task = await start_server(('127.0.0.1', unused_tcp_port), lambda: session_)
    yield unused_tcp_port, session_
    await stop_task(serving_task)


@pytest.mark.asyncio
async def test_server_rejected_login(mock_server_session):
    port, server_session = mock_server_session
    server_session.on_login_mock = MagicMock(return_value=LoginRejected(LoginRejectReason.NOT_AUTHORIZED))
    with pytest.raises(ConnectionRefusedError):
        logger.info('going to connect')
        client_session = await connect_async(
            ('127.0.0.1', port),
            'test-u',
            'test-password',
            'session'
        )
        assert client_session is None

