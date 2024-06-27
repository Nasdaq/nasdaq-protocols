import asyncio

import pytest
from nasdaq_protocols import common


@pytest.fixture(scope='function')
async def receiver() -> asyncio.Queue:
    return asyncio.Queue()


@pytest.mark.asyncio
async def test__dispatchablemessagequeue__no_active_dispatcher__able_to_put_and_get():
    q = common.DispatchableMessageQueue(session_id='test')
    await q.put('test')

    assert await q.get() == 'test'


@pytest.mark.asyncio
async def test__dispatchablemessagequeue__no_active_dispatcher__able_to_put_and_get__nowait():
    q = common.DispatchableMessageQueue(session_id='test')
    q.put_nowait('test')

    assert q.get_nowait() == 'test'


@pytest.mark.asyncio
async def test__dispatchablemessagequeue__when_queue_is_empty__get_nowait_returns_none():
    q = common.DispatchableMessageQueue(session_id='test')
    assert q.get_nowait() is None


@pytest.mark.asyncio
async def test__dispatchablemessagequeue__active_dispatcher__item_is_dispatched(receiver: asyncio.Queue):
    q = common.DispatchableMessageQueue(session_id='test', on_msg_coro=receiver.put)
    await q.put('test')

    assert await receiver.get() == 'test'

    await q.stop()


@pytest.mark.asyncio
async def test__dispatchablemessagequeue__active_dispatcher__get_raises_exception(receiver: asyncio.Queue):
    q = common.DispatchableMessageQueue(session_id='test', on_msg_coro=receiver.put)
    await q.put('test')

    with pytest.raises(common.StateError):
        await q.get()

    await q.stop()


@pytest.mark.asyncio
async def test__dispatchablemessagequeue__active_dispatcher__get_raises_exception__nowait(receiver: asyncio.Queue):
    q = common.DispatchableMessageQueue(session_id='test', on_msg_coro=receiver.put)
    q.put_nowait('test')

    with pytest.raises(common.StateError):
        q.get_nowait()

    await q.stop()


@pytest.mark.asyncio
async def test__dispatchablemessagequeue__empty_queue__get_blocks_until_item_available(receiver: asyncio.Queue):
    q = common.DispatchableMessageQueue(session_id='test')

    read_task = asyncio.create_task(q.get())
    await asyncio.sleep(0.1)
    await q.put('test')

    assert await read_task == 'test'


@pytest.mark.asyncio
async def test__dispatchablemessagequeue__stop_queue_while_read_blocking__queue_stopped(receiver: asyncio.Queue):
    q = common.DispatchableMessageQueue(session_id='test')

    read_task = asyncio.create_task(q.get())
    await asyncio.sleep(0.1)
    await q.stop()

    with pytest.raises(common.EndOfQueue):
        await read_task


@pytest.mark.asyncio
async def test__dispatchablemessagequeue__dispatcher_raises_exception__queue_continues(receiver: asyncio.Queue):
    async def on_msg(msg):
        if msg == 'exception':
            raise RuntimeError('exception')
        receiver.put_nowait(msg)

    q = common.DispatchableMessageQueue(session_id='test', on_msg_coro=on_msg)
    put_task1 = asyncio.create_task(q.put('test1'))
    put_task2 = asyncio.create_task(q.put('exception'))
    put_task3 = asyncio.create_task(q.put('test2'))
    await asyncio.wait([put_task1, put_task2, put_task3])

    assert receiver.get_nowait() == 'test1'
    assert receiver.get_nowait() == 'test2'
    await q.stop()


@pytest.mark.asyncio
async def test__dispatchablemessagequeue__queue_stopped__get_raises_exception():
    q = common.DispatchableMessageQueue(session_id='test')
    await q.stop()

    with pytest.raises(common.EndOfQueue):
        await q.get()


@pytest.mark.asyncio
async def test__dispatchablemessagequeue__queue_stopped__get_raises_exception__nowait():
    q = common.DispatchableMessageQueue(session_id='test')
    await q.stop()

    with pytest.raises(common.EndOfQueue):
        q.get_nowait()


@pytest.mark.asyncio
async def test__dispatchablemessagequeue__no_active_dispatcher__pause_raises_exception():
    q = common.DispatchableMessageQueue(session_id='test')

    with pytest.raises(common.StateError):
        async with q.pause_dispatching():
            pass


@pytest.mark.asyncio
async def test__dispatchablemessagequeue__active_dispatcher__able_to_pause_queue(receiver: asyncio.Queue):
    q = common.DispatchableMessageQueue(session_id='test', on_msg_coro=receiver.put)

    async with q.pause_dispatching():
        await q.put('test')
        assert await q.get() == 'test'

    await q.stop()


@pytest.mark.asyncio
async def test__dispatchablemessagequeue__queue_stopped_in_dispatcher__queue_is_stopped(receiver: asyncio.Queue):
    q = common.DispatchableMessageQueue(session_id='test')
    event = asyncio.Event()

    async def on_msg(_msg):
        event.set()
        await common.stop_task(q)

    q.start_dispatching(on_msg)

    await q.put('test')

    await event.wait()
    assert q.is_stopped() is True


@pytest.mark.asyncio
async def test__dispatchablemessagequeue__active_dispatcher__unable_to_start_dispatching_again(receiver: asyncio.Queue):
    q = common.DispatchableMessageQueue(session_id='test', on_msg_coro=receiver.put)

    with pytest.raises(common.StateError):
        q.start_dispatching(receiver.put)

    await q.stop()


@pytest.mark.asyncio
async def test__dispatchablemessagequeue__active_dispatcher__able_to_pause_dispatcher(receiver: asyncio.Queue):
    q = common.DispatchableMessageQueue(session_id='test', on_msg_coro=receiver.put)
    assert q.is_dispatching() is True

    async with q.pause_dispatching():
        assert q.is_dispatching() is False

    assert q.is_dispatching() is True

    await q.stop()


@pytest.mark.asyncio
async def test__dispatchablemessagequeue__no_active_dispatcher__unable_to_pause_dispatcher():
    q = common.DispatchableMessageQueue(session_id='test')

    with pytest.raises(common.StateError):
        async with q.pause_dispatching():
            pass