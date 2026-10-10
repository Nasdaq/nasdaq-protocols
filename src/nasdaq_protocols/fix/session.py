import abc
from datetime import datetime, timezone
from functools import reduce
from itertools import count
from operator import add
from typing import Callable, Any, Awaitable, Iterator, Protocol
import attrs

from nasdaq_protocols import common
from ._reader import FixMessageReader
from . import core


__all__ = [
    'FixSessionId',
    'OnFixMsgCoro',
    'OnGapCoro',
    'FixSession',
    'Fix44Session',
    'Fix50Session',
]


OnFixMsgCoro = Callable[[Any], Awaitable[None]]
OnGapCoro = Callable[[int, int], Awaitable[None]]


class SequenceReset(Protocol):
    NewSeqNo: int


class TestRequest(Protocol):
    TestReqID: str


_SESSION_MSG_TYPES = frozenset({
    core.HEART_BEAT_MSG,
    core.LOGOUT_MSG,
    core.LOGIN_MSG,
    core.TEST_REQUEST_MSG,
    core.RESEND_REQUEST_MSG,
    core.REJECT_MSG,
    core.SEQUENCE_RESET_MSG,
})


@attrs.define(auto_attribs=True)
class FixSessionId(common.SessionId):
    username: str = 'nouser'

    def __str__(self):
        return f'fix-{self.username}@{self.host}:{self.port}'


@attrs.define(auto_attribs=True)
@common.logable
class FixSession(common.AsyncSession):
    on_msg_coro: OnFixMsgCoro = None
    on_close_coro: common.OnCloseCoro = None
    sequence: Iterator[int] = attrs.field(default=1, kw_only=True)
    client_heartbeat_interval: int = attrs.field(default=1, kw_only=True)
    server_heartbeat_interval: int = attrs.field(default=1, kw_only=True)
    session_id: FixSessionId = attrs.Factory(FixSessionId)
    dispatch_on_connect: bool = False
    expected_seq_num: int | None = attrs.field(default=None, kw_only=True)
    on_gap: OnGapCoro | None = attrs.field(default=None, kw_only=True)
    reader_factory: common.ReaderFactory = attrs.field(init=False, default=FixMessageReader)
    sender_comp_id: str = attrs.field(init=False, default=None)
    sender_sub_id: str = attrs.field(init=False, default=None)
    target_comp_id: str = attrs.field(init=False, default=None)
    _logon_msg_type: str = attrs.field(init=False, default=None)
    _login_pending: bool = attrs.field(init=False, default=True)

    @abc.abstractmethod
    def begin_string(self):
        ...

    async def login(self, login_msg: core.Message) -> 'FixSession':
        self._initialize_session(login_msg)
        self.log.debug('%s> logging in ', self.session_id)
        self.send_msg(login_msg)

        try:
            logon_resp = await self.receive_msg()
            if not isinstance(logon_resp, login_msg.__class__):
                self.log.error(f'{self.session_id}> Login failed, {(str(logon_resp))}')
                await self.close()
                raise ConnectionRefusedError(str(logon_resp))
        except common.EndOfQueue:
            await self.close()
            raise ConnectionRefusedError('Connection reset by server.')  # pylint: disable=W0707

        self.log.debug('%s> received logon response: %s', self.session_id, logon_resp)
        self.log.debug('%s> login success', self.session_id)

        self._login_pending = False
        await self._check_for_gap(logon_resp)

        self.start_dispatching()
        self.start_heartbeats(self.client_heartbeat_interval, self.server_heartbeat_interval)
        return self

    async def on_message(self, msg: core.Message) -> None:
        if self._login_pending:
            await super().on_message(msg)
            return

        if msg.is_sequence_reset():
            self._handle_sequence_reset(msg)
            return

        seq = msg.Header.MsgSeqNum
        if seq < self.expected_seq_num:
            await self._handle_low_sequence(msg, seq)
            return
        if seq > self.expected_seq_num:
            self.log.debug('%s> dropping out-of-sequence msg seq=%s (expected=%s), '
                            'awaiting resend replay', self.session_id, seq, self.expected_seq_num)
            return
        self.expected_seq_num = seq + 1

        if msg.is_test_request():
            self._reply_to_test_request(msg)
        if not self._is_session_msg(msg):
            await super().on_message(msg)

    def send_msg(self, msg: core.Message, *, seq_num: int | None = None, poss_dup: bool = False) -> None:
        msg.validate(segments=[core.MessageSegments.BODY])
        msg.Header.SenderSubID = self.sender_sub_id
        msg.Header.TargetCompID = self.target_comp_id
        msg.Header.SenderCompID = self.sender_comp_id
        msg.Header.MsgSeqNum = next(self.sequence) if seq_num is None else seq_num
        msg.Header.SendingTime = datetime.now(timezone.utc).strftime("%Y%m%d-%H:%M:%S")
        if poss_dup:
            msg.Header.PossDupFlag = True
            msg.Header.OrigSendingTime = msg.Header.SendingTime

        data = self._prepare_complete_msg(msg)
        self.log.debug('%s> sent message[%s]: %s', self.session_id, msg.Name, data)
        self._transport.write(data)
        self.log.debug('%s> sent message[%s]: %s', self.session_id, msg.Name, msg.as_collection())

        if not msg.is_heartbeat() and self._local_hb_monitor:
            self._local_hb_monitor.ping()

    async def send_heartbeat(self):
        heart_beat = core.Message.Def[core.HEART_BEAT_MSG]()
        self.log.debug('%s> sending heartbeat: %s', self.session_id, heart_beat)
        self.send_msg(heart_beat)

    def _initialize_session(self, logon_msg):
        self.session_id.username = logon_msg.Username
        self.sequence = count(logon_msg.Header.MsgSeqNum)
        self.sender_comp_id = logon_msg.Header.SenderCompID
        self.sender_sub_id = logon_msg.Header.SenderSubID
        self.target_comp_id = logon_msg.Header.TargetCompID
        self._logon_msg_type = logon_msg.Type

    async def _check_for_gap(self, logon_resp: core.Message) -> None:
        seq = logon_resp.Header.MsgSeqNum
        if self.expected_seq_num is None or seq == self.expected_seq_num:
            # Needs confirmation with protocol spec: whether the Logon response's MsgSeqNum is
            # its own slot (requiring +1 here, as currently implemented) or already the
            # next sequence number the server will send (no +1 needed).
            self.expected_seq_num = seq + 1
        elif seq > self.expected_seq_num:
            self.log.info('%s> gap detected at logon, expected=%s received=%s', self.session_id,
                          self.expected_seq_num, seq)
            if self.on_gap is not None:
                await self.on_gap(self.expected_seq_num, seq)
            self._send_resend_request(self.expected_seq_num, 0)
        else:
            await self._handle_low_sequence(logon_resp, seq)

    def _handle_sequence_reset(self, msg: SequenceReset) -> None:
        new_seq_no = msg.NewSeqNo
        self.log.debug('%s> SequenceReset NewSeqNo=%s (expected was %s)', self.session_id,
                        new_seq_no, self.expected_seq_num)
        self.expected_seq_num = new_seq_no

    async def _handle_low_sequence(self, msg: core.Message, seq: int) -> None:
        if bool(self._read_header_field(msg, 'PossDupFlag', False)):
            self.log.debug('%s> dropping duplicate seq=%s (expected=%s)', self.session_id,
                            seq, self.expected_seq_num)
            return
        self.log.error('%s> fatal sequence error, received=%s < expected=%s', self.session_id,
                        seq, self.expected_seq_num)
        self._send_logout()
        self.initiate_close()

    def _reply_to_test_request(self, msg: TestRequest) -> None:
        heart_beat = core.Message.Def[core.HEART_BEAT_MSG]()
        test_req_id = msg.TestReqID
        if heart_beat.Body.contains('TestReqID'):
            heart_beat.TestReqID = test_req_id
        self.log.debug('%s> replying to TestRequest, TestReqID=%s', self.session_id, test_req_id)
        self.send_msg(heart_beat)

    def _send_resend_request(self, begin_seq_no: int, end_seq_no: int) -> None:
        resend_request = core.Message.Def[core.RESEND_REQUEST_MSG]()
        resend_request.BeginSeqNo = begin_seq_no
        resend_request.EndSeqNo = end_seq_no
        self.log.debug('%s> sending ResendRequest BeginSeqNo=%s EndSeqNo=%s', self.session_id,
                        begin_seq_no, end_seq_no)
        self.send_msg(resend_request)

    def _send_logout(self) -> None:
        self.log.debug('%s> sending Logout', self.session_id)
        self.send_msg(core.Message.Def[core.LOGOUT_MSG]())

    def _is_session_msg(self, msg: core.Message) -> bool:
        return msg.Type in _SESSION_MSG_TYPES or msg.Type == self._logon_msg_type

    @staticmethod
    def _segment_get(segment, name: str, default=None):
        if segment.contains(name) and name in segment:
            return segment[name]
        return default

    def _read_header_field(self, msg: core.Message, name: str, default=None):
        return self._segment_get(msg.Header, name, default)

    def _prepare_complete_msg(self, msg: core.Message) -> bytearray:
        data = bytearray(msg.to_bytes()[1])
        data[0:0] = core.Field.from_tag_value(core.MSG_TYPE_FIELD, msg.Type).to_bytes()[1] + core.SOH
        data[0:0] = core.Field.from_tag_value(core.BODY_LEN_FIELD, len(data)).to_bytes()[1] + core.SOH
        data[0:0] = core.Field.from_tag_value(core.BEGIN_STRING_FIELD, self.begin_string()).to_bytes()[1] + core.SOH
        checksum = str(reduce(add, data) % 256).rjust(3, '0')
        data.extend(core.Field.from_tag_value(core.CHECKSUM_FIELD, checksum).to_bytes()[1] + core.SOH)
        return data


@attrs.define(auto_attribs=True)
class Fix44Session(FixSession):
    def begin_string(self):
        return 'FIX.4.4'


@attrs.define(auto_attribs=True)
class Fix50Session(FixSession):
    def begin_string(self):
        return 'FIXT.1.1'
