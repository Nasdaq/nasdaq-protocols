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
        _keep_sending_messages(session, ENTER_LOGIN_MSG, 0.01)
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
