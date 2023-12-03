import asyncio
from typing import Any, Callable, Awaitable
from itertools import count

import attrs
from nasdaq_protocols.common import logable, stop_task, Validators


__all__ = [
    'HearbeatMonitor',
    'OnMonitorNoActivityCoro',
]


OnMonitorNoActivityCoro = Callable[[], Awaitable[None]]


@logable
@attrs.define(auto_attribs=True)
class HearbeatMonitor:
    """
    Monitors for no activity for configured interval.
    Activity is reported to this monitor by calling ping()
    """
    session_id: Any = attrs.field(validator=Validators.not_none())
    interval: float = attrs.field(validator=Validators.not_none())
    on_no_activity_coro: OnMonitorNoActivityCoro = attrs.field(validator=Validators.not_none())
    stop_when_no_activity: bool = attrs.field(kw_only=True, default=True)
    tolerate_missed_heartbeats: int = attrs.field(kw_only=True, default=1)
    _pinged: bool = attrs.field(init=False, default=True)
    _monitor_task: asyncio.Task = attrs.field(init=False, default=None)

    def __attrs_post_init__(self):
        self._monitor_task = asyncio.create_task(self._start_monitor(), name=f'{self.session_id}-monitor')
        self.log.debug('%s> monitor started.', self.session_id)

    def ping(self):
        self._pinged = True

    def is_running(self):
        return self._monitor_task is not None and not self._monitor_task.done()

    async def stop(self):
        self._monitor_task = await stop_task(self._monitor_task)

    async def _start_monitor(self):
        missed_heartbeats = count(1)
        while True:
            await asyncio.sleep(self.interval)

            if self._pinged:
                self._pinged = False
                missed_heartbeats = count(1)
                continue

            if next(missed_heartbeats) >= self.tolerate_missed_heartbeats:
                await self.on_no_activity_coro()
                if self.stop_when_no_activity:
                    break
