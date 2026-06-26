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
    def deserialize(self):
        empty_response = (None, False, False)
        view = bytes(self._buffer[self._read_pos:])

        if view.find(MSG_TYPE_TAG) != -1:
            start = view.find(b'=', SKIP_FIRST_EQ_POS)
            if start == -1:
                return empty_response
            end = view.find(SOH, start)
            if end == -1:
                return empty_response
            body_length = int(view[start+1:end])
            msg_len = calc_msg_len(end+1, body_length)
            if len(view) < msg_len:
                return empty_response

            _len, msg = Message.from_bytes(view[:msg_len])
            self._read_pos += msg_len

            # Compact when more than half the buffer is consumed
            if self._read_pos > len(self._buffer) // 2:
                del self._buffer[:self._read_pos]
                self._read_pos = 0

            return msg, msg.is_logout(), msg.is_heartbeat()
        return empty_response


def calc_msg_len(third_field_pos: int, body_length: int) -> int:
    return third_field_pos + body_length + TRAILER_LENGTH
