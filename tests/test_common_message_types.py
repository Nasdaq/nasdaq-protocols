import string

import pytest
from nasdaq_protocols.common import types


BYTES_456 = b'\xc8\x01\x00\x00'
BYTES_0 = b'\x00\x00\x00\x00'
BYTES_NEG_456 = b'\x38\xfe\xff\xff'
SHORT_BYTES_456 = b'\xc8\x01'
SHORT_BYTES_0 = b'\x00\x00'
SHORT_BYTES_NEG_456 = b'\x38\xfe'
LONG_BYTES_456 = b'\xc8\x01\x00\x00\x00\x00\x00\x00'
LONG_BYTES_0 = b'\x00\x00\x00\x00\x00\x00\x00\x00'
LONG_BYTES_NEG_456 = b'\x38\xfe\xff\xff\xff\xff\xff\xff'
SIGNED_INT_TYPES = [
    types.Int,
    types.IntBE,
    types.Short,
    types.ShortBE,
    types.Long,
    types.LongBE
]
UNSIGNED_INT_TYPES = [
    types.UnsignedInt,
    types.UnsignedIntBE,
    types.UnsignedShort,
    types.UnsignedShortBE,
    types.UnsignedLong,
    types.UnsignedLongBE
]
INT_TYPES = SIGNED_INT_TYPES + UNSIGNED_INT_TYPES
ALL_ASCII = [(_, _.encode('ascii')) for _ in string.printable]
NON_ASCII = [('ß', b'\xdf')]


def test__boolean__to_str():
    assert types.Boolean.to_str(True) == 'True'
    assert types.Boolean.to_str(False) == 'False'


def test__boolean__from_str():
    assert types.Boolean.from_str('True') is True
    assert types.Boolean.from_str('False') is False


def test__boolean__to_bytes():
    assert types.Boolean.to_bytes(True) == (1, b'\x01')
    assert types.Boolean.to_bytes(False) == (1, b'\x00')


def test__boolean__from_bytes():
    assert types.Boolean.from_bytes(b'\x01') == (1, True)
    assert types.Boolean.from_bytes(b'\x00') == (1, False)


def test__byte__to_str():
    assert types.Byte.to_str(0) == '0'
    assert types.Byte.to_str(255) == '255'


def test__byte__from_str():
    assert types.Byte.from_str('0') == 0
    assert types.Byte.from_str('255') == 255


def test__byte__to_bytes():
    assert types.Byte.to_bytes(0) == (1, b'\x00')
    assert types.Byte.to_bytes(255) == (1, b'\xff')


def test__byte__from_bytes():
    assert types.Byte.from_bytes(b'\x00') == (1, 0)
    assert types.Byte.from_bytes(b'\xff') == (1, 255)


def test__int__to_str():
    for type_ in INT_TYPES:
        assert type_.to_str(456) == '456'
        assert type_.to_str(0) == '0'
        assert type_.to_str(-456) == '-456'


def test__int__from_str():
    for type_ in INT_TYPES:
        assert type_.from_str('456') == 456
        assert type_.from_str('0') == 0
        assert type_.from_str('-456') == -456


def test__int__to_bytes():
    assert types.Short.to_bytes(456) == (2, SHORT_BYTES_456)
    assert types.Short.to_bytes(0) == (2, SHORT_BYTES_0)
    assert types.Short.to_bytes(-456) == (2, SHORT_BYTES_NEG_456)
    assert types.UnsignedShort.to_bytes(0) == (2, SHORT_BYTES_0)
    assert types.UnsignedShort.to_bytes(456) == (2, SHORT_BYTES_456)

    assert types.ShortBE.to_bytes(456) == (2, SHORT_BYTES_456[::-1])
    assert types.ShortBE.to_bytes(0) == (2, SHORT_BYTES_0[::-1])
    assert types.ShortBE.to_bytes(-456) == (2, SHORT_BYTES_NEG_456[::-1])
    assert types.UnsignedShortBE.to_bytes(0) == (2, SHORT_BYTES_0[::-1])
    assert types.UnsignedShortBE.to_bytes(456) == (2, SHORT_BYTES_456[::-1])

    assert types.Int.to_bytes(456) == (4, BYTES_456)
    assert types.Int.to_bytes(0) == (4, BYTES_0)
    assert types.Int.to_bytes(-456) == (4, BYTES_NEG_456)
    assert types.UnsignedInt.to_bytes(456) == (4, BYTES_456)
    assert types.UnsignedInt.to_bytes(0) == (4, BYTES_0)

    assert types.IntBE.to_bytes(456) == (4, BYTES_456[::-1])
    assert types.IntBE.to_bytes(0) == (4, BYTES_0[::-1])
    assert types.IntBE.to_bytes(-456) == (4, BYTES_NEG_456[::-1])
    assert types.UnsignedIntBE.to_bytes(456) == (4, BYTES_456[::-1])
    assert types.UnsignedIntBE.to_bytes(0) == (4, BYTES_0[::-1])

    assert types.Long.to_bytes(456) == (8, LONG_BYTES_456)
    assert types.Long.to_bytes(0) == (8, LONG_BYTES_0)
    assert types.Long.to_bytes(-456) == (8, LONG_BYTES_NEG_456)
    assert types.UnsignedLong.to_bytes(456) == (8, LONG_BYTES_456)
    assert types.UnsignedLong.to_bytes(0) == (8, LONG_BYTES_0)

    assert types.LongBE.to_bytes(456) == (8, LONG_BYTES_456[::-1])
    assert types.LongBE.to_bytes(0) == (8, LONG_BYTES_0[::-1])
    assert types.LongBE.to_bytes(-456) == (8, LONG_BYTES_NEG_456[::-1])
    assert types.UnsignedLongBE.to_bytes(456) == (8, LONG_BYTES_456[::-1])
    assert types.UnsignedLongBE.to_bytes(0) == (8, LONG_BYTES_0[::-1])

    for type_ in UNSIGNED_INT_TYPES:
        with pytest.raises(OverflowError):
            type_.to_bytes(-456)


def test__int__from_bytes():
    assert types.Short.from_bytes(SHORT_BYTES_456) == (2, 456)
    assert types.Short.from_bytes(SHORT_BYTES_0) == (2, 0)
    assert types.Short.from_bytes(SHORT_BYTES_NEG_456) == (2, -456)
    assert types.UnsignedShort.from_bytes(SHORT_BYTES_0) == (2, 0)
    assert types.UnsignedShort.from_bytes(SHORT_BYTES_456) == (2, 456)

    assert types.ShortBE.from_bytes(SHORT_BYTES_456[::-1]) == (2, 456)
    assert types.ShortBE.from_bytes(SHORT_BYTES_0[::-1]) == (2, 0)
    assert types.ShortBE.from_bytes(SHORT_BYTES_NEG_456[::-1]) == (2, -456)
    assert types.UnsignedShortBE.from_bytes(SHORT_BYTES_0[::-1]) == (2, 0)
    assert types.UnsignedShortBE.from_bytes(SHORT_BYTES_456[::-1]) == (2, 456)

    assert types.Int.from_bytes(BYTES_456) == (4, 456)
    assert types.Int.from_bytes(BYTES_0) == (4, 0)
    assert types.Int.from_bytes(BYTES_NEG_456) == (4, -456)
    assert types.UnsignedInt.from_bytes(BYTES_0) == (4, 0)
    assert types.UnsignedInt.from_bytes(BYTES_456) == (4, 456)

    assert types.IntBE.from_bytes(BYTES_456[::-1]) == (4, 456)
    assert types.IntBE.from_bytes(BYTES_0[::-1]) == (4, 0)
    assert types.IntBE.from_bytes(BYTES_NEG_456[::-1]) == (4, -456)
    assert types.UnsignedIntBE.from_bytes(BYTES_0[::-1]) == (4, 0)
    assert types.UnsignedIntBE.from_bytes(BYTES_456[::-1]) == (4, 456)

    assert types.Long.from_bytes(LONG_BYTES_456) == (8, 456)
    assert types.Long.from_bytes(LONG_BYTES_0) == (8, 0)
    assert types.Long.from_bytes(LONG_BYTES_NEG_456) == (8, -456)
    assert types.UnsignedLong.from_bytes(LONG_BYTES_0) == (8, 0)
    assert types.UnsignedLong.from_bytes(LONG_BYTES_456) == (8, 456)

    assert types.LongBE.from_bytes(LONG_BYTES_456[::-1]) == (8, 456)
    assert types.LongBE.from_bytes(LONG_BYTES_0[::-1]) == (8, 0)
    assert types.LongBE.from_bytes(LONG_BYTES_NEG_456[::-1]) == (8, -456)
    assert types.UnsignedLongBE.from_bytes(LONG_BYTES_0[::-1]) == (8, 0)
    assert types.UnsignedLongBE.from_bytes(LONG_BYTES_456[::-1]) == (8, 456)

    assert types.Short.from_bytes(SHORT_BYTES_456) != (2, 0)
    assert types.UnsignedInt.from_bytes(BYTES_NEG_456) != (4, -456)
    assert types.Long.from_bytes(LONG_BYTES_456) != (8, -456)


def test__int__boundary_conditions():
    test_data = [
        (types.Byte, 256),
        (types.UnsignedShort, 65536),
        (types.Short, 32768),
        (types.UnsignedShortBE, 65536),
        (types.ShortBE, 32768),
        (types.UnsignedInt, 4294967296),
        (types.Int, 2147483648),
        (types.UnsignedIntBE, 4294967296),
        (types.IntBE, 2147483648),
        (types.UnsignedLong, 18446744073709551616),
        (types.Long, 9223372036854775808),
        (types.UnsignedLongBE, 18446744073709551616),
        (types.LongBE, 9223372036854775808)
    ]
    for type_, value in test_data:
        with pytest.raises(OverflowError):
            type_.to_bytes(value)


def test__char_ascii__all_methods():
    for char, byte_ in ALL_ASCII:
        assert types.CharAscii.to_str(char) == char
        assert types.CharAscii.from_str(char) == char
        assert types.CharAscii.to_bytes(char) == (1, byte_)
        assert types.CharAscii.from_bytes(byte_) == (1, char)

    for char, byte_ in NON_ASCII:
        with pytest.raises(ValueError):
            types.CharAscii.to_bytes(char)
        with pytest.raises(ValueError):
            types.CharAscii.from_bytes(byte_)


def test__char_iso8599__all_methods():
    for char, byte_ in ALL_ASCII:
        assert types.CharIso8599.to_str(char) == char
        assert types.CharIso8599.from_str(char) == char
        assert types.CharIso8599.to_bytes(char) == (1, byte_)
        assert types.CharIso8599.from_bytes(byte_) == (1, char)

    for char, byte_ in NON_ASCII:
        assert types.CharIso8599.from_bytes(byte_) == (1, char)
        assert types.CharIso8599.to_bytes(char) == (1, byte_)


def test__ascii_string__all_methods():
    ascii_string = ''.join([_[0] for _ in ALL_ASCII])
    ascii_bytes = len(ascii_string).to_bytes(2, 'little') + b''.join([_[1] for _ in ALL_ASCII])

    assert types.AsciiString.to_str(ascii_string) == ascii_string
    assert types.AsciiString.from_str(ascii_string) == ascii_string
    assert types.AsciiString.to_bytes(ascii_string) == (len(ascii_string) + 2, ascii_bytes)
    assert types.AsciiString.from_bytes(ascii_bytes) == (len(ascii_string) + 2, ascii_string)

    ascii_string_with_len_5 = types.FixedAsciiString(length=5)
    assert ascii_string_with_len_5.to_str('abcde') == 'abcde'
    assert ascii_string_with_len_5.from_str('abcde') == 'abcde'
    assert ascii_string_with_len_5.to_bytes('abcde') == (5, b'abcde')
    assert ascii_string_with_len_5.from_bytes(b'abcde') == (5, 'abcde')


def test__non_ascii_string__all_methods():
    non_ascii_string = 'ß' * 5
    non_ascii_bytes = len(non_ascii_string).to_bytes(2, 'little') + b'\xdf' * 5

    assert types.Iso8859String.to_str(non_ascii_string) == non_ascii_string
    assert types.Iso8859String.from_str(non_ascii_string) == non_ascii_string
    assert types.Iso8859String.to_bytes(non_ascii_string) == (len(non_ascii_string) + 2, non_ascii_bytes)
    assert types.Iso8859String.from_bytes(non_ascii_bytes) == (len(non_ascii_string) + 2, non_ascii_string)

    non_ascii_string_with_len_5 = types.FixedIsoString(length=5)
    assert non_ascii_string_with_len_5.to_str('ßßßßß') == 'ßßßßß'
    assert non_ascii_string_with_len_5.from_str('ßßßßß') == 'ßßßßß'
    assert non_ascii_string_with_len_5.to_bytes('ßßßßß') == (5, b'\xdf' * 5)
    assert non_ascii_string_with_len_5.from_bytes(b'\xdf' * 5) == (5, 'ßßßßß')