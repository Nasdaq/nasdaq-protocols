import asyncio

import attrs
import pytest
from nasdaq_protocols import common


def test_unable_to_decorate_function_with_loggable():

    with pytest.raises(AssertionError):
        @common.logable
        def func():
            pass


def test_able_to_decorate_class_with_logable():
    @common.logable
    class A:
        pass

    assert hasattr(A, 'log')
    assert A.log.name == 'A'


def test_not_none_validator_prevents_none():
    @attrs.define
    class A:
        attr: str = attrs.field(validator=common.Validators.not_none())

    with pytest.raises(ValueError):
        A(None)


def test_not_none_validator_accepts_valid_value():
    @attrs.define
    class A:
        attr: str = attrs.field(validator=common.Validators.not_none())

    assert A('test').attr == 'test'


@pytest.mark.asyncio
async def test_stop_task_cancels_task():
    q = asyncio.Queue()

    task = asyncio.create_task(q.get())
    assert not task.done()

    await common.stop_task(task)
    assert task.done()
    assert task.cancelled()


@pytest.mark.asyncio
async def test_stop_task_stops_task_on_any_runtime_error():
    reader_ready_to_be_stopped = asyncio.Event()

    async def reader():
        try:
            q = asyncio.Queue()
            reader_ready_to_be_stopped.set()
            await q.get()
        finally:
            raise RuntimeError('test')

    task = asyncio.create_task(reader())

    await reader_ready_to_be_stopped.wait()
    await common.stop_task(task)
    assert task.done()


@pytest.mark.asyncio
async def test_stop_task_on_already_stopped_tasks():
    q = asyncio.Queue()

    task = asyncio.create_task(q.get())

    task = await common.stop_task(task)
    await common.stop_task(task)

