import abc
from datetime import datetime, timezone
from functools import reduce
from itertools import count
from operator import add
from typing import Callable, Any, Awaitable, Iterator
import attrs

from nasdaq_protocols import common
from ._reader import FixMessageReader
from . import core


__all__ = [
    'FixSessionId',
    'OnFixMsgCoro',
    'FixSession',
    'Fix44Session',
    'Fix50Session',
]


OnFixMsgCoro = Callable[[Any], Awaitable[None]]


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
    reader_factory: common.ReaderFactory = attrs.field(init=False, default=FixMessageReader)
    sender_comp_id: str = attrs.field(init=False, default=None)
    sender_sub_id: str = attrs.field(init=False, default=None)
    target_comp_id: str = attrs.field(init=False, default=None)

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
        self.start_dispatching()
        self.start_heartbeats(self.client_heartbeat_interval, self.server_heartbeat_interval)
        return self

    def send_msg(self, msg: core.Message) -> None:
        msg.validate(segments=[core.MessageSegments.BODY])
        msg.Header.SenderSubID = self.sender_sub_id
        msg.Header.TargetCompID = self.target_comp_id
        msg.Header.SenderCompID = self.sender_comp_id
        msg.Header.MsgSeqNum = next(self.sequence)
        msg.Header.SendingTime = datetime.now(timezone.utc).strftime("%Y%m%d-%H:%M:%S")

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
        self.sequence = count(logon_msg.Header.MsgSeqNum.value)
        self.sender_comp_id = logon_msg.Header.SenderCompID
        self.sender_sub_id = logon_msg.Header.SenderSubID
        self.target_comp_id = logon_msg.Header.TargetCompID

    def _prepare_complete_msg(self, msg: core.Message) -> bytearray:
        data = bytearray(msg.to_bytes()[1])
        data[0:0] = core.Field.from_tag_value(core.MSG_TYPE_FIELD, msg.Type).to_bytes()[1] + core.SOH
        data[0:0] = core.Field.from_tag_value(core.BODY_LEN_FIELD, len(data)).to_bytes()[1] + core.SOH
        data[0:0] = core.Field.from_tag_value(core.BEGIN_STRING_FIELD, self.begin_string()).to_bytes()[1] + core.SOH
        # Fill the checksum
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
