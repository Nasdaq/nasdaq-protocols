from typing import Callable

from nasdaq_protocols.common import TypeDefinition


__all__ = [
    'FixString',
    'FixBool',
    'FixInt',
    'FixFloat',
    'FixChar',
    'FixQuantity',
    'FixPrice',
    'FixPriceOffset',
    'FixAmount',
    'FixMultipleValueString',
    'FixCurrency',
    'FixExchange',
    'FixUTCTimeStamp',
    'FixUTCTime',
    'FixLocalMktDate',
    'FixTzTime',
    'FixTzTimestamp',
    'FixDayOfMonth',
    'FixUTCTimeOnly',
    'FixTzTimeonly'
]


def _pack_str(str_: str) -> tuple[int, bytes]:
    return len(str_), str_.encode('ascii')


def _unpack_str(data: bytes) -> tuple[int, str]:
    return len(data), data.decode('ascii')


def _pack_int(val: int) -> tuple[int, bytes]:
    return _pack_str(str(val))


def _unpack_int(val: bytes) -> tuple[int, int]:
    len_, str_ = _unpack_str(val)
    return len_, int(str_)


def _pack_float(val: int | float) -> tuple[int, bytes]:
    return _pack_str(str(val))


def _unpack_float(val: bytes) -> tuple[int, float]:
    len_, str_ = _unpack_str(val)
    return len_, float(str_)


@TypeDefinition.add_type('fix_string')
class FixString(TypeDefinition):
    to_str: Callable[[str], str] = str
    from_str: Callable[[str], str] = str
    to_bytes: Callable[[str], tuple[int, bytes]] = _pack_str
    from_bytes: Callable[[bytes], tuple[int, str]] = _unpack_str
    hint = 'str'
    type_cls = str
    default_value = ''


@TypeDefinition.add_type('fix_bool')
class FixBool(TypeDefinition):
    to_str: Callable[[bool], str] = lambda x: 'Y' if x else 'N'
    from_str: Callable[[str], bool] = lambda x: x in ('Y', 'y')
    to_bytes: Callable[[bool], tuple[int, bytes]] = lambda x: (1, b'Y') if x else (1, b'N')
    from_bytes: Callable[[bytes], tuple[int, bool]] = lambda x: (len(x), x == b'Y')
    hint = 'bool'
    type_cls = bool
    default_value = False


@TypeDefinition.add_type('fix_bool')
class FixInt(TypeDefinition):
    to_str: Callable[[int], str] = str
    from_str: Callable[[str], int] = int
    to_bytes: Callable[[int], tuple[int, bytes]] = _pack_int
    from_bytes: Callable[[bytes], tuple[int, int]] = _unpack_int
    hint = 'int'
    type_cls = int
    default_value = 0


@TypeDefinition.add_type('fix_float')
class FixFloat(TypeDefinition):
    to_str: Callable[[float], str] = str
    from_str: Callable[[str], float] = float
    to_bytes: Callable[[float | int], tuple[int, bytes]] = _pack_float
    from_bytes: Callable[[bytes], tuple[int, float]] = _unpack_float
    hint = 'float'
    type_cls = float
    default_value = 0


@TypeDefinition.add_type('fix_char')
class FixChar(FixString):
    ...


@TypeDefinition.add_type('fix_quantity')
class FixQuantity(FixFloat):
    ...


@TypeDefinition.add_type('fix_price')
class FixPrice(FixFloat):
    ...


@TypeDefinition.add_type('fix_price_offset')
class FixPriceOffset(FixFloat):
    ...


@TypeDefinition.add_type('fix_amount')
class FixAmount(FixFloat):
    ...


@TypeDefinition.add_type('fix_multiple_value_string')
class FixMultipleValueString(FixString):
    ...


@TypeDefinition.add_type('fix_currency')
class FixCurrency(FixString):
    ...


@TypeDefinition.add_type('fix_exchange')
class FixExchange(FixString):
    ...


@TypeDefinition.add_type('fix_utc_timestamp')
class FixUTCTimeStamp(FixString):
    ...


@TypeDefinition.add_type('fix_utc_time')
class FixUTCTime(FixString):
    ...


@TypeDefinition.add_type('fix_local_mkt_date')
class FixLocalMktDate(FixString):
    ...


@TypeDefinition.add_type('fix_tx_time')
class FixTzTime(FixString):
    ...


@TypeDefinition.add_type('fix_tz_timestamp')
class FixTzTimestamp(FixString):
    ...


@TypeDefinition.add_type('fix_day_of_month')
class FixDayOfMonth(FixInt):
    ...


class FixUTCTimeOnly(FixString):
    pass


class FixTzTimeonly(FixString):
    pass
