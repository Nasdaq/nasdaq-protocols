"""
nasdaq_protocols.soup.core module contains the implementation of the
soup messages.
"""
import enum
import struct
from typing import Type

import attrs
from nasdaq_protocols import common

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


class LoginRejectReason(enum.Enum):
    """Login Reject Reason sent from server in case of login failure."""

    NOT_AUTHORIZED = 'A'
    SESSION_NOT_AVAILABLE = 'S'

    @classmethod
    def get(cls, reason: str):
        """Get the LoginRejectReason enum value from the given reason."""
        return reason if isinstance(reason, cls) else LoginRejectReason(reason)


@common.logable
class SoupMessage(common.Serializable['SoupMessage']):
    """
    Base class for all soup messages.

    Given raw bytes use this class to unpack the bytes to the corresponding soup message::

        input_bytes = b'\x00\x1fAtest      2                   '
        len, soup_msg = SoupMessage.from_bytes(input_bytes)
        type(soup_msg)

    """

    ClassByIndicator = {}
    Format = '!h c'
    Length = 1
    Indicator = ''

    def __init_subclass__(cls, indicator: str, description: str, **kwargs):
        assert len(indicator) == 1, f'Invalid type {indicator}, type can be only one character'
        SoupMessage.ClassByIndicator[indicator] = cls
        cls.Indicator = indicator
        cls.Description = description

    def to_bytes(self) -> tuple[int, bytes]:
        """
        Pack the soup message to binary format

        :return: tuple of length and bytes
        """
        bytes_ = struct.pack(SoupMessage.Format, SoupMessage.Length, self.Indicator.encode('ascii'))
        return len(bytes_), bytes_

    @classmethod
    def from_bytes(cls, bytes_) -> tuple[int, Type['SoupMessage']]:
        """
        unpacks the bytes to the corresponding soup message

        :param bytes_: bytes to unpack
        :return: tuple of length and soup message
        """
        try:
            return len(bytes_), SoupMessage.ClassByIndicator[chr(bytes_[2])].unpack(bytes_)
        except KeyError:
            indicator = chr(bytes_[2])
            raise InvalidSoupMessage(f'unpacking soup message with unknown {indicator=}, received = {bytes_}')
        except IndexError:
            raise InvalidSoupMessage(f'not enough bytes to unpack, received = {bytes_}')

    @classmethod
    def unpack(cls, bytes_: bytes) -> Type['SoupMessage'] | 'SoupMessage':
        try:
            _, _ = struct.unpack(SoupMessage.Format, bytes_)
            return cls()
        except struct.error:
            raise InvalidSoupMessage(f'invalid soup message, received = {bytes_}')

    def is_heartbeat(self):
        return False

    def is_logout(self):
        return False


@attrs.define(slots=False, auto_attribs=True)
class LoginRequest(SoupMessage, indicator='L', description='Login Request'):
    """
    SoupBinTCP Login Request Message.

    :param user: Username to login
    :type user: str

    :param password:  Password to login
    :type password: str

    :param session: Name of the session to join [Default=''] .
    :type session: str

    :param sequence: The sequence number. [Default=1]
    :type sequence: str
    """

    Format = '!h c 6s 10s 10s 20s'
    Length = 47

    user: str
    password: str = attrs.field(repr=False)
    session: str
    sequence: str

    def to_bytes(self) -> tuple[int, bytes]:
        """
        Pack the soup message to binary format

        :return:
        """
        bytes_ = struct.pack(LoginRequest.Format,
                             LoginRequest.Length,
                             self.Indicator.encode('ascii'),
                             _pack(self.user, 6),
                             _pack(self.password, 10),
                             _pack(self.session, 10),
                             _pack(str(self.sequence), 20))
        return len(bytes_), bytes_

    @classmethod
    def unpack(cls, bytes_):
        _1, _2, user, passwd, sess, seq = struct.unpack(LoginRequest.Format, bytes_)
        return LoginRequest(_unpack_string(user),
                            _unpack_string(passwd),
                            _unpack_string(sess),
                            str(_unpack_int(seq)))


@attrs.define(slots=False, auto_attribs=True)
class LoginAccepted(SoupMessage, indicator='A', description='Login Accepted'):
    """
    SoupBinTCP Login Accepted Message.

    :param session_id: Name of the session joined [Default=''] .
    :param sequence: The next sequence number.
    """
    Format = '!h c 10s 20s'
    Len = 31

    session_id: str
    sequence: int

    def to_bytes(self) -> tuple[int, bytes]:
        """
        Pack the soup message to binary format
        :return: bytes
        """
        bytes_ = struct.pack(LoginAccepted.Format,
                             LoginAccepted.Len, self.Indicator.encode('ascii'),
                             _pack(self.session_id, 10),
                             _pack(str(self.sequence), 20))
        return len(bytes_), bytes_

    @classmethod
    def unpack(cls, bytes_):
        _, _, sess, seq = struct.unpack(LoginAccepted.Format, bytes_)
        return LoginAccepted(_unpack_string(sess), _unpack_int(seq))


@attrs.define(slots=False, auto_attribs=True)
class LoginRejected(SoupMessage, indicator='J', description='Login Rejected'):
    """
    SoupBinTCP Login Rejected Message.

    :param reason: Reason for login failure. Refer `LoginRejectReason`
    """
    Format = '!h c c'
    Length = 2

    reason: LoginRejectReason = attrs.field(converter=LoginRejectReason.get)

    def to_bytes(self) -> tuple[int, bytes]:
        """
        Pack the soup message to binary format
        :return: bytes
        """
        bytes_ = struct.pack(LoginRejected.Format,
                             LoginRejected.Length,
                             self.Indicator.encode('ascii'),
                             self.reason.value.encode('ascii'))
        return len(bytes_), bytes_

    @classmethod
    def unpack(cls, bytes_):
        _, _, rea = struct.unpack(LoginRejected.Format, bytes_)
        return LoginRejected(_unpack_string(rea))


@attrs.define(slots=False, auto_attribs=True)
class SequencedData(SoupMessage, indicator='S', description='Sequenced Data'):
    """
    SoupBinTCP Sequenced Data Message.

    :param data: The application payload sent by the server.
    """
    data: bytes

    def to_bytes(self) -> tuple[int, bytes]:
        """
        Pack the soup message to binary format
        :return: bytes
        """
        msg = struct.pack(SoupMessage.Format, len(self.data) + 1, self.Indicator.encode('ascii'))
        bytes_ = msg + bytes(self.data)
        return len(bytes_), bytes_

    @classmethod
    def unpack(cls, bytes_):
        len_, _ = struct.unpack(SoupMessage.Format, bytes_[:3])
        return SequencedData(bytes_[3:] if len_ > 1 else b'')


@attrs.define(slots=False, auto_attribs=True)
class UnSequencedData(SoupMessage, indicator='U', description='UnSequenced Data'):
    """
    SoupBinTCP Unsequenced Data Message.

    :param data: The application payload to be sent to server.
    """
    data: bytes

    def to_bytes(self) -> tuple[int, bytes]:
        """
        Pack the soup message to binary format
        :return: bytes
        """
        msg = struct.pack(SoupMessage.Format, len(self.data) + 1, self.Indicator.encode('ascii'))
        bytes_ = msg + bytes(self.data)
        return len(bytes_), bytes_

    @classmethod
    def unpack(cls, bytes_):
        len_, _ = struct.unpack(SoupMessage.Format, bytes_[:3])
        return UnSequencedData(bytes_[3:] if len_ > 1 else b'')


@attrs.define(slots=False, auto_attribs=True)
class Debug(SoupMessage, indicator='+', description='Debug'):
    """
    SoupBinTCP Debug Message.

    :param msg: The debug message.
    """
    msg: str

    def to_bytes(self) -> tuple[int, bytes]:
        """
        Pack the soup message to binary format
        :return: bytes
        """
        msg = struct.pack(SoupMessage.Format, len(self.msg) + 1, self.Indicator.encode('ascii'))
        bytes_ = msg + self.msg.encode('ascii')
        return len(bytes_), bytes_

    @classmethod
    def unpack(cls, bytes_):
        len_, _ = struct.unpack(SoupMessage.Format, bytes_[:3])
        return Debug(bytes_[3:].decode('ascii') if len_ > 1 else '')


@attrs.define(slots=False, auto_attribs=True)
class ClientHeartbeat(SoupMessage, indicator='R', description='Client Heartbeat'):
    """
    SoupBinTCP Client Heartbeat Message.
    """

    def is_heartbeat(self):
        return True


@attrs.define(slots=False, auto_attribs=True)
class ServerHeartbeat(SoupMessage, indicator='H', description='Server Heartbeat'):
    """
    SoupBinTCP Server Heartbeat Message.
    """

    def is_heartbeat(self):
        return True


@attrs.define(slots=False, auto_attribs=True)
class EndOfSession(SoupMessage, indicator='Z', description='End of Session'):
    """
    SoupBinTCP End of Session Message.

    This message is sent from server to indicate the soup stream is now closed.
    """

    def is_logout(self):
        return True


@attrs.define(slots=False, auto_attribs=True)
class LogoutRequest(SoupMessage, indicator='O', description='LogoutRequest'):
    """
    SoupBinTCP Logout Request Message.

    This message is initiated by the client to sever for graceful session logoff.
    """

    def is_logout(self):
        return True


def _pack(data, field_size):
    return data.ljust(field_size).encode('ascii')


def _unpack_string(bytes_):
    return bytes_.decode('ascii').strip()


def _unpack_int(bytes_):
    return int(bytes_.strip(b' \x00'))
