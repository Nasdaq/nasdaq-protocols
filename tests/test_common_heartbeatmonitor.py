import asyncio
import time
import sys

import pytest
from nasdaq_protocols import common


@pytest.fixture(scope='function')
def monitor_trip_receiver_kit():
    q = asyncio.Queue()

    async def on_no_activity():
        q.put_nowait(time.time())

    yield q, on_no_activity


async def ping(monitor: common.HeartbeatMonitor, interval: float, times: int = sys.maxsize ** 10):
    for i in range(times):
        monitor.ping()
        await asyncio.sleep(interval)


@pytest.mark.asyncio
async def test_monitor_trips_when_not_pinged(monitor_trip_receiver_kit):
    q, receiver = monitor_trip_receiver_kit
    start_time = time.time()

    monitor = common.HeartbeatMonitor(session_id='test', interval=0.1, on_no_activity_coro=receiver)

    monitor_trip_time = await q.get()
    assert monitor_trip_time - start_time >= 0.1
    assert not monitor.is_running()


@pytest.mark.asyncio
async def test_monitor_does_not_trip_when_pinged(monitor_trip_receiver_kit):
    q, receiver = monitor_trip_receiver_kit
    start_time = time.time()
    monitor = common.HeartbeatMonitor(session_id='test', interval=0.1, on_no_activity_coro=receiver)

    pinger = asyncio.create_task(ping(monitor, 0.1, 5))

    monitor_trip_time = await q.get()
    assert pinger.done()
    assert (monitor_trip_time - start_time) >= 0.1 * 5
    assert not monitor.is_running()


@pytest.mark.asyncio
async def test_monitor_is_not_tripped_while_active_heartbeats(monitor_trip_receiver_kit):
    q, receiver = monitor_trip_receiver_kit
    monitor = common.HeartbeatMonitor(session_id='test', interval=0.1, on_no_activity_coro=receiver)

    # keep pinging
    pinger = asyncio.create_task(ping(monitor, 0.1))

    await asyncio.sleep(0.1 * 5)

    assert monitor.is_running()
    assert not pinger.done()
    with pytest.raises(asyncio.QueueEmpty):
        q.get_nowait()
    await monitor.stop()
    await common.stop_task(pinger)


@pytest.mark.asyncio
async def test_monitor_trips_when_pinged_after_interval(monitor_trip_receiver_kit):
    q, receiver = monitor_trip_receiver_kit
    start_time = time.time()

    monitor = common.HeartbeatMonitor(session_id='test', interval=0.1, on_no_activity_coro=receiver)
    await asyncio.sleep(0.2)
    monitor.ping()
    monitor_trip_time = await q.get()

    assert monitor_trip_time - start_time >= 0.1
    assert not monitor.is_running()


@pytest.mark.asyncio
async def test_shutdown_monitor_from_no_activity_coro_monitor_stops_itself(monitor_trip_receiver_kit):
    monitor = None
    event = asyncio.Event()

    async def receiver():
        await monitor.stop()
        event.set()

    monitor = common.HeartbeatMonitor(session_id='test', interval=0.1, on_no_activity_coro=receiver)

    await event.wait()
    assert monitor.is_stopped()


@pytest.mark.asyncio
async def test_shutdown_monitor_from_no_activity_coro(monitor_trip_receiver_kit):
    monitor = None
    event = asyncio.Event()

    async def receiver():
        await monitor.stop()
        event.set()

    monitor = common.HeartbeatMonitor(session_id='test', interval=0.1, on_no_activity_coro=receiver,
                                      stop_when_no_activity=False)

    await event.wait()
    assert monitor.is_stopped()