from typing import Any

import attrs
from nasdaq_protocols import common
from .core import SoupMessage


@attrs.define(auto_attribs=True)
@common.logable
class SoupMessageReader(common.Reader):
    def deserialize(self) -> Any:
        empty_response = (None, False, False)
        available = len(self._buffer) - self._read_pos

        if available < 2:
            return empty_response

        siz = int.from_bytes(self._buffer[self._read_pos:self._read_pos + 2], 'big')
        if (siz + 2) > available:
            return empty_response

        frame = bytes(memoryview(self._buffer)[self._read_pos:self._read_pos + siz + 2])
        _, msg = SoupMessage.from_bytes(frame)
        self._read_pos += siz + 2

        # Compact when more than half the buffer is consumed
        if self._read_pos > len(self._buffer) // 2:
            del self._buffer[:self._read_pos]
            self._read_pos = 0

        return msg, msg.is_logout(), msg.is_heartbeat()
