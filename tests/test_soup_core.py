import logging

import pytest
from nasdaq_protocols import soup


logger = logging.getLogger(__name__)
test_login_reject = b'\x00/Lnousernopasswordsession   1                   '
test_login_accepted = b'\x00\x1fAtest      2                   '
test_login_rejected = b'\x00\x02JA'
test_login_rejected_session = b'\x00\x02JS'
test_debug = b'\x00\t+test_txt'
test_sequenced = b'\x00\tStest_txt'
test_unsequenced = b'\x00\tUtest_txt'
client_heartbeat_message = b'\x00\x01R'
server_heartbeat_message = b'\x00\x01H'
end_of_session_message = b'\x00\x01Z'
logout_request_message = b'\x00\x01O'


def test_login_rejected_reason():
    assert soup.LoginRejectReason.NOT_AUTHORIZED == soup.LoginRejectReason.get('A')
    assert soup.LoginRejectReason.SESSION_NOT_AVAILABLE == soup.LoginRejectReason.get('S')


def test_unpack_unknown_soup_message():
    test_message = b'\x00\x02>'
    with pytest.raises(soup.InvalidSoupMessage):
        soup.SoupMessage.from_bytes(test_message)


def test_unpack_invalid_soup_message():
    test_message = b'\x00'
    with pytest.raises(soup.InvalidSoupMessage):
        soup.SoupMessage.from_bytes(test_message)


def test_pack_login_request():
    input_lr = soup.LoginRequest('nouser', 'nopassword', 'session', '1')
    _len, bytes_ = input_lr.to_bytes()

    assert test_login_reject == bytes_


def test_unpack_login_request():
    _len, message = soup.SoupMessage.from_bytes(test_login_reject)

    assert type(message) is soup.LoginRequest
    assert message.Indicator == 'L'
    assert message.user == 'nouser'
    assert message.password == 'nopassword'
    assert message.session == 'session'
    assert message.sequence == '1'
    str_ = repr(message)
    assert 'nopassword' not in str_
    assert not message.is_logout()
    assert not message.is_heartbeat()


def test_pack_login_accepted():
    input_la = soup.LoginAccepted('test', 2)
    _len, bytes_ = input_la.to_bytes()

    assert test_login_accepted == bytes_


def test_unpack_login_accepted():
    _len, message = soup.SoupMessage.from_bytes(test_login_accepted)

    assert type(message) is soup.LoginAccepted
    assert message.Indicator == 'A'
    assert message.session_id == 'test'
    assert message.sequence == 2
    assert not message.is_logout()
    assert not message.is_heartbeat()


def test_pack_login_rejected():
    input_lra = soup.LoginRejected(soup.LoginRejectReason.NOT_AUTHORIZED)
    input_lrs = soup.LoginRejected(soup.LoginRejectReason.SESSION_NOT_AVAILABLE)
    _len, input_lra_bytes = input_lra.to_bytes()
    _len, input_lrs_bytes = input_lrs.to_bytes()

    assert test_login_rejected == input_lra_bytes
    assert test_login_rejected_session == input_lrs_bytes


def test_unpack_login_rejected_auth():
    _len, message = soup.SoupMessage.from_bytes(test_login_rejected)

    assert type(message) is soup.LoginRejected
    assert message.Indicator == 'J'
    assert message.reason == soup.LoginRejectReason.NOT_AUTHORIZED
    assert not message.is_logout()
    assert not message.is_heartbeat()


def test_unpack_login_rejected_session():
    _len, message = soup.SoupMessage.from_bytes(test_login_rejected_session)

    assert type(message) is soup.LoginRejected
    assert message.Indicator == 'J'
    assert message.reason == soup.LoginRejectReason.SESSION_NOT_AVAILABLE
    assert not message.is_logout()
    assert not message.is_heartbeat()


def test_pack_sequenced_data():
    input_sd = soup.SequencedData(b'test_txt')
    _len, bytes_ = input_sd.to_bytes()

    assert test_sequenced == bytes_


def test_unpack_sequenced_data():
    _len, message = soup.SoupMessage.from_bytes(test_sequenced)

    assert type(message) is soup.SequencedData
    assert message.Indicator == 'S'
    assert message.data == b'test_txt'
    assert not message.is_logout()
    assert not message.is_heartbeat()


def test_pack_empty_sequence_data():
    input_sd = soup.SequencedData(b'')
    _len, bytes_ = input_sd.to_bytes()

    assert b'\x00\x01S' == bytes_


def test_unpack_empty_sequence_data():
    _len, message = soup.SoupMessage.from_bytes(b'\x00\x01S')

    assert type(message) is soup.SequencedData
    assert message.Indicator == 'S'
    assert message.data == b''
    assert not message.is_logout()
    assert not message.is_heartbeat()


def test_pack_unsequenced_data():
    input_usd = soup.UnSequencedData(b'test_txt')
    _len, bytes_ = input_usd.to_bytes()

    assert test_unsequenced == bytes_


def test_unpack_unsequenced_data():
    _len, message = soup.SoupMessage.from_bytes(test_unsequenced)

    assert type(message) is soup.UnSequencedData
    assert message.Indicator == 'U'
    assert message.data == b'test_txt'
    assert not message.is_logout()
    assert not message.is_heartbeat()


def test_pack_empty_unsequenced_data():
    input_usd = soup.UnSequencedData(b'')
    _len, bytes_ = input_usd.to_bytes()

    assert b'\x00\x01U' == bytes_


def test_unpack_empty_unsequenced_data():
    _len, message = soup.SoupMessage.from_bytes(b'\x00\x01U')

    assert type(message) is soup.UnSequencedData
    assert message.Indicator == 'U'
    assert message.data == b''
    assert not message.is_logout()
    assert not message.is_heartbeat()


def test_pack_debug():
    input_d = soup.Debug('test_txt')
    _len, bytes_ = input_d.to_bytes()

    assert test_debug == bytes_


def test_unpack_debug():
    _len, message = soup.SoupMessage.from_bytes(test_debug)

    assert type(message) is soup.Debug
    assert message.Indicator == '+'
    assert message.msg == 'test_txt'
    assert not message.is_logout()
    assert not message.is_heartbeat()


def test_pack_client_heartbeat():
    _len, bytes_ = soup.ClientHeartbeat().to_bytes()
    assert client_heartbeat_message == bytes_


def test_unpack_client_heartbeat():
    _len, message = soup.SoupMessage.from_bytes(client_heartbeat_message)

    assert type(message) is soup.ClientHeartbeat
    assert message.Indicator == 'R'
    assert message.is_heartbeat()
    assert not message.is_logout()


def test_pack_server_heartbeat():
    _len, bytes_ = soup.ServerHeartbeat().to_bytes()
    assert server_heartbeat_message == bytes_


def test_unpack_server_heartbeat():
    _len, message = soup.SoupMessage.from_bytes(server_heartbeat_message)

    assert type(message) is soup.ServerHeartbeat
    assert message.Indicator == 'H'
    assert message.is_heartbeat()
    assert not message.is_logout()


def test_pack_end_of_session():
    _len, bytes_ = soup.EndOfSession().to_bytes()
    assert end_of_session_message == bytes_


def test_unpack_end_of_session():
    _len, message = soup.SoupMessage.from_bytes(end_of_session_message)

    assert type(message) is soup.EndOfSession
    assert message.Indicator == 'Z'
    assert message.is_logout()
    assert not message.is_heartbeat()


def test_pack_logout_request():
    _len, bytes_ = soup.LogoutRequest().to_bytes()
    assert logout_request_message == bytes_


def test_unpack_logout_request():
    _len, message = soup.SoupMessage.from_bytes(logout_request_message)

    assert type(message) is soup.LogoutRequest
    assert message.Indicator == 'O'
    assert message.is_logout()
    assert not message.is_heartbeat()


def test_unpack_invalid_logout_request():
    with pytest.raises(soup.InvalidSoupMessage):
        soup.SoupMessage.from_bytes(b'\x00\x01O\x00')


def test_unpack_invalid_logout_request_2():
    with pytest.raises(soup.InvalidSoupMessage):
        soup.SoupMessage.from_bytes(b'\x00\x01O\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
