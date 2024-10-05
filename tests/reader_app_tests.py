import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import attrs
import pytest

from nasdaq_protocols import common


LOG = logging.getLogger(__name__)
READER_TESTS = []


@attrs.define(slots=False, auto_attribs=True)
class MsgHandler:
    received_messages: asyncio.Queue = attrs.field(init=False, default=attrs.Factory(asyncio.Queue))
    closed: asyncio.Event = attrs.field(init=False, default=attrs.Factory(asyncio.Event))

    async def on_msg(self, msg: Any):
        await self.received_messages.put(msg)

    async def on_close(self):
        self.closed.set()


@pytest.fixture(scope='function')
def handler() -> MsgHandler:
    yield MsgHandler()


def reader_test(target):
    READER_TESTS.append(target)
    return target


def tst_params(*args, **kwargs):
    for arg in args:
        if arg not in kwargs:
            raise ValueError(f'Argument {arg} is required')
    if len(args) == 1:
        return kwargs[args[0]]
    return [kwargs[arg] for arg in args]


def all_test_params(**kwargs):
    return tst_params('handler', 'reader', 'input_factory', 'output_factory', **kwargs)


@reader_test
async def reader__stop__reader_is_stopped(**kwargs):
    handler, reader = tst_params('handler', 'reader', **kwargs)

    assert not handler.closed.is_set()

    await common.stop_task(reader)

    assert handler.closed.is_set()


@reader_test
async def reader__one_msg_per_packet__msg_is_read(**kwargs):
    handler, reader, input_factory, output_factory = all_test_params(**kwargs)

    bytes_ = input_factory(1)
    await reader.on_data(bytes_)

    bytes_ = input_factory(2)
    await reader.on_data(bytes_)

    msg1 = await handler.received_messages.get()
    assert msg1 == output_factory(1), f'{msg1} != {output_factory(1)}'

    msg2 = await handler.received_messages.get()
    assert msg2 == output_factory(2), f'{msg2} != {output_factory(2)}'


@reader_test
async def _reader__multiple_msgs_per_packet__all_msgs_read(**kwargs):
    handler, reader, input_factory, output_factory = all_test_params(**kwargs)

    input_ = input_factory(1) + input_factory(2)
    await reader.on_data(input_)

    msg1 = await handler.received_messages.get()
    assert msg1 == output_factory(1)

    msg2 = await handler.received_messages.get()
    assert msg2 == output_factory(2)


@reader_test
async def reader__one_msg_in_multiple_packets__msg_is_read(**kwargs):
    handler, reader, input_factory, output_factory = all_test_params(**kwargs)

    bytes_ = input_factory(1)
    # Send in the bytes one by one except the last one.
    for byte_ in bytes_[:-1]:
        await reader.on_data(bytes([byte_]))
        await asyncio.sleep(0.001)
        with pytest.raises(asyncio.QueueEmpty):
            _ = handler.received_messages.get_nowait()

    # Feed in the last byte and the message is formed and dispatched.
    bytes_ = input_factory(1)
    await reader.on_data(bytes([bytes_[-1]]))
    msg = await handler.received_messages.get()

    assert msg == output_factory(1)


@reader_test
async def reader__end_of_session__reader_is_stopped(**kwargs):
    handler, reader, input_factory, output_factory = all_test_params(**kwargs)

    bytes_ = input_factory(0)
    await reader.on_data(bytes_)

    await handler.closed.wait()
    assert handler.closed.is_set()


@reader_test
async def reader__handler_raises_exception__reader_is_stopped(**kwargs):
    handler, reader, input_factory, output_factory = all_test_params(**kwargs)

    # Cross wire reader's on_msg_coro to throw an exception
    reader.on_msg_coro = MagicMock(side_effect=KeyError('test'))
    bytes_ = input_factory(1)
    await reader.on_data(bytes_)

    await handler.closed.wait()
    assert handler.closed.is_set()


@reader_test
async def reader__empty_data__no_effect(**kwargs):
    handler, reader, input_factory, output_factory = all_test_params(**kwargs)
    await reader.on_data(b'')


@pytest.fixture(scope='function', params=READER_TESTS)
async def reader_clientapp_common_tests(request, handler):
    async def _test(reader_factory, input_factory, output_factory):
        reader = reader_factory('test', handler.on_msg, handler.on_close)
        await request.param(
            handler=handler,
            reader=reader,
            input_factory=input_factory,
            output_factory=output_factory
        )

    yield _test
