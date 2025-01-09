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
        if self._buffer.find(MSG_TYPE_TAG) != -1:
            start = self._buffer.find(b'=', SKIP_FIRST_EQ_POS)
            if start == -1:
                return empty_response
            end = self._buffer.find(SOH, start)
            if end == -1:
                return empty_response
            body_length = int(self._buffer[start+1:end])
            msg_len = calc_msg_len(end+1, body_length)
            if len(self._buffer) < msg_len:
                return empty_response

            _len, msg = Message.from_bytes(self._buffer[:msg_len])
            self._buffer = self._buffer[msg_len:]
            return msg, msg.is_logout(), msg.is_heartbeat()
        return empty_response


def calc_msg_len(third_field_pos: int, body_length: int) -> int:
    return third_field_pos + body_length + TRAILER_LENGTH
