import pytest

from nasdaq_protocols.fix import *


def test__fix_bool__to_str():
    assert types.FixBool.to_str(True) == 'Y'
    assert types.FixBool.to_str(False) == 'N'


def test__fix_bool__from_str():
    assert types.FixBool.from_str('Y') is True
    assert types.FixBool.from_str('y') is True
    assert types.FixBool.from_str('N') is False
    assert types.FixBool.from_str('n') is False
    assert types.FixBool.from_str('something') is False


def test__fix_bool__to_bytes():
    assert types.FixBool.to_bytes(True) == (1, b'Y')
    assert types.FixBool.to_bytes(False) == (1, b'N')


def test__fix_bool__from_bytes():
    assert types.FixBool.from_bytes(b'Y') == (1, True)
    assert types.FixBool.from_bytes(b'N') == (1, False)
    assert types.FixBool.from_bytes(b'invalid') == (len('invalid'), False)


def test__fix_string__to_str():
    assert types.FixString.to_str('test') == 'test'


def test__fix_string__from_str():
    assert types.FixString.from_str('test') == 'test'


def test__fix_string__to_bytes():
    assert FixString.to_bytes('test') == (len('test'), b'test')
    assert FixString.to_bytes('t') == (len('t'), b't')


def test__fix_string__from_bytes():
    assert FixString.from_bytes(b'test') == (len('test'), 'test')
    assert FixString.from_bytes(b't') == (1, 't')


def test__fix_int__to_str():
    assert FixInt.to_str(0) == '0'
    assert FixInt.to_str(1) == '1'
    assert FixInt.to_str(12345) == '12345'


def test__fix_int__from_str():
    assert FixInt.from_str('0') == 0
    assert FixInt.from_str('1') == 1
    assert FixInt.from_str('12345') == 12345


def test__fix_int__to_bytes():
    assert FixInt.to_bytes(0) == (1, b'0')
    assert FixInt.to_bytes(1) == (1, b'1')
    assert FixInt.to_bytes(12345) == (5, b'12345')


def test__fix_int__from_bytes():
    assert FixInt.from_bytes(b'0') == (1, 0)
    assert FixInt.from_bytes(b'1') == (1, 1)
    assert FixInt.from_bytes(b'12345') == (5, 12345)
    with pytest.raises(ValueError):
        assert FixInt.from_bytes(b'a')


##
def test__fix_float__to_str():
    assert FixFloat.to_str(0.1) == '0.1'
    assert FixFloat.to_str(1.0) == '1.0'
    assert FixFloat.to_str(12.345) == '12.345'


def test__fix_float__from_str():
    assert FixFloat.from_str('0.1') == 0.1
    assert FixFloat.from_str('1.0') == 1.0
    assert FixFloat.from_str('12.345') == 12.345


def test__fix_float__to_bytes():
    assert FixFloat.to_bytes(0.1) == (3, b'0.1')
    assert FixFloat.to_bytes(1.0) == (3, b'1.0')
    assert FixFloat.to_bytes(12.345) == (6, b'12.345')
    assert FixFloat.to_bytes(1) == (1, b'1')


def test__fix_float__from_bytes():
    assert FixFloat.from_bytes(b'0.1') == (3, 0.1)
    assert FixFloat.from_bytes(b'1.0') == (3, 1.0)
    assert FixFloat.from_bytes(b'12.345') == (6, 12.345)
    assert FixFloat.from_bytes(b'2') == (1, 2.0)
    with pytest.raises(ValueError):
        assert FixFloat.from_bytes(b'a')
