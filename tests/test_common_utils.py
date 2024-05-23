import asyncio

import attrs
import pytest
from nasdaq_protocols import common


def test__loggable__unable_to_decorate_function():

    with pytest.raises(AssertionError):
        @common.logable
        def func():
            pass


def test__loggable__able_to_decorate_class():
    @common.logable
    class A:
        pass

    assert hasattr(A, 'log')
    assert A.log.name == 'A'


def test__not_none_validator__fails_when_none_is_supplied():
    @attrs.define
    class A:
        attr: str | None = attrs.field(validator=common.Validators.not_none())

    with pytest.raises(ValueError):
        A(None)


def test__not_none_validator__accepts_valid_value():
    @attrs.define
    class A:
        attr: str = attrs.field(validator=common.Validators.not_none())

    assert A('test').attr == 'test'


@pytest.mark.asyncio
async def test__stop_task__stops_an_async_task():
    q = asyncio.Queue()

    task = asyncio.create_task(q.get())
    assert not task.done()

    await common.stop_task(task)
    assert task.done()
    assert task.cancelled()


@pytest.mark.asyncio
async def test__stop_task__stops_task_even_if_runtime_error_is_raised():
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
async def test__stop_task__no_effect_on_already_stopped_tasks():
    q = asyncio.Queue()

    task = asyncio.create_task(q.get())

    task = await common.stop_task(task)
    await common.stop_task(task)
