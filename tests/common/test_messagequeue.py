import asyncio

import pytest
from nasdaq_protocols.common import DispatchableMessageQueue


@pytest.fixture(scope='function')
async def receiver() -> asyncio.Queue:
    return asyncio.Queue()


@pytest.mark.asyncio
async def test_able_to_put_get_without_active_dispatcher():
    q = DispatchableMessageQueue(session_id='test')
    await q.put('test')

    assert await q.get() == 'test'


@pytest.mark.asyncio
async def test_able_to_put_get_nowait_without_active_dispatcher():
    q = DispatchableMessageQueue(session_id='test')
    q.put_nowait('test')

    assert q.get_nowait() == 'test'


@pytest.mark.asyncio
async def test_get_nowait_on_empty_queue_returns_none():
    q = DispatchableMessageQueue(session_id='test')
    assert q.get_nowait() is None


@pytest.mark.asyncio
async def test_able_to_put_get_with_active_dispatcher(receiver: asyncio.Queue):
    q = DispatchableMessageQueue(session_id='test', on_msg_coro=receiver.put)
    await q.put('test')

    assert await receiver.get() == 'test'

    await q.stop()


@pytest.mark.asyncio
async def test_unable_get_with_active_dispatcher(receiver: asyncio.Queue):
    q = DispatchableMessageQueue(session_id='test', on_msg_coro=receiver.put)
    await q.put('test')

    with pytest.raises(DispatchableMessageQueue.StateError):
        await q.get()

    await q.stop()


@pytest.mark.asyncio
async def test_unable_to_get_nowait_with_active_dispatcher(receiver: asyncio.Queue):
    q = DispatchableMessageQueue(session_id='test', on_msg_coro=receiver.put)
    q.put_nowait('test')

    with pytest.raises(DispatchableMessageQueue.StateError):
        q.get_nowait()

    await q.stop()


@pytest.mark.asyncio
async def test_blocking_read_when_queue_is_empty(receiver: asyncio.Queue):
    q = DispatchableMessageQueue(session_id='test')

    read_task = asyncio.create_task(q.get())
    await asyncio.sleep(0.1)
    await q.put('test')

    assert await read_task == 'test'


@pytest.mark.asyncio
async def test_stopping_queue_with_pending_blocking_read(receiver: asyncio.Queue):
    q = DispatchableMessageQueue(session_id='test')

    read_task = asyncio.create_task(q.get())
    await asyncio.sleep(0.1)
    await q.stop()

    with pytest.raises(DispatchableMessageQueue.EndOfQueue):
        await read_task


@pytest.mark.asyncio
async def test_queue_continues_processing_if_handler_throws_exception(receiver: asyncio.Queue):
    async def on_msg(msg):
        if msg == 'exception':
            raise RuntimeError('exception')
        receiver.put_nowait(msg)

    q = DispatchableMessageQueue(session_id='test', on_msg_coro=on_msg)
    put_task1 = asyncio.create_task(q.put('test1'))
    put_task2 = asyncio.create_task(q.put('exception'))
    put_task3 = asyncio.create_task(q.put('test2'))
    await asyncio.wait([put_task1, put_task2, put_task3])

    assert receiver.get_nowait() == 'test1'
    assert receiver.get_nowait() == 'test2'
    await q.stop()


@pytest.mark.asyncio
async def test_get_on_stopped_queue_raises_exception():
    q = DispatchableMessageQueue(session_id='test')
    await q.stop()

    with pytest.raises(DispatchableMessageQueue.EndOfQueue):
        await q.get()


@pytest.mark.asyncio
async def test_get_nowait_on_stopped_queue_raises_exception():
    q = DispatchableMessageQueue(session_id='test')
    await q.stop()

    with pytest.raises(DispatchableMessageQueue.EndOfQueue):
        q.get_nowait()


@pytest.mark.asyncio
async def test_unable_to_pause_a_queue_without_dispatcher():
    q = DispatchableMessageQueue(session_id='test')

    with pytest.raises(DispatchableMessageQueue.StateError):
        async with q.pause_dispatching():
            pass


@pytest.mark.asyncio
async def test_able_to_pause_a_queue_with_dispatcher(receiver: asyncio.Queue):
    q = DispatchableMessageQueue(session_id='test', on_msg_coro=receiver.put)

    async with q.pause_dispatching():
        await q.put('test')
        assert await q.get() == 'test'

    await q.stop()