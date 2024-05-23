import asyncio
import logging

import attrs
import pytest
from nasdaq_protocols import soup
from nasdaq_protocols.soup._reader import SoupMessageReader
from nasdaq_protocols import common
from unittest.mock import MagicMock


LOG = logging.getLogger(__name__)
INPUT1 = soup.LoginRequest('nouser', 'nopassword', 'session', '1')
INPUT2 = soup.LoginAccepted('session', 10)


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
async def test__soup_message_reader__stop__reader_is_stopped(reader, handler):
    assert not handler.closed.is_set()

    await common.stop_task(reader)

    assert handler.closed.is_set()


@pytest.mark.asyncio
async def test__soup_message_reader__one_msg_per_packet__msg_is_read(reader, handler):
    _len, bytes_ = INPUT1.to_bytes()
    await reader.on_data(bytes_)
    _len, bytes_ = INPUT2.to_bytes()
    await reader.on_data(bytes_)

    msg1 = await handler.received_messages.get()
    assert msg1 == INPUT1

    msg2 = await handler.received_messages.get()
    assert msg2 == INPUT2


@pytest.mark.asyncio
async def test__soup_message_reader__multiple_msgs_per_packet__all_msgs_read(reader, handler):
    _len, input1_bytes = INPUT1.to_bytes()
    _len, input2_bytes = INPUT2.to_bytes()
    input_ = input1_bytes + input2_bytes

    await reader.on_data(input_)

    msg1 = await handler.received_messages.get()
    assert msg1 == INPUT1

    msg2 = await handler.received_messages.get()
    assert msg2 == INPUT2


@pytest.mark.asyncio
async def test__soup_message_reader__one_msg_in_multiple_packets__msg_is_read(reader, handler):
    # Send in the bytes one by one except the last one.
    _len, bytes_ = INPUT1.to_bytes()
    for byte_ in bytes_[:-1]:
        await reader.on_data(bytes([byte_]))
        await asyncio.sleep(0.001)
        with pytest.raises(asyncio.QueueEmpty):
            _ = handler.received_messages.get_nowait()

    # Feed in the last byte and the message is formed and dispatched.
    _len, bytes_ = INPUT1.to_bytes()
    await reader.on_data(bytes([bytes_[-1]]))
    msg = await handler.received_messages.get()

    assert msg == INPUT1


@pytest.mark.asyncio
@pytest.mark.parametrize('msg', [soup.LogoutRequest(), soup.EndOfSession()])
async def test__soup_message_reader__end_of_session__reader_is_stopped(reader, handler, msg):
    _len, bytes_ = msg.to_bytes()
    await reader.on_data(bytes_)

    await handler.closed.wait()
    assert handler.closed.is_set()


@pytest.mark.asyncio
async def test__soup_message_reader__handler_raises_exception__reader_is_stopped(reader, handler):
    # Cross wire reader's on_msg_coro to throw an exception
    reader.on_msg_coro = MagicMock(side_effect=KeyError('test'))
    _len, bytes_ = INPUT1.to_bytes()
    await reader.on_data(bytes_)

    await handler.closed.wait()
    assert handler.closed.is_set()


@pytest.mark.asyncio
async def test__soup_message_reader__empty_data__no_effect(reader, handler):
    await reader.on_data(b'')
