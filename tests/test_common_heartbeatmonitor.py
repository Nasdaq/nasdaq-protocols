import asyncio
import time
import sys

import pytest
from nasdaq_protocols import common


@pytest.fixture(scope='function')
def monitor_trip_receiver_kit():
    """
    returns a tuple of a queue and a receiver coroutine that puts
    the time when it is called into the queue

    The queue represents the time points when the monitor trips
    """
    q = asyncio.Queue()

    async def on_no_activity():
        q.put_nowait(time.time())

    yield q, on_no_activity


async def ping(monitor: common.HeartbeatMonitor, interval: float, times: int = sys.maxsize ** 10):
    for i in range(times):
        monitor.ping()
        await asyncio.sleep(interval)


@pytest.mark.asyncio
async def test__heartbeatmonitor__when_no_heartbeats__trips(monitor_trip_receiver_kit):
    q, receiver = monitor_trip_receiver_kit
    start_time = time.time()

    monitor = common.HeartbeatMonitor(session_id='test', interval=0.1, on_no_activity_coro=receiver)

    monitor_trip_time = await q.get()
    assert monitor_trip_time - start_time >= 0.1
    assert not monitor.is_running()


@pytest.mark.asyncio
async def test__heartbeatmonitor__after_heart_beats_stop__trips(monitor_trip_receiver_kit):
    q, receiver = monitor_trip_receiver_kit
    start_time = time.time()
    monitor = common.HeartbeatMonitor(session_id='test', interval=0.1, on_no_activity_coro=receiver)

    pinger = asyncio.create_task(ping(monitor, 0.1, 5))

    monitor_trip_time = await q.get()
    assert pinger.done()
    assert (monitor_trip_time - start_time) >= 0.1 * 5
    assert not monitor.is_running()


@pytest.mark.asyncio
async def test__heatbeatmonitor__active_heartbeats__monitor_is_active(monitor_trip_receiver_kit):
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
async def test__heartbeatmonitor__delayed_heart_beats__trips(monitor_trip_receiver_kit):
    q, receiver = monitor_trip_receiver_kit
    start_time = time.time()

    monitor = common.HeartbeatMonitor(session_id='test', interval=0.1, on_no_activity_coro=receiver)
    await asyncio.sleep(0.2)
    monitor.ping()
    monitor_trip_time = await q.get()

    assert monitor_trip_time - start_time >= 0.1
    assert not monitor.is_running()


@pytest.mark.asyncio
@pytest.mark.parametrize('stop_flag', [True, False])
async def test__heartbeatmonitor__stopped_from_trip_handler__monitor_is_stopped(monitor_trip_receiver_kit, stop_flag):
    monitor = None
    event = asyncio.Event()

    async def receiver():
        await monitor.stop()
        event.set()

    monitor = common.HeartbeatMonitor(session_id='test', interval=0.1, on_no_activity_coro=receiver,
                                      stop_when_no_activity=stop_flag)

    await event.wait()
    assert monitor.is_stopped()
