import enum
import struct

import attrs
from nasdaq_protocols.common import logable, Serializable


__all__ = [
    'InvalidSoupMessage',
    'LoginRejectReason',
    'SoupMessage',
    'LoginRequest',
    'LoginAccepted',
    'LoginRejected',
    'SequencedData',
    'UnSequencedData',
    'Debug',
    'ClientHeartbeat',
    'ServerHeartbeat',
    'EndOfSession',
    'LogoutRequest'
]


class InvalidSoupMessage(ValueError):
    """Raised when an invalid soup message is received."""
    pass


class LoginRejectReason(enum.Enum):
    NOT_AUTHORIZED = 'A'
    SESSION_NOT_AVAILABLE = 'S'

    @classmethod
    def get(cls, reason: str):
        """Get the LoginRejectReason enum value from the given reason."""
        return reason if isinstance(reason, cls) else LoginRejectReason(reason)


@logable
class SoupMessage(Serializable):
    """Base class for all soup messages."""

    ClassByIndicator = {}
    Format = '!h c'
    Length = 1
    Indicator = ''

    def __init_subclass__(cls, indicator: str, description: str, **kwargs):
        assert len(indicator) == 1, f'Invalid type {indicator}, type can be only one character'
        SoupMessage.ClassByIndicator[indicator] = cls
        cls.Indicator = indicator
        cls.Description = description

    def to_bytes(self) -> bytes:
        """Pack the soup message to binary format"""
        return struct.pack(SoupMessage.Format, SoupMessage.Length, self.Indicator.encode('ascii'))

    @classmethod
    def from_bytes(cls, bytes_):
        """unpacks the bytes to the corresponding soup message"""
        try:
            return SoupMessage.ClassByIndicator[chr(bytes_[2])].unpack(bytes_)
        except KeyError:
            indicator = chr(bytes_[2])
            raise InvalidSoupMessage(f'unpacking soup message with unknown {indicator=}, received = {bytes_}')
        except IndexError:
            raise InvalidSoupMessage(f'not enough bytes to unpack, received = {bytes_}')

    @classmethod
    def unpack(cls, bytes_: bytes):
        _, _ = struct.unpack(SoupMessage.Format, bytes_)
        return cls()

    def is_heartbeat(self):
        return False

    def is_logout(self):
        return False


@attrs.define(slots=False, auto_attribs=True)
class LoginRequest(SoupMessage, indicator='L', description='Login Request'):
    Format = '!h c 6s 10s 10s 20s'
    Length = 47

    user: str
    password: str = attrs.field(repr=False)
    session: str
    sequence: str

    def to_bytes(self):
        return struct.pack(LoginRequest.Format,
                           LoginRequest.Length,
                           self.Indicator.encode('ascii'),
                           _pack(self.user, 6),
                           _pack(self.password, 10),
                           _pack(self.session, 10),
                           _pack(str(self.sequence), 20))

    @classmethod
    def unpack(cls, bytes_):
        _1, _2, user, passwd, sess, seq = struct.unpack(LoginRequest.Format, bytes_)
        return LoginRequest(_unpack_string(user),
                            _unpack_string(passwd),
                            _unpack_string(sess),
                            str(_unpack_int(seq)))


@attrs.define(slots=False, auto_attribs=True)
class LoginAccepted(SoupMessage, indicator='A', description='Login Accepted'):
    Format = '!h c 10s 20s'
    Len = 31

    session_id: str
    sequence: int

    def to_bytes(self):
        return struct.pack(LoginAccepted.Format,
                           LoginAccepted.Len, self.Indicator.encode('ascii'),
                           _pack(self.session_id, 10),
                           _pack(str(self.sequence), 20))

    @classmethod
    def unpack(cls, bytes_):
        _, _, sess, seq = struct.unpack(LoginAccepted.Format, bytes_)
        return LoginAccepted(_unpack_string(sess), _unpack_int(seq))


@attrs.define(slots=False, auto_attribs=True)
class LoginRejected(SoupMessage, indicator='J', description='Login Rejected'):
    Format = '!h c c'
    Length = 2

    reason: LoginRejectReason = attrs.field(converter=LoginRejectReason.get)

    def to_bytes(self):
        return struct.pack(LoginRejected.Format,
                           LoginRejected.Length,
                           self.Indicator.encode('ascii'),
                           self.reason.value.encode('ascii'))

    @classmethod
    def unpack(cls, bytes_):
        _, _, rea = struct.unpack(LoginRejected.Format, bytes_)
        return LoginRejected(_unpack_string(rea))


@attrs.define(slots=False, auto_attribs=True)
class SequencedData(SoupMessage, indicator='S', description='Sequenced Data'):
    data: bytes

    def to_bytes(self):
        msg = struct.pack(SoupMessage.Format,
                          len(self.data)+1,
                          self.Indicator.encode('ascii'))
        return msg + bytes(self.data)

    @classmethod
    def unpack(cls, bytes_):
        len_, _ = struct.unpack(SoupMessage.Format, bytes_[:3])
        return SequencedData(bytes_[3:] if len_ > 1 else b'')


@attrs.define(slots=False, auto_attribs=True)
class UnSequencedData(SoupMessage, indicator='U', description='UnSequenced Data'):
    data: bytes

    def to_bytes(self):
        msg = struct.pack(SoupMessage.Format,
                          len(self.data)+1,
                          self.Indicator.encode('ascii'))
        return msg + bytes(self.data)

    @classmethod
    def unpack(cls, bytes_):
        len_, _ = struct.unpack(SoupMessage.Format, bytes_[:3])
        return UnSequencedData(bytes_[3:] if len_ > 1 else b'')


@attrs.define(slots=False, auto_attribs=True)
class Debug(SoupMessage, indicator='+', description='Debug'):
    msg: str

    def to_bytes(self):
        msg = struct.pack(SoupMessage.Format,
                          len(self.msg) + 1,
                          self.Indicator.encode('ascii'))
        return msg + self.msg.encode('ascii')

    @classmethod
    def unpack(cls, bytes_):
        len_, _ = struct.unpack(SoupMessage.Format, bytes_[:3])
        return Debug(bytes_[3:].decode('ascii') if len_ > 1 else '')


@attrs.define(slots=False, auto_attribs=True)
class ClientHeartbeat(SoupMessage, indicator='R', description='Client Heartbeat'):
    def is_heartbeat(self):
        return True


@attrs.define(slots=False, auto_attribs=True)
class ServerHeartbeat(SoupMessage, indicator='H', description='Server Heartbeat'):
    def is_heartbeat(self):
        return True


@attrs.define(slots=False, auto_attribs=True)
class EndOfSession(SoupMessage, indicator='Z', description='End of Session'):
    def is_logout(self):
        return True


@attrs.define(slots=False, auto_attribs=True)
class LogoutRequest(SoupMessage, indicator='O', description='LogoutRequest'):
    def is_logout(self):
        return True


def _pack(data, field_size):
    return data.ljust(field_size).encode('ascii')


def _unpack_string(bytes_):
    return bytes_.decode('ascii').strip()


def _unpack_int(bytes_):
    return int(bytes_.strip(b' \x00'))