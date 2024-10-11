import enum

from .. import types
from ...common import TypeDefinition


__all__ = [
    'SupportedTypes',
    'Version',
    'get_supported_types'
]
SupportedTypes = dict[str, TypeDefinition]


class Version(enum.IntEnum):
    FIX_4_2 = 42
    FIX_4_4 = 44
    FIX_5_0 = 50
    FIX_5_0_2 = 502


def get_supported_types(version: Version) -> SupportedTypes:
    version_map = {
        Version.FIX_4_2: fix_42_version_types,
        Version.FIX_4_4: fix_44_version_types,
        Version.FIX_5_0: fix_50_version_types,
        Version.FIX_5_0_2: fix_502_version_types
    }
    try:
        return version_map[version]()
    except KeyError as k_error:
        raise ValueError(f'Version {version} not supported') from k_error


def fix_42_version_types():
    return {
        'AMT': types.FixAmount,
        'BOOLEAN': types.FixBool,
        'CHAR': types.FixChar,
        'CURRENCY': types.FixCurrency,
        'DATA': types.FixString,
        'DAYOFMONTH': types.FixDayOfMonth,
        'EXCHANGE': types.FixExchange,
        'FLOAT': types.FixFloat,
        'INT': types.FixInt,
        'LENGTH': types.FixInt,
        'LOCALMKTDATE': types.FixString,
        'MONTHYEAR': types.FixInt,
        'MULTIPLEVALUESTRING': types.FixMultipleValueString,
        'PRICE': types.FixPrice,
        'PRICEOFFSET': types.FixPriceOffset,
        'QTY': types.FixQuantity,
        'STRING': types.FixString,
        'UTCDATE': types.FixString,
        'UTCTIMEONLY': types.FixUTCTimeOnly,
        'UTCTIMESTAMP': types.FixUTCTimeStamp,
        # tmp
        'COUNTRY': types.FixString,
        'PERCENTAGE': types.FixFloat,
        'LONG': types.FixInt,
    }


def fix_44_version_types():
    fix_44_types = fix_42_version_types()
    fix_44_types.update({
        'SEQNUM': types.FixInt,
        'NUMINGROUP': types.FixInt,
    })
    return fix_44_types


def fix_50_version_types():
    fix_50_types = fix_42_version_types()
    fix_50_types.update({
        'FIXSTRING': types.FixString,
        'MULTIPLECHARVALUE': types.FixString,
        'NUMINGROUP': types.FixInt,
        'SEQNUM': types.FixInt
    })
    return fix_50_types


def fix_502_version_types():
    fix_52_types = fix_50_version_types()
    fix_52_types.update({
        'LOCALMKTDATE': types.FixLocalMktDate,
        'TZTIMEONLY': types.FixTzTimeonly,
        'MULTIPLESTRINGVALUE': types.FixMultipleValueString,
    })
    return fix_52_types
