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
test_un_sequenced = b'\x00\tUtest_txt'
client_heartbeat_message = b'\x00\x01R'
server_heartbeat_message = b'\x00\x01H'
end_of_session_message = b'\x00\x01Z'
logout_request_message = b'\x00\x01O'


def test__login_rejected__reason():
    assert soup.LoginRejectReason.NOT_AUTHORIZED == soup.LoginRejectReason.get('A')
    assert soup.LoginRejectReason.SESSION_NOT_AVAILABLE == soup.LoginRejectReason.get('S')


def test__soup_message__unpack_unknown_soup_message__exception_is_raised():
    test_message = b'\x00\x02>'
    with pytest.raises(soup.InvalidSoupMessage):
        soup.SoupMessage.from_bytes(test_message)


def test__soup_message__unpack_invalid_soup_message__exception_is_raised():
    test_message = b'\x00'
    with pytest.raises(soup.InvalidSoupMessage):
        soup.SoupMessage.from_bytes(test_message)


def test__login_request__to_bytes():
    input_lr = soup.LoginRequest('nouser', 'nopassword', 'session', '1')
    _len, bytes_ = input_lr.to_bytes()

    assert test_login_reject == bytes_


def test__login_request__from_bytes():
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


def test__login_accepted__to_bytes():
    input_la = soup.LoginAccepted('test', 2)
    _len, bytes_ = input_la.to_bytes()

    assert test_login_accepted == bytes_


def test__login_accepted__from_bytes():
    _len, message = soup.SoupMessage.from_bytes(test_login_accepted)

    assert type(message) is soup.LoginAccepted
    assert message.Indicator == 'A'
    assert message.session_id == 'test'
    assert message.sequence == 2
    assert not message.is_logout()
    assert not message.is_heartbeat()


def test__login_rejected__to_bytes():
    input_lra = soup.LoginRejected(soup.LoginRejectReason.NOT_AUTHORIZED)
    input_lrs = soup.LoginRejected(soup.LoginRejectReason.SESSION_NOT_AVAILABLE)
    _len, input_lra_bytes = input_lra.to_bytes()
    _len, input_lrs_bytes = input_lrs.to_bytes()

    assert test_login_rejected == input_lra_bytes
    assert test_login_rejected_session == input_lrs_bytes


def test__login_rejected_auth__from_bytes():
    _len, message = soup.SoupMessage.from_bytes(test_login_rejected)

    assert type(message) is soup.LoginRejected
    assert message.Indicator == 'J'
    assert message.reason == soup.LoginRejectReason.NOT_AUTHORIZED
    assert not message.is_logout()
    assert not message.is_heartbeat()


def test__login_rejected_session__from_bytes():
    _len, message = soup.SoupMessage.from_bytes(test_login_rejected_session)

    assert type(message) is soup.LoginRejected
    assert message.Indicator == 'J'
    assert message.reason == soup.LoginRejectReason.SESSION_NOT_AVAILABLE
    assert not message.is_logout()
    assert not message.is_heartbeat()


def test__sequenced_data__to_bytes():
    input_sd = soup.SequencedData(b'test_txt')
    _len, bytes_ = input_sd.to_bytes()

    assert test_sequenced == bytes_


def test__sequenced_data__from_bytes():
    _len, message = soup.SoupMessage.from_bytes(test_sequenced)

    assert type(message) is soup.SequencedData
    assert message.Indicator == 'S'
    assert message.data == b'test_txt'
    assert not message.is_logout()
    assert not message.is_heartbeat()


def test__sequenced_data__empty_message__to_bytes():
    input_sd = soup.SequencedData(b'')
    _len, bytes_ = input_sd.to_bytes()

    assert b'\x00\x01S' == bytes_


def test__sequence_data__empty_message__from_bytes():
    _len, message = soup.SoupMessage.from_bytes(b'\x00\x01S')

    assert type(message) is soup.SequencedData
    assert message.Indicator == 'S'
    assert message.data == b''
    assert not message.is_logout()
    assert not message.is_heartbeat()


def test__un_sequenced_data__to_bytes():
    input_usd = soup.UnSequencedData(b'test_txt')
    _len, bytes_ = input_usd.to_bytes()

    assert test_un_sequenced == bytes_


def test__unsequenced_data__from_bytes():
    _len, message = soup.SoupMessage.from_bytes(test_un_sequenced)

    assert type(message) is soup.UnSequencedData
    assert message.Indicator == 'U'
    assert message.data == b'test_txt'
    assert not message.is_logout()
    assert not message.is_heartbeat()


def test__un_sequenced_data__empty_message__to_bytes():
    input_usd = soup.UnSequencedData(b'')
    _len, bytes_ = input_usd.to_bytes()

    assert b'\x00\x01U' == bytes_


def test__unsequenced_data__empty_message__from_bytes():
    _len, message = soup.SoupMessage.from_bytes(b'\x00\x01U')

    assert type(message) is soup.UnSequencedData
    assert message.Indicator == 'U'
    assert message.data == b''
    assert not message.is_logout()
    assert not message.is_heartbeat()


def test__debug__to_bytes():
    input_d = soup.Debug('test_txt')
    _len, bytes_ = input_d.to_bytes()

    assert test_debug == bytes_


def test__debug__from_bytes():
    _len, message = soup.SoupMessage.from_bytes(test_debug)

    assert type(message) is soup.Debug
    assert message.Indicator == '+'
    assert message.msg == 'test_txt'
    assert not message.is_logout()
    assert not message.is_heartbeat()


def test__client_heartbeat__to_bytes():
    _len, bytes_ = soup.ClientHeartbeat().to_bytes()
    assert client_heartbeat_message == bytes_


def test__client_heartbeat__from_bytes():
    _len, message = soup.SoupMessage.from_bytes(client_heartbeat_message)

    assert type(message) is soup.ClientHeartbeat
    assert message.Indicator == 'R'
    assert message.is_heartbeat()
    assert not message.is_logout()


def test__server_heartbeat__to_bytes():
    _len, bytes_ = soup.ServerHeartbeat().to_bytes()
    assert server_heartbeat_message == bytes_


def test__server_heartbeat__from_bytes():
    _len, message = soup.SoupMessage.from_bytes(server_heartbeat_message)

    assert type(message) is soup.ServerHeartbeat
    assert message.Indicator == 'H'
    assert message.is_heartbeat()
    assert not message.is_logout()


def test__end_of_session__to_bytes():
    _len, bytes_ = soup.EndOfSession().to_bytes()
    assert end_of_session_message == bytes_


def test__end_of_session__from_bytes():
    _len, message = soup.SoupMessage.from_bytes(end_of_session_message)

    assert type(message) is soup.EndOfSession
    assert message.Indicator == 'Z'
    assert message.is_logout()
    assert not message.is_heartbeat()


def test__logout_request__to_bytes():
    _len, bytes_ = soup.LogoutRequest().to_bytes()
    assert logout_request_message == bytes_


def test__logout_request__from_bytes():
    _len, message = soup.SoupMessage.from_bytes(logout_request_message)

    assert type(message) is soup.LogoutRequest
    assert message.Indicator == 'O'
    assert message.is_logout()
    assert not message.is_heartbeat()


def test__logout_request__invalid_message__from_bytes():
    with pytest.raises(soup.InvalidSoupMessage):
        soup.SoupMessage.from_bytes(b'\x00\x01O\x00')


def test__logout_request__invalid_message2__from_bytes():
    with pytest.raises(soup.InvalidSoupMessage):
        soup.SoupMessage.from_bytes(b'\x00\x01O\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
