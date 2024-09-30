import asyncio

import attrs
from nasdaq_protocols import common
from .core import SoupMessage


@attrs.define(auto_attribs=True)
@common.logable
class SoupMessageReader(common.Reader):
    _buffer: bytearray = attrs.field(init=False, factory=bytearray)
    _task: asyncio.Task = attrs.field(init=False, default=None)
    _stopped: bool = attrs.field(init=False, default=False)

    async def on_data(self, data: bytes):
        self.log.debug('%s> on_data: existing = %s, received = %s', self.session_id, self._buffer, data)
        if len(data) == 0:
            return
        self._buffer.extend(data)
        self._task = asyncio.create_task(self._process(), name=f'soup-reader:{self.session_id}')

    async def stop(self):
        await common.stop_task(self._task)
        await self.on_close_coro()
        self.log.debug('%s> stopped.', self.session_id)

    def is_stopped(self):
        return self._stopped

    async def _process(self):
        buff_len = len(self._buffer)
        while buff_len > 1:
            siz = int.from_bytes(self._buffer[:2], 'big')
            if (siz+2) > buff_len:
                # entire message not received yet
                return
            _, msg = SoupMessage.from_bytes(self._buffer[:siz + 2])

            if msg.is_logout():
                await self.on_close_coro()
                return

            if not msg.is_heartbeat():
                self.log.debug('%s> dispatching message %s', self.session_id, str(msg))
                try:
                    await self.on_msg_coro(msg)
                except Exception:  # pylint: disable=broad-except
                    await self.on_close_coro()
            else:
                self.log.debug('%s> received heartbeat', self.session_id)

            self._buffer = self._buffer[siz + 2:]
            buff_len -= (siz+2)
