import time

import pytest
import asyncio

from nasdaq_protocols.common import StateError
from nasdaq_protocols.common.sync_executor import SyncExecutor


@pytest.fixture
def sync_executor():
    executor = SyncExecutor(name="test")
    yield executor
    executor.stop()


async def async_function():
    await asyncio.sleep(0.1)
    return "async result"


def test__sync_executor__execute(sync_executor):
    result = sync_executor.execute(async_function())
    assert result == "async result"


def test__sync_executor__execute_with_timeout(sync_executor):
    result = sync_executor.execute(async_function(), timeout=1)
    assert result == "async result"


def test__sync_executor__execute_timeout_error(sync_executor):
    with pytest.raises(asyncio.TimeoutError):
        sync_executor.execute(async_function(), timeout=0.01)


def test__sync_executor__execute_sync(sync_executor):
    output = []

    def sync_function():
        # A use case where a sync function creates an async task
        async def _():
            await asyncio.sleep(0.1)
            output.append("async result")
        return asyncio.create_task(_())

    result = sync_executor.execute_sync(sync_function)

    while not result.done():
        time.sleep(0.01)

    assert output == ["async result"]


def test__sync_executor__execute_after_stop(sync_executor):
    sync_executor.stop()
    with pytest.raises(RuntimeError):
        sync_executor.execute(async_function())

    with pytest.raises(StateError):
        sync_executor.execute_sync(lambda: None)


def test__sync_executor__invalid_underlying(sync_executor):
    with pytest.raises(ValueError):
        sync_executor.execute(None)

    with pytest.raises(ValueError):
        sync_executor.execute_sync(None)

    with pytest.raises(ValueError):
        sync_executor.execute_sync(async_function())

    with pytest.raises(ValueError):
        sync_executor.execute(lambda: None)