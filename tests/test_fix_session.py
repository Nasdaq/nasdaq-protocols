import asyncio

import pytest

from nasdaq_protocols.common import stop_task
from nasdaq_protocols.fix.session import (
    Fix44Session,
    Fix50Session
)
from .fix_messages import *
from .mocks import *


EXP_LOGON_MSG_B = b'8=FIX.4.4\x019=79\x0135=L\x0134=1\x0149=CLIENT\x0150=CLIENT_SUB\x0156=SERVER\x0152=20241003-22:02:54\x01553=test_user\x0110=031\x01'
EXP_LOGON_MSG = Login.from_bytes(EXP_LOGON_MSG_B)[1]
ENTER_LOGIN_MSG = Login({
        fix.MessageSegments.HEADER: {
            'SenderCompID': 'CLIENT',
            'TargetCompID': 'SERVER',
            'MsgSeqNum': 1,
        },
        fix.MessageSegments.BODY: {
            'Username': 'test_user'
        }
    })


def if_logon(username: str):
    def matcher(actual):
        msg = fix.Message.from_bytes(actual)[1]
        return msg.Username == username
    return matcher


def if_heartbeat():
    def matcher(actual):
        msg = fix.Message.from_bytes(actual)[1]
        return msg.is_heartbeat()
    return matcher


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__login_successful(mock_server_session, session_factory):
    port, server_session = mock_server_session

    server_session.when(
        if_logon("test_user"), 'match-login-request'
    ).do(
        send(EXP_LOGON_MSG), 'send-login-accept'
    )

    fix_session = await fix.connect_async(
        ('127.0.0.1', port), ENTER_LOGIN_MSG, session_factory
    )

    await fix_session.close()


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__login_failed(mock_server_session, session_factory):
    port, server_session = mock_server_session

    nope_msg_b = EXP_LOGON_MSG_B.replace(b'35=L', b'35=N')
    nope_msg = Nope.from_bytes(nope_msg_b)[1]

    server_session.when(
        if_logon("test_user"), 'match-login-request'
    ).do(
        send(nope_msg), 'send-login-reject'
    )

    with pytest.raises(ConnectionRefusedError):
        await fix.connect_async(
            ('127.0.0.1', port), ENTER_LOGIN_MSG, session_factory
        )


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__login_failed__server_closes_connection(mock_server_session, session_factory):
    port, server_session = mock_server_session

    server_session.when(
        if_logon("test_user"), 'match-login-request'
    ).do(
        lambda s, _d: s.close(), 'close-connection'
    )

    with pytest.raises(ConnectionRefusedError):
        await fix.connect_async(
            ('127.0.0.1', port), ENTER_LOGIN_MSG, session_factory
        )


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__no_server_heartbeats__session_closed(mock_server_session, session_factory):
    port, server_session = mock_server_session
    server_heartbeat_interval = 0.1

    server_session.when(
        if_logon("test_user"), 'match-login-request'
    ).do(
        send(EXP_LOGON_MSG), 'send-login-accept'
    )

    session = await fix.connect_async(
        ('127.0.0.1', port), ENTER_LOGIN_MSG,
        lambda : session_factory(
            client_heartbeat_interval=100,
            server_heartbeat_interval=server_heartbeat_interval
        )
    )

    # Wait for server heartbeat interval to timeout.
    await asyncio.sleep((server_heartbeat_interval * 2) + 1)

    assert session.is_closed()


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__client_heartbeats__session_is_active(mock_server_session, session_factory):
    port, server_session = mock_server_session
    heart_beats_received = []
    heart_beat_interval = 0.1

    server_session.when(
        if_logon("test_user"), 'match-login-request'
    ).do(
        send(EXP_LOGON_MSG), 'send-login-accept'
    )

    session = await fix.connect_async(
        ('127.0.0.1', port), ENTER_LOGIN_MSG,
        lambda : session_factory(
            client_heartbeat_interval=heart_beat_interval,
            server_heartbeat_interval=100
        )
    )

    # keep-alive
    server_session.when(
        if_heartbeat(), 'match-heartbeat'
    ).do(
        lambda s, data: heart_beats_received.append(data), 'record-heartbeat'
    ).do(
        send(Heartbeat()), 'send-server-heartbeat'
    )

    await asyncio.sleep((heart_beat_interval * 2) + 1)

    # At least one heartbeat should have been received.
    assert len(heart_beats_received) >= 1

    # Session should have been closed, since server heartbeats were not received.
    assert not session.is_closed()

    await session.close()
    assert session.is_closed()


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__active_message_flow__no_heartbeats_sent(mock_server_session, session_factory):
    port, server_session = mock_server_session
    heart_beats_received = []
    heart_beat_interval = 0.1

    server_session.when(
        if_logon("test_user"), 'match-login-request'
    ).do(
        send(EXP_LOGON_MSG), 'send-login-accept'
    )

    session = await fix.connect_async(
        ('127.0.0.1', port), ENTER_LOGIN_MSG,
        lambda : session_factory(
            client_heartbeat_interval=heart_beat_interval,
            server_heartbeat_interval=100
        )
    )

    # keep-alive
    server_session.when(
        if_heartbeat(), 'match-heartbeat'
    ).do(
        lambda s, data: heart_beats_received.append(data), 'record-heartbeat'
    )

    # Let client send messages.
    message_sender = asyncio.create_task(
        _keep_sending_messages(session, App(), 0.01)
    )

    await asyncio.sleep((heart_beat_interval * 2) + 1)

    # At least one heartbeat should have been received.
    assert len(heart_beats_received) == 0

    # Session should have been closed, since server heartbeats were not received.
    assert not session.is_closed()

    await session.close()
    assert session.is_closed()

    await stop_task(message_sender)


async def _keep_sending_messages(session, msg, timeout):
    try:
        while True:
            session.send_msg(msg)
            await asyncio.sleep(timeout)
    except:
        pass


HEADER = fix.MessageSegments.HEADER
BODY = fix.MessageSegments.BODY


def _wire(msg, begin_string='FIX.4.4'):
    data = bytearray(msg.to_bytes()[1])
    data[0:0] = fix.Field.from_tag_value(35, msg.Type).to_bytes()[1] + fix.SOH
    data[0:0] = fix.Field.from_tag_value(9, len(data)).to_bytes()[1] + fix.SOH
    data[0:0] = fix.Field.from_tag_value(8, begin_string).to_bytes()[1] + fix.SOH
    checksum = str(sum(data) % 256).rjust(3, '0')
    data.extend(fix.Field.from_tag_value(10, checksum).to_bytes()[1] + fix.SOH)
    return bytes(data)


def _server_msg(msg_cls, seq, *, header=None, body=None):
    hdr = {
        'SenderCompID': 'SERVER',
        'TargetCompID': 'CLIENT',
        'MsgSeqNum': seq,
        'SendingTime': '20241003-22:02:54',
    }
    hdr.update(header or {})
    return _wire(msg_cls({HEADER: hdr, BODY: body or {}}))


def if_msg_type(msg_type):
    def matcher(actual):
        return fix.Message.from_bytes(actual)[1].Type == msg_type
    return matcher


def _record(store):
    def action(_session, data):
        store.append(fix.Message.from_bytes(data)[1])
    return action


def _collector():
    received = []

    async def on_msg(msg):
        received.append(msg)

    return received, on_msg


def _client(session_factory, on_msg=None, **kwargs):
    params = dict(client_heartbeat_interval=100, server_heartbeat_interval=100)
    params.update(kwargs)
    if on_msg is not None:
        params['on_msg_coro'] = on_msg
    return lambda: session_factory(**params)


async def _wait_until(predicate, timeout=3.0):
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        if predicate():
            return True
        await asyncio.sleep(0.01)
    return predicate()


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__recovery__no_gap_messages_delivered_directly(mock_server_session, session_factory):
    port, server_session = mock_server_session
    received, on_msg = _collector()
    sent_resend = []

    server_session.when(if_logon('test_user'), 'login').do(
        send(EXP_LOGON_MSG), 'accept'
    ).do(
        send(_server_msg(App, 2)), 'app-2'
    ).do(
        send(_server_msg(App, 3)), 'app-3'
    )
    server_session.when(if_msg_type('2'), 'resend').do(_record(sent_resend), 'record-resend')

    session = await fix.connect_async(
        ('127.0.0.1', port), ENTER_LOGIN_MSG, _client(session_factory, on_msg)
    )

    assert await _wait_until(lambda: len(received) == 2)
    assert [m.Header.MsgSeqNum for m in received] == [2, 3]
    assert sent_resend == []

    await session.close()


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__recovery__gap_at_logon_sends_open_ended_resend(mock_server_session, session_factory):
    port, server_session = mock_server_session
    sent_resend = []

    logon_ahead = _server_msg(Login, 5, body={'Username': 'test_user'})
    server_session.when(if_logon('test_user'), 'login').do(send(logon_ahead), 'accept-ahead')
    server_session.when(if_msg_type('2'), 'resend').do(_record(sent_resend), 'record-resend')

    session = await fix.connect_async(
        ('127.0.0.1', port), ENTER_LOGIN_MSG, _client(session_factory, expected_seq_num=2)
    )

    assert not session.is_closed()
    assert await _wait_until(lambda: len(sent_resend) == 1)
    assert sent_resend[0].BeginSeqNo == 2
    assert sent_resend[0].EndSeqNo == 0

    await session.close()


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__recovery__racing_live_message_is_dropped_and_redelivered_by_replay(
        mock_server_session, session_factory):
    port, server_session = mock_server_session
    received, on_msg = _collector()

    logon_ahead = _server_msg(Login, 5, body={'Username': 'test_user'})
    server_session.when(if_logon('test_user'), 'login').do(
        send(logon_ahead), 'accept-ahead'
    ).do(
        send(_server_msg(App, 5)), 'racing-live-message'
    )
    server_session.when(if_msg_type('2'), 'resend').do(
        send(_server_msg(App, 2)), 'replay-2'
    ).do(
        send(_server_msg(App, 3)), 'replay-3'
    ).do(
        send(_server_msg(App, 4)), 'replay-4'
    ).do(
        send(_server_msg(App, 5, header={'PossDupFlag': True})), 'replay-5-dup-of-racer'
    )

    session = await fix.connect_async(
        ('127.0.0.1', port), ENTER_LOGIN_MSG, _client(session_factory, on_msg, expected_seq_num=2)
    )

    # the racing live message (seq=5) arrives before the replay and is dropped silently;
    # it is only delivered once the replay redelivers it in order.
    assert await _wait_until(lambda: len(received) == 4)
    assert [m.Header.MsgSeqNum for m in received] == [2, 3, 4, 5]
    assert session.expected_seq_num == 6

    await session.close()


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__recovery__gapfill_collapses_housekeeping_run(mock_server_session, session_factory):
    port, server_session = mock_server_session
    received, on_msg = _collector()

    logon_ahead = _server_msg(Login, 11, body={'Username': 'test_user'})
    server_session.when(if_logon('test_user'), 'login').do(send(logon_ahead), 'accept-ahead')
    server_session.when(if_msg_type('2'), 'resend').do(
        send(_server_msg(App, 2)), 'replay-2'
    ).do(
        send(_server_msg(App, 3)), 'replay-3'
    ).do(
        send(_server_msg(SequenceReset, 4, body={'GapFillFlag': True, 'NewSeqNo': 7})), 'collapse-heartbeats'
    ).do(
        send(_server_msg(App, 7)), 'replay-7'
    ).do(
        send(_server_msg(App, 8)), 'replay-8'
    ).do(
        send(_server_msg(App, 9)), 'replay-9'
    ).do(
        send(_server_msg(App, 10)), 'replay-10'
    )

    session = await fix.connect_async(
        ('127.0.0.1', port), ENTER_LOGIN_MSG, _client(session_factory, on_msg, expected_seq_num=2)
    )

    assert await _wait_until(lambda: len(received) == 6)
    assert [m.Header.MsgSeqNum for m in received] == [2, 3, 7, 8, 9, 10]
    assert session.expected_seq_num == 11

    await session.close()


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__recovery__possdup_below_expected_is_dropped(
        mock_server_session, session_factory):
    port, server_session = mock_server_session
    received, on_msg = _collector()
    sent_logout = []

    logon_ahead = _server_msg(Login, 5, body={'Username': 'test_user'})
    server_session.when(if_logon('test_user'), 'login').do(send(logon_ahead), 'accept-ahead')
    server_session.when(if_msg_type('2'), 'resend').do(
        send(_server_msg(App, 1, header={'PossDupFlag': True})), 'stale-duplicate'
    ).do(
        send(_server_msg(App, 2)), 'replay-2'
    ).do(
        send(_server_msg(App, 3)), 'replay-3'
    ).do(
        send(_server_msg(App, 4)), 'replay-4'
    )
    server_session.when(if_msg_type('5'), 'logout').do(_record(sent_logout), 'record-logout')

    session = await fix.connect_async(
        ('127.0.0.1', port), ENTER_LOGIN_MSG, _client(session_factory, on_msg, expected_seq_num=2)
    )

    assert await _wait_until(lambda: len(received) == 3)
    assert [m.Header.MsgSeqNum for m in received] == [2, 3, 4]
    assert sent_logout == []
    assert not session.is_closed()

    await session.close()


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__recovery__sequence_reset_without_gapfill_forces_expected(
        mock_server_session, session_factory):
    port, server_session = mock_server_session
    received, on_msg = _collector()

    logon_ahead = _server_msg(Login, 15, body={'Username': 'test_user'})
    server_session.when(if_logon('test_user'), 'login').do(send(logon_ahead), 'accept-ahead')
    server_session.when(if_msg_type('2'), 'resend').do(
        send(_server_msg(SequenceReset, 2, body={'NewSeqNo': 14})), 'reset'
    ).do(
        send(_server_msg(App, 14)), 'app-after-reset'
    )

    session = await fix.connect_async(
        ('127.0.0.1', port), ENTER_LOGIN_MSG, _client(session_factory, on_msg, expected_seq_num=2)
    )

    assert await _wait_until(lambda: len(received) == 1)
    assert [m.Header.MsgSeqNum for m in received] == [14]
    assert session.expected_seq_num == 15

    await session.close()


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__recovery__fatal_low_sequence_logs_out_and_closes(
        mock_server_session, session_factory):
    port, server_session = mock_server_session
    received, on_msg = _collector()
    sent_logout = []

    logon_ahead = _server_msg(Login, 5, body={'Username': 'test_user'})
    server_session.when(if_logon('test_user'), 'login').do(send(logon_ahead), 'accept-ahead')
    server_session.when(if_msg_type('2'), 'resend').do(
        send(_server_msg(App, 1)), 'fatal-low'
    )
    server_session.when(if_msg_type('5'), 'logout').do(_record(sent_logout), 'record-logout')

    session = await fix.connect_async(
        ('127.0.0.1', port), ENTER_LOGIN_MSG, _client(session_factory, on_msg, expected_seq_num=2)
    )

    assert await _wait_until(lambda: len(sent_logout) >= 1)
    assert await _wait_until(session.is_closed)
    assert received == []


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__recovery__test_request_during_replay_answered_with_heartbeat(
        mock_server_session, session_factory):
    port, server_session = mock_server_session
    sent_heartbeats = []

    logon_ahead = _server_msg(Login, 5, body={'Username': 'test_user'})
    server_session.when(if_logon('test_user'), 'login').do(send(logon_ahead), 'accept-ahead')
    server_session.when(if_msg_type('2'), 'resend').do(
        send(_server_msg(App, 2)), 'replay-2'
    ).do(
        send(_server_msg(TestRequest, 3, body={'TestReqID': 'PING-1'})), 'replay-test-request'
    ).do(
        send(_server_msg(App, 4)), 'replay-4'
    )
    server_session.when(if_heartbeat(), 'heartbeat').do(_record(sent_heartbeats), 'record-heartbeat')

    session = await fix.connect_async(
        ('127.0.0.1', port), ENTER_LOGIN_MSG, _client(session_factory, expected_seq_num=2)
    )

    assert await _wait_until(lambda: any(hb.TestReqID == 'PING-1' for hb in sent_heartbeats))
    assert await _wait_until(lambda: session.expected_seq_num == 5)

    await session.close()


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__send_msg__explicit_seq_num_does_not_advance_counter(mock_server_session, session_factory):
    port, server_session = mock_server_session
    sent = []

    server_session.when(if_logon('test_user'), 'login').do(send(EXP_LOGON_MSG), 'accept')
    server_session.when(if_msg_type('D'), 'app').do(_record(sent), 'record-app')

    session = await fix.connect_async(
        ('127.0.0.1', port), ENTER_LOGIN_MSG, _client(session_factory)
    )

    session.send_msg(App())
    await asyncio.sleep(0.05)
    session.send_msg(App(), seq_num=99)
    await asyncio.sleep(0.05)
    session.send_msg(App())

    assert await _wait_until(lambda: len(sent) == 3)
    a1, explicit, a2 = [m.Header.MsgSeqNum for m in sent]
    assert explicit == 99
    assert a2 == a1 + 1

    await session.close()


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__send_msg__poss_dup_sets_flags(mock_server_session, session_factory):
    port, server_session = mock_server_session
    sent = []

    server_session.when(if_logon('test_user'), 'login').do(send(EXP_LOGON_MSG), 'accept')
    server_session.when(if_msg_type('D'), 'app').do(_record(sent), 'record-app')

    session = await fix.connect_async(
        ('127.0.0.1', port), ENTER_LOGIN_MSG, _client(session_factory)
    )

    session.send_msg(App(), poss_dup=True)

    assert await _wait_until(lambda: len(sent) == 1)
    msg = sent[0]
    assert msg.Header.PossDupFlag is True
    assert msg.Header.OrigSendingTime
    assert msg.Header.OrigSendingTime == msg.Header.SendingTime

    await session.close()


@pytest.fixture(autouse=True)
def _restore_fix_message_registry():
    for msg_cls in (Login, Heartbeat, Nope, TestRequest, ResendRequest, SequenceReset, Logout, App):
        fix.Message.Def[msg_cls.Type] = msg_cls
        fix.Message.Def[msg_cls.Name] = msg_cls
    yield


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__on_message__in_sequence_message_is_queued(session_factory):
    session = session_factory()
    session._login_pending = False
    session.expected_seq_num = 3

    msg = fix.Message.from_bytes(_server_msg(App, 3))[1]
    await session.on_message(msg)

    assert session.expected_seq_num == 4
    queued = await session.receive_msg()
    assert queued.Header.MsgSeqNum == 3


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__on_message__ahead_message_is_dropped_not_queued(session_factory):
    session = session_factory()
    session._login_pending = False
    session.expected_seq_num = 3

    msg = fix.Message.from_bytes(_server_msg(App, 5))[1]
    await session.on_message(msg)

    assert session.expected_seq_num == 3
    assert session._msg_queue.get_nowait() is None


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__on_message__login_pending_bypasses_sequence_check(session_factory):
    session = session_factory()
    session.expected_seq_num = None

    logon_resp = fix.Message.from_bytes(_server_msg(Login, 99, body={'Username': 'test_user'}))[1]
    await session.on_message(logon_resp)

    assert session.expected_seq_num is None
    queued = await session.receive_msg()
    assert queued.Header.MsgSeqNum == 99


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__handle_sequence_reset__forces_expected_to_new_seq_no(session_factory):
    session = session_factory()
    session.expected_seq_num = 7
    session._handle_sequence_reset(SequenceReset({fix.MessageSegments.BODY: {'NewSeqNo': 20}}))
    assert session.expected_seq_num == 20


@pytest.mark.parametrize('session_factory', [Fix44Session, Fix50Session])
async def test__fix_session__start_dispatching__no_op_without_on_msg_coro(session_factory):
    session = session_factory()
    session._login_pending = False
    session.expected_seq_num = 3

    session.start_dispatching()

    msg = fix.Message.from_bytes(_server_msg(App, 3))[1]
    await session.on_message(msg)

    received = await session.receive_msg()
    assert received.Header.MsgSeqNum == 3

