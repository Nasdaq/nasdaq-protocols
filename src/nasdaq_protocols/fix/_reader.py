import asyncio

import attrs
from nasdaq_protocols import common
from .core import Message, SOH


__all__ = [
    'FixMessageReader'
]
SKIP_FIRST_EQ_POS = 2
TRAILER_LENGTH = 7
MSG_TYPE_TAG = b'35='


@attrs.define(auto_attribs=True)
@common.logable
class FixMessageReader(common.Reader):
    _buffer: bytearray = attrs.field(init=False, factory=bytearray)
    _task: asyncio.Task = attrs.field(init=False, default=None)
    _stopped: bool = attrs.field(init=False, default=False)

    async def on_data(self, data: bytes):
        self.log.debug('%s> on_data: existing = %s, received = %s', self.session_id, self._buffer, data)
        if len(data) == 0:
            return
        self._buffer.extend(data)
        self._task = asyncio.create_task(self._process(), name=f'fix-reader:{self.session_id}')

    async def stop(self):
        await common.stop_task(self._task)
        await self.on_close_coro()
        self.log.debug('%s> stopped.', self.session_id)

    def is_stopped(self):
        return self._stopped

    async def _process(self):
        while self._buffer.find(MSG_TYPE_TAG) != -1:
            start = self._buffer.find(b'=', SKIP_FIRST_EQ_POS)
            end = self._buffer.find(SOH, start)
            body_length = int(self._buffer[start+1:end])
            msg_len = calc_msg_len(end+1, body_length)
            if len(self._buffer) < msg_len:
                self.log.debug('%s> not enough value, value size = %d, body length = %d',
                               self.session_id, len(self._buffer), body_length)
                return

            _len, msg = Message.from_bytes(self._buffer[:msg_len])

            if msg.is_logout():
                await self.on_close_coro()
                return

            try:
                await self.on_msg_coro(msg)
            except Exception:  # pylint: disable=broad-except
                await self.on_close_coro()
            self._buffer = self._buffer[msg_len:]


def calc_msg_len(third_field_pos: int, body_length: int) -> int:
    return third_field_pos + body_length + TRAILER_LENGTH
