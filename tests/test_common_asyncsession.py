import asyncio
import logging
import socket
from typing import Any

import attrs
import pytest
from nasdaq_protocols import common
from nasdaq_protocols.common import StateError

LOG = logging.getLogger(__name__)


@attrs.define(auto_attribs=True)
class SampleTestReader(common.Reader):
    separator: bytes = attrs.field(kw_only=True, default=None)

    def deserialize(self) -> Any:
        idx, sep_len = len(self._buffer), len(self.separator) if self.separator else 0
        if self.separator:
            idx = self._buffer.find(self.separator)
            if idx == -1:
                return None, False, False

        result = self._buffer[:idx].decode('ascii')
        self._buffer = self._buffer[idx + sep_len:]
        return result, False, False

    @staticmethod
    def create(session_id, on_msg, on_close):
        return SampleTestReader(session_id, on_msg, on_close)

    @staticmethod
    def creator(separator: bytes):
        def _creator(session_id, on_msg, on_close):
            return SampleTestReader(session_id, on_msg, on_close, separator=separator)
        return _creator


@attrs.define(auto_attribs=True)
class SampleTestClientSession(common.AsyncSession):
    session_id: Any = attrs.field(validator=common.Validators.not_none())
    reader_factory: common.ReaderFactory = SampleTestReader.create
    received: asyncio.Queue = attrs.field(init=False, factory=asyncio.Queue)
    closed: asyncio.Event = attrs.field(init=False, factory=asyncio.Event)
    slow_client: bool = attrs.field(kw_only=True, default=False)

    def __attrs_post_init__(self):
        self.on_msg_coro = self.slow_on_msg if self.slow_client else self.received.put
        self.on_close_coro = self.on_close
        super().__attrs_post_init__()

    def send_msg(self, data: str):
        self._transport.write(data.encode('ascii'))

    async def slow_on_msg(self, msg):
        await self.received.put(msg)
        await asyncio.sleep(0.01)

    async def send_heartbeat(self):
        pass

    async def on_close(self):
        LOG.warning("Session %s closed", self.session_id)
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


async def test__asyncsession__set_handlers_duplicate_handlers__raises_exception(mock_server_session, client_session):
    _, server_session = mock_server_session

    server_session.when(lambda x: x == b'stop').do(lambda session, _: session.close())

    with pytest.raises(StateError):
        q = asyncio.Queue()
        client_session.set_handlers(on_msg_coro=q.put)

    # informs the server to close the connection from server side.
    client_session.send_msg('stop')
    await asyncio.wait_for(client_session.closed.wait(), 1)

    # test client session is closed
    assert client_session.is_closed()

    with pytest.raises(StateError):
        # test setting handlers on closed session raises exception
        client_session.set_handlers(on_close_coro=client_session.on_close)


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


async def test__asyncsession__stream_after_connect_and_close__client_session_able_to_read_all_messages(mock_server_session):
    event_loop = asyncio.get_running_loop()
    port, server_session = mock_server_session

    # server sends 100000 messages after connection and then closes the session
    def stream_messages_and_close(session, _):
        for i in range(100000):
            session.send(f'msg{i}|'.encode('ascii'))
        session.send(f'end-of-stream'.encode('ascii'))
        session.close()
    server_session.when_connect().do(stream_messages_and_close)

    session_ = SampleTestClientSession(session_id=common.SessionId())
    _, session_ = await event_loop.create_connection(lambda: session_, '127.0.0.1', port=port)

    found_end_of_stream = False
    while not session_.closed.is_set() and not found_end_of_stream:
        msg = await asyncio.wait_for(session_.received.get(), 0.1)
        if 'end-of-stream' in msg:
            found_end_of_stream = True

    await session_.closed.wait()

    assert found_end_of_stream
    assert session_.closed.is_set()
    assert session_.is_closed()


@pytest.mark.parametrize('graceful_shutdown', [False, True])
@pytest.mark.parametrize('num_messages', [1, 10, 100])
@pytest.mark.parametrize('slow_client', [False, True])
async def test__asyncsession__graceful_shutdown__enables_client_to_read_all_messages(mock_server_session, graceful_shutdown, num_messages, slow_client):
    event_loop = asyncio.get_running_loop()
    port, server_session = mock_server_session

    # server sends n messages after connection and then closes the session
    server_session.when_connect().do(get_streamer_close_function(num_messages))

    session_ = SampleTestClientSession(
        session_id=common.SessionId(),
        reader_factory=SampleTestReader.creator(separator=b'|'),
        graceful_shutdown=graceful_shutdown,
        slow_client=slow_client
    )

    _1, _2 = await event_loop.create_connection(
        lambda: session_, '127.0.0.1', port=port
    )

    found_end_of_stream = False
    while not found_end_of_stream:
        try:
            msg = await asyncio.wait_for(session_.received.get(), 0.1)
            if 'end-of-stream' == msg:
                found_end_of_stream = True
        except asyncio.TimeoutError:
            if session_.closed.is_set():
                break
        except Exception:
            break

    task_id = asyncio.current_task().get_name()
    LOG.info('Waiting for session to close, from task %s', task_id)
    await session_.closed.wait()
    LOG.info('Session closed')

    assert session_.closed.is_set()
    assert session_.is_closed()

    assert found_end_of_stream == graceful_shutdown, \
        "Graceful shutdown should allow reading all messages"


def get_streamer_close_function(message_count: int):
    def stream_messages_and_close(session, _):
        for i in range(message_count):
            session.send(f'msg{i}|'.encode('ascii'))
        session.send(f'end-of-stream|'.encode('ascii'))
        session.close()
    return stream_messages_and_close