from enum import Enum

import pytest
from nasdaq_protocols.common import *


TEST_RECORD_FIELDS = [
    structures.Field('byte_field', types.Byte),
    structures.Field('short_field', types.Short),
    structures.Field('string_field', types.AsciiString),
]


class TestRecord(Record):
    __test__ = False
    Fields = TEST_RECORD_FIELDS

    byte_field: int
    short_field: int
    string_field: str


class TestRecordWithPresentBit(RecordWithPresentBit):
    __test__ = False
    Fields = TEST_RECORD_FIELDS

    byte_field: int
    short_field: int
    string_field: str


class TestRecordInRecord(structures.RecordWithPresentBit):
    __test__ = False
    Fields = [
        structures.Field('record', TestRecordWithPresentBit)
    ]

    record: TestRecordWithPresentBit


class TestArrayOfRecords(structures.RecordWithPresentBit):
    __test__ = False
    Fields = [
        structures.Field('records', Array(TestRecordWithPresentBit))
    ]

    records: list[TestRecordWithPresentBit]


def test__record__to_bytes():
    expected_bytes = b'\x02\x05\x00\x04\x00test'
    record = TestRecord()
    record.byte_field = 2
    record.short_field = 5
    record.string_field = 'test'

    assert record.byte_field == 2
    assert record.short_field == 5
    assert record.string_field == 'test'

    len_, bytes_ = TestRecord.to_bytes(record)
    assert len_ == len(expected_bytes)
    assert bytes_ == expected_bytes


def test__record__from_bytes():
    record = TestRecord.from_bytes(b'\x02\x05\x00\x04\x00test')[1]

    assert record.byte_field == 2
    assert record.short_field == 5
    assert record.string_field == 'test'


def test__record_with_present_bit__to_bytes():
    expected_bytes = b'\x01\x02\x05\x00\x04\x00test'
    record = TestRecordWithPresentBit()
    record.byte_field = 2
    record.short_field = 5
    record.string_field = 'test'

    assert record.byte_field == 2
    assert record.short_field == 5
    assert record.string_field == 'test'

    len_, bytes_ = TestRecordWithPresentBit.to_bytes(record)
    assert len_ == len(expected_bytes)
    assert bytes_ == expected_bytes


def test__record_with_present_bit__from_bytes():
    record = TestRecordWithPresentBit.from_bytes(b'\x01\x02\x05\x00\x04\x00test')[1]

    assert record.byte_field == 2
    assert record.short_field == 5
    assert record.string_field == 'test'


def test__record___record_in_record__to_bytes():
    expected_bytes = b'\x01\x01\x02\x05\x00\x04\x00test'
    record = TestRecordInRecord()
    record.record = TestRecordWithPresentBit()
    record.record.byte_field = 2
    record.record.short_field = 5
    record.record.string_field = 'test'

    assert record.record.byte_field == 2
    assert record.record.short_field == 5
    assert record.record.string_field == 'test'

    len_, bytes_ = TestRecordInRecord.to_bytes(record)
    assert len_ == len(expected_bytes)
    assert bytes_ == expected_bytes


def test__record__record_in_record__from_bytes():
    record = TestRecordInRecord.from_bytes(b'\x01\x01\x02\x05\x00\x04\x00test')[1]

    assert record.record.byte_field == 2
    assert record.record.short_field == 5
    assert record.record.string_field == 'test'


def test__record__array_of_records__to_bytes():
    expected_bytes = b'\x01\x02\x00' + (b'\x02\x05\x00\x04\x00test' * 2)
    record = TestArrayOfRecords()
    record.records = [
        TestRecordWithPresentBit(),
        TestRecordWithPresentBit(),
    ]
    record.records[0].byte_field = 2
    record.records[0].short_field = 5
    record.records[0].string_field = 'test'
    record.records[1].byte_field = 2
    record.records[1].short_field = 5
    record.records[1].string_field = 'test'

    assert record.records[0].byte_field == 2
    assert record.records[0].short_field == 5
    assert record.records[0].string_field == 'test'
    assert record.records[1].byte_field == 2
    assert record.records[1].short_field == 5
    assert record.records[1].string_field == 'test'

    len_, bytes_ = TestArrayOfRecords.to_bytes(record)
    assert len_ == len(expected_bytes)
    assert bytes_ == expected_bytes


def test__record__array_of_records__from_bytes():
    record = TestArrayOfRecords.from_bytes(b'\x01\x02\x00' + (b'\x02\x05\x00\x04\x00test' * 2))[1]

    assert record.records[0].byte_field == 2
    assert record.records[0].short_field == 5
    assert record.records[0].string_field == 'test'
    assert record.records[1].byte_field == 2
    assert record.records[1].short_field == 5
    assert record.records[1].string_field == 'test'


def test__record__equal():
    record1 = TestRecord()
    record1.byte_field = 2
    record1.short_field = 5
    record1.string_field = 'test'

    record2 = TestRecord()
    record2.byte_field = 2
    record2.short_field = 5
    record2.string_field = 'test'

    assert record1 == record2
    assert record1 != 1
    assert record1 != 'test'
    assert record1 != TestRecordWithPresentBit()


def test__record__not_equal():
    record1 = TestRecord()
    record1.byte_field = 2
    record1.short_field = 5
    record1.string_field = 'test'

    record2 = TestRecord()
    record2.byte_field = 2
    record2.short_field = 5
    record2.string_field = 'test2'

    assert record1 != record2


def test__record__to_str():
    record = TestRecord()
    record.byte_field = 2
    record.short_field = 5
    record.string_field = 'test'

    assert (TestRecord.to_str(record) ==
            str(record) ==
            "{'TestRecord':{{'byte_field': 2, 'short_field': 5, 'string_field': 'test'}}}")


def test__record__is_record():
    assert Record.is_record(TestRecord)


def test__record__create_with_all_values():
    values = {
        'byte_field': 2,
        'short_field': 5,
        'string_field': 'test'
    }
    record = TestRecord(values)

    assert record.byte_field == 2
    assert record.short_field == 5
    assert record.string_field == 'test'


def test__record__nested_record__default_values_initialised():
    values = {
    }
    record = TestRecordInRecord(values)

    assert record.record.byte_field == 0
    assert record.record.short_field == 0
    assert record.record.string_field == ''


def test__record__from_str__not_implemented():
    with pytest.raises(NotImplementedError):
        TestRecord.from_str('test')


def test__record__enum_type_field():
    class TestEnum(Enum):
        A = 1
        B = 2

    record = TestRecord()
    record.byte_field = TestEnum.A
    record.short_field = TestEnum.B
    record.string_field = 'test'

    assert record.byte_field == 1
    assert record.short_field == 2


def test__record__invalid_type__exception_is_raised():
    record = TestRecord()
    record.byte_field = 2
    record.short_field = 5
    record.string_field = 'test'

    with pytest.raises(ValueError):
        record.string_field = 3

    with pytest.raises(ValueError):
        record_in_record = TestRecordInRecord()
        record_in_record.record = record


def test__record_with_present_bit__get_value():
    record = TestRecordWithPresentBit()
    record.byte_field = 2
    record.short_field = 5
    record.string_field = 'test'

    record_in_record = TestRecordInRecord()
    record_in_record.record = record

    array_of_records = TestArrayOfRecords()
    array_of_records.records = [record, record]

    assert Record.get_value(record_in_record) == {
        'TestRecordInRecord': {
            'record': {
                'TestRecordWithPresentBit': {
                    'byte_field': 2,
                    'short_field': 5,
                    'string_field': 'test'
                }
            }
        }
    }

    assert Record.get_value(array_of_records) == {
        'TestArrayOfRecords': {
            'records': [
                {
                    'TestRecordWithPresentBit': {
                        'byte_field': 2,
                        'short_field': 5,
                        'string_field': 'test'
                    }
                },
                {
                    'TestRecordWithPresentBit': {
                        'byte_field': 2,
                        'short_field': 5,
                        'string_field': 'test'
                    }
                }
            ]
        }
    }


def test__array__from_str__not_implemented():
    with pytest.raises(NotImplementedError):
        Array.from_str('test')


def test__array__to_str__not_implemented():
    with pytest.raises(NotImplementedError):
        Array.to_str('test')


def test__array__basic_types__to_bytes():
    array_of_chars = Array(types.CharAscii)
    input_ = 'abcde'
    expected_op = (7, b'\x05\x00abcde')

    assert array_of_chars.to_bytes(input_) == expected_op


def test__array__basic_types__from_bytes():
    array_of_chars = Array(types.CharAscii)
    input_ = b'\x05\x00abcde'
    expected_op = (7, ['a', 'b', 'c', 'd', 'e'])

    assert array_of_chars.from_bytes(input_) == expected_op


def test__record_with_present_bit__empty_record__to_bytes():
    assert TestRecordWithPresentBit.to_bytes(None) == (1, b'\x00')
    assert TestRecordWithPresentBit.to_bytes(TestRecordWithPresentBit()) == (1, b'\x00')


def test__record_with_present_bit__empty_record2__from_bytes():
    assert TestRecordWithPresentBit.from_bytes(b'\x00') == (1, None)