from functools import partial
from typing import Callable, Tuple
from nasdaq_protocols.common.types import TypeDefinition


__all__ = [
    'Boolean',
    'Int',
    'IntBE',
    'UnsignedInt',
    'UnsignedIntBE',
    'Byte',
    'Short',
    'ShortBE',
    'UnsignedShort',
    'UnsignedShortBE',
    'Long',
    'LongBE',
    'UnsignedLong',
    'UnsignedLongBE',
    'CharAscii',
    'CharIso8599',
    'AsciiString',
    'Iso8859String',
    'FixedAsciiString',
    'FixedIsoString'
]
_StringPackable = Callable[[str], Tuple[int, bytes]]
_StringUnPackable = Callable[[bytes], Tuple[int, str]]
_IntPackable = Callable[[int], Tuple[int, bytes]]
_IntUnPackable = Callable[[bytes], Tuple[int, int]]
_BoolPackable = Callable[[bool], Tuple[int, bytes]]
_BoolUnPackable = Callable[[bytes], Tuple[int, bool]]
_ASCII = 'ascii'
_ISO_STR = 'iso-8859-1'
_BIG = 'big'
_LITTLE = 'little'


def _int_packer_fac(endian: str, signed: bool, size: int, value: int) -> Tuple[int, bytes]:
    return size, value.to_bytes(size, endian, signed=signed)


def _int_unpacker_fac(endian: str, signed: bool, size: int, value: bytes) -> Tuple[int, int]:
    return size, int.from_bytes(value[:size], endian, signed=signed)


def _str_unpack_fac(encoding: str, data: bytes) -> Tuple[int, str]:
    offset, len_ = Short.from_bytes(data)
    return offset+len_, data[offset:offset+len_].decode(encoding)


def _str_pack_fac(encoding: str, str_: str) -> Tuple[int, bytes]:
    len_size, len_bytes = Short.to_bytes(len(str_))
    return len_size+len(str_), len_bytes + str_.encode(encoding)


class TypeSize:
    BOOLEAN = 1
    BYTE = 1
    CHAR = 1
    SHORT = 2
    INT = 4
    LONG = 8


@TypeDefinition.add_type('boolean')
class Boolean(TypeDefinition):
    to_str: Callable[[bool], str] = lambda x: 'True' if x else 'False'
    from_str: Callable[[str], bool] = lambda x: x in ('True', '1')
    to_bytes: _BoolPackable = lambda x: (TypeSize.BOOLEAN, b'\x01' if x else b'\x00')
    from_bytes: _BoolUnPackable = lambda x: (TypeSize.BOOLEAN, x[0:1] == b'\x01')
    hint = 'bool'
    type_cls = bool
    default_value = False


@TypeDefinition.add_type('int_4')
class Int(TypeDefinition):
    to_str: Callable[[int], str] = str
    from_str: Callable[[str], int] = int
    to_bytes: _IntPackable = partial(_int_packer_fac, _LITTLE, True, TypeSize.INT)
    from_bytes: _IntUnPackable = partial(_int_unpacker_fac, _LITTLE, True, TypeSize.INT)
    hint = 'int'
    type_cls = int
    default_value = 0


@TypeDefinition.add_type('int_4_be')
class IntBE(Int):
    to_bytes: _IntPackable = partial(_int_packer_fac, _BIG, True, TypeSize.INT)
    from_bytes: _IntUnPackable = partial(_int_unpacker_fac, _BIG, True, TypeSize.INT)


@TypeDefinition.add_type('uint_4')
class UnsignedInt(Int):
    to_bytes: _IntPackable = partial(_int_packer_fac, _LITTLE, False, TypeSize.INT)
    from_bytes: _IntUnPackable = partial(_int_unpacker_fac, _LITTLE, False, TypeSize.INT)


@TypeDefinition.add_type('uint_4_be')
class UnsignedIntBE(UnsignedInt):
    to_bytes: _IntPackable = partial(_int_packer_fac, _BIG, False, TypeSize.INT)
    from_bytes: _IntUnPackable = partial(_int_unpacker_fac, _BIG, False, TypeSize.INT)


@TypeDefinition.add_type('byte')
class Byte(Int):
    to_bytes: _IntPackable = partial(_int_packer_fac, _LITTLE, False, TypeSize.BYTE)
    from_bytes: _IntUnPackable = partial(_int_unpacker_fac, _LITTLE, False, TypeSize.BYTE)


@TypeDefinition.add_type('int_2')
class Short(Int):
    to_bytes: _IntPackable = partial(_int_packer_fac, _LITTLE, True, TypeSize.SHORT)
    from_bytes: _IntUnPackable = partial(_int_unpacker_fac, _LITTLE, True, TypeSize.SHORT)


@TypeDefinition.add_type('int_2_be')
class ShortBE(Int):
    to_bytes: _IntPackable = partial(_int_packer_fac, _BIG, True, TypeSize.SHORT)
    from_bytes: _IntUnPackable = partial(_int_unpacker_fac, _BIG, True, TypeSize.SHORT)


@TypeDefinition.add_type('uint_2')
class UnsignedShort(Int):
    to_bytes: _IntPackable = partial(_int_packer_fac, _LITTLE, False, TypeSize.SHORT)
    from_bytes: _IntUnPackable = partial(_int_unpacker_fac, _LITTLE, False, TypeSize.SHORT)


@TypeDefinition.add_type('uint_2_be')
class UnsignedShortBE(Int):
    to_bytes: _IntPackable = partial(_int_packer_fac, _BIG, False, TypeSize.SHORT)
    from_bytes: _IntUnPackable = partial(_int_unpacker_fac, _BIG, False, TypeSize.SHORT)


@TypeDefinition.add_type('int_8')
class Long(Int):
    to_bytes: _IntPackable = partial(_int_packer_fac, _LITTLE, True, TypeSize.LONG)
    from_bytes: _IntUnPackable = partial(_int_unpacker_fac, _LITTLE, True, TypeSize.LONG)


@TypeDefinition.add_type('int_8_be')
class LongBE(Int):
    to_bytes: _IntPackable = partial(_int_packer_fac, _BIG, True, TypeSize.LONG)
    from_bytes: _IntUnPackable = partial(_int_unpacker_fac, _BIG, True, TypeSize.LONG)


@TypeDefinition.add_type('uint_8')
class UnsignedLong(Int):
    to_bytes: _IntPackable = partial(_int_packer_fac, _LITTLE, False, TypeSize.LONG)
    from_bytes: _IntUnPackable = partial(_int_unpacker_fac, _LITTLE, False, TypeSize.LONG)


@TypeDefinition.add_type('uint_8_be')
class UnsignedLongBE(Int):
    to_bytes: _IntPackable = partial(_int_packer_fac, _BIG, False, TypeSize.LONG)
    from_bytes: _IntUnPackable = partial(_int_unpacker_fac, _BIG, False, TypeSize.LONG)


@TypeDefinition.add_type('char_ascii')
class CharAscii(TypeDefinition):
    to_str: Callable[[str], str] = str
    from_str: Callable[[str], str] = str
    to_bytes: _StringPackable = lambda x: (TypeSize.CHAR, x[:TypeSize.CHAR].encode(_ASCII))
    from_bytes: _StringUnPackable = lambda x: (TypeSize.CHAR, x[:TypeSize.CHAR].decode(_ASCII))
    hint = 'str'
    type_cls = str
    default_value = ' '


@TypeDefinition.add_type('char_iso-8859-1')
class CharIso8599(CharAscii):
    to_bytes: _StringPackable = lambda x: (TypeSize.CHAR, x[:TypeSize.CHAR].encode('iso-8859-1'))
    from_bytes: _StringUnPackable = lambda x: (TypeSize.CHAR, x[:TypeSize.CHAR].decode('iso-8859-1'))


@TypeDefinition.add_type('str_ascii')
class AsciiString(CharAscii):
    """
    :param to_bytes: encodes the string to bytes and prepends the 2 digit size of the string
    :type to_bytes: Callable[[str], Tuple[int, bytes]]

    :param from_bytes: decodes the bytes to string and returns the size of the string and the string
    :type from_bytes: Callable[[bytes], Tuple[int, str]]
    """
    to_bytes: _StringPackable = partial(_str_pack_fac, _ASCII)
    from_bytes: _StringUnPackable = partial(_str_unpack_fac, _ASCII)
    default_value = ''


@TypeDefinition.add_type('str_iso-8859-1')
class Iso8859String(CharAscii):
    to_bytes: _StringPackable = partial(_str_pack_fac, 'iso-8859-1')
    from_bytes: _StringUnPackable = partial(_str_unpack_fac, 'iso-8859-1')
    default_value = ''


@TypeDefinition.add_type('str_ascii_n')
class FixedAsciiString(TypeDefinition):
    to_str: Callable[[str], str] = str
    from_str: Callable[[str], str] = str
    hint = 'str'
    type_cls = str
    default_value = ''

    def __init__(self, length, right_justified=False):
        self.length = length
        self.right_justified = right_justified

    def to_bytes(self, value: str) -> Tuple[int, bytes]:
        value = value.rjust(self.length) if self.right_justified else value.ljust(self.length)
        return self.length, value.encode(_ASCII)

    def from_bytes(self, data: bytes) -> Tuple[int, str]:
        return self.length, data[:self.length].decode(_ASCII).strip()


@TypeDefinition.add_type('str_iso-8859-1_n')
class FixedIsoString(TypeDefinition):
    to_str: Callable[[str], str] = str
    from_str: Callable[[str], str] = str
    hint = 'str'
    type_cls = str
    default_value = ''

    def __init__(self, length, right_justified=False):
        self.length = length
        self.right_justified = right_justified

    def to_bytes(self, value: str) -> Tuple[int, bytes]:
        value = value.rjust(self.length) if self.right_justified else value.ljust(self.length)
        return self.length, value.encode(_ISO_STR)

    def from_bytes(self, data: bytes) -> Tuple[int, str]:
        return self.length, data[:self.length].decode(_ISO_STR).strip()
