import asyncio
import logging

import attrs
import pytest
from nasdaq_protocols import soup
from nasdaq_protocols.soup._reader import SoupMessageReader
from nasdaq_protocols import common
from unittest.mock import MagicMock


logger = logging.getLogger(__name__)
input1 = soup.LoginRequest('nouser', 'nopassword', 'session', '1')
input2 = soup.LoginAccepted('session', 10)


@attrs.define(slots=False, auto_attribs=True)
class MsgHandler:
    received_messages: asyncio.Queue = attrs.field(init=False, default=attrs.Factory(asyncio.Queue))
    closed: asyncio.Event = attrs.field(init=False, default=attrs.Factory(asyncio.Event))

    async def on_msg(self, msg: soup.SoupMessage):
        await self.received_messages.put(msg)

    async def on_close(self):
        self.closed.set()


@pytest.fixture(scope='function')
def handler() -> MsgHandler:
    yield MsgHandler()


@pytest.fixture(scope='function')
async def reader(handler) -> SoupMessageReader:
    reader = SoupMessageReader('test', handler.on_msg, handler.on_close)

    # ensure queue is empty.
    with pytest.raises(asyncio.QueueEmpty):
        handler.received_messages.get_nowait()

    yield reader
    await common.stop_task(reader)


@pytest.mark.asyncio
async def test_reader_is_stoppable(reader, handler):
    assert not handler.closed.is_set()

    await common.stop_task(reader)

    assert handler.closed.is_set()


@pytest.mark.asyncio
async def test_reader_reads_one_message_per_packet(reader, handler):
    _len, bytes_ = input1.to_bytes()
    await reader.on_data(bytes_)
    _len, bytes_ = input2.to_bytes()
    await reader.on_data(bytes_)

    msg1 = await handler.received_messages.get()
    assert msg1 == input1

    msg2 = await handler.received_messages.get()
    assert msg2 == input2


@pytest.mark.asyncio
async def test_reader_reads_multiple_message_in_one_packet(reader, handler):
    _len, input1_bytes = input1.to_bytes()
    _len, input2_bytes = input2.to_bytes()
    input_ = input1_bytes + input2_bytes

    await reader.on_data(input_)

    msg1 = await handler.received_messages.get()
    assert msg1 == input1

    msg2 = await handler.received_messages.get()
    assert msg2 == input2


@pytest.mark.asyncio
async def test_reader_reads_one_message_from_multiple_packets(reader, handler):
    # Send in the bytes one by one except the last one.
    _len, bytes_ = input1.to_bytes()
    for byte_ in bytes_[:-1]:
        await reader.on_data(bytes([byte_]))
        await asyncio.sleep(0.001)
        with pytest.raises(asyncio.QueueEmpty):
            _ = handler.received_messages.get_nowait()

    # Feed in the last byte and the message is formed and dispatched.
    _len, bytes_ = input1.to_bytes()
    await reader.on_data(bytes([bytes_[-1]]))
    msg = await handler.received_messages.get()

    assert msg == input1


@pytest.mark.asyncio
@pytest.mark.parametrize('msg', [soup.LogoutRequest(), soup.EndOfSession()])
async def test_reader_invokes_close_when_end_of_session_is_detected(reader, handler, msg):
    _len, bytes_ = msg.to_bytes()
    await reader.on_data(bytes_)

    await handler.closed.wait()
    assert handler.closed.is_set()


@pytest.mark.asyncio
async def test_reader_invokes_close_when_msg_handler_throws_exception(reader, handler):
    # Cross wire reader's on_msg_coro to throw an exception
    reader.on_msg_coro = MagicMock(side_effect=KeyError('test'))
    _len, bytes_ = input1.to_bytes()
    await reader.on_data(bytes_)

    await handler.closed.wait()
    assert handler.closed.is_set()


@pytest.mark.asyncio
async def test_reader_accepts_empty_bytes(reader, handler):
    await reader.on_data(b'')
