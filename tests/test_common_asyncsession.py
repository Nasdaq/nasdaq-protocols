import asyncio
import logging
from typing import Any

import attrs
import pytest
from nasdaq_protocols import common


LOG = logging.getLogger(__name__)


@attrs.define(auto_attribs=True)
class SampleTestReader(common.Reader):
    stopped: bool = False

    async def stop(self):
        self.stopped = True

    def is_stopped(self):
        return self.stopped

    async def on_data(self, data: bytes):
        await asyncio.create_task(self.on_msg_coro(data.decode('ascii')))

    @staticmethod
    def create(session_id, on_msg, on_close):
        return SampleTestReader(session_id, on_msg, on_close)


@attrs.define(auto_attribs=True)
class SampleTestClientSession(common.AsyncSession):
    session_id: Any = attrs.field(validator=common.Validators.not_none())
    reader_factory: common.ReaderFactory = SampleTestReader.create
    received: asyncio.Queue = attrs.field(init=False, factory=asyncio.Queue)
    closed: asyncio.Event = attrs.field(init=False, factory=asyncio.Event)

    def __attrs_post_init__(self):
        self.on_msg_coro = self.received.put
        self.on_close_coro = self.on_close
        super().__attrs_post_init__()

    def send_msg(self, data: str):
        self._transport.write(data.encode('ascii'))

    async def send_heartbeat(self):
        pass

    async def on_close(self):
        self.closed.set()


@pytest.fixture(scope='function')
async def client_session(mock_server_session) -> SampleTestClientSession:
    event_loop = asyncio.get_running_loop()
    port, server_session = mock_server_session
    session_ = SampleTestClientSession(session_id=common.SessionId())
    _, session_ = await event_loop.create_connection(lambda: session_, '127.0.0.1', port=port)

    # test server-client communication works
    server_session.when(lambda x: x == b'echo').do(lambda session, _: session.send('echoed'))
    session_.send_msg('echo')
    assert await asyncio.wait_for(session_.received.get(), 1) == 'echoed'
    assert session_.is_active()

    yield session_

    assert not session_.is_active()
    assert session_.closed.is_set()
    assert session_.is_closed()
    assert session_._reader.is_stopped()
    if session_._local_hb_monitor:
        assert session_._local_hb_monitor.is_stopped()
    if session_._remote_hb_monitor:
        assert session_._remote_hb_monitor.is_stopped()
    assert session_._msg_queue.is_stopped()


async def test__asyncsession__transport_closed__session_is_closed(mock_server_session, client_session):
    _, server_session = mock_server_session

    server_session.when(lambda x: x == b'stop').do(lambda session, _: session.close())

    # informs the server to close the connection from server side.
    client_session.send_msg('stop')
    await asyncio.wait_for(client_session.closed.wait(), 1)

    # test client session is closed
    assert client_session.is_closed()


async def test__asyncsession__close__session_is_closed(mock_server_session, client_session):
    _, server_session = mock_server_session

    await client_session.close()

    await asyncio.sleep(0.1)

    assert server_session.connected is False
    assert client_session.is_closed()

    # test calling close() multiple times is safe.
    await client_session.close()


async def test__asyncsession__missed_remote_heartbeats__session_is_closed(mock_server_session, client_session):
    _, server_session = mock_server_session

    client_session.start_heartbeats(10, 0.01)
    await asyncio.sleep(0.1)

    # test client session is closed
    assert client_session.is_closed()
