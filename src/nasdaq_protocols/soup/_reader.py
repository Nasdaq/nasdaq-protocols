from typing import Any

import attrs
from nasdaq_protocols import common
from .core import SoupMessage


@attrs.define(auto_attribs=True)
@common.logable
class SoupMessageReader(common.Reader):
    def deserialize(self) -> Any:
        empty_response = (None, False, False)
        buff_len = len(self._buffer)

        if buff_len < 2:
            return empty_response

        siz = int.from_bytes(self._buffer[:2], 'big')
        if (siz+2) > buff_len:
            return empty_response

        _, msg = SoupMessage.from_bytes(self._buffer[:siz + 2])
        self._buffer = self._buffer[siz + 2:]

        return msg, msg.is_logout(), msg.is_heartbeat()
